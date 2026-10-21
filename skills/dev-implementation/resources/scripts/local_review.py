#!/usr/bin/env python3
"""Local model review through Ollama: transport, review slices, and the prompt base.

The model behind Ollama has no tools, so every pass is self-contained. This module never imports
run_external_review.py; the runner imports it.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_NUM_CTX = 32768


class LocalReviewError(Exception):
    """A probe, budget or transport failure; str(error) is the reason shown to the developer."""


@dataclass(frozen=True)
class Reply:
    content: str  # answer_text of message.content; "" on failure
    done_reason: str | None
    error: str | None  # None on HTTP 200


def host_from_env() -> str:
    host = os.environ.get("OLLAMA_HOST") or DEFAULT_HOST
    return (host if "://" in host else f"http://{host}").rstrip("/")


def post(url: str, payload: dict[str, Any], timeout: int) -> Any:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def probe(host: str, model: str, timeout: int = 10) -> int | None:
    """Check the server and the model; return the Modelfile's num_ctx, or None when it sets none."""
    try:
        urllib.request.urlopen(f"{host}/api/version", timeout=timeout).close()
    except OSError as error:  # URLError is an OSError
        raise LocalReviewError(f"Ollama server not reachable at {host}") from error
    try:
        shown = post(f"{host}/api/show", {"model": model}, timeout)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise LocalReviewError(f"model {model} is not installed (ollama list)") from error
        raise LocalReviewError(f"HTTP {error.code} from {host}/api/show") from error
    except OSError as error:
        raise LocalReviewError(f"Ollama server not reachable at {host}") from error
    for line in str(shown.get("parameters") or "").splitlines():
        name, _, value = line.strip().partition(" ")
        if name == "num_ctx":
            return int(value.strip())
    return None


def chat_options(model_ctx: int | None, flag_ctx: int | None, prompt_tokens: int) -> dict[str, int]:
    """Leave sampling to the Modelfile; send num_ctx only when it is not the Modelfile's own."""
    effective = flag_ctx or model_ctx or DEFAULT_NUM_CTX
    options = {"num_predict": effective - prompt_tokens}
    if flag_ctx is not None or model_ctx is None:
        options["num_ctx"] = effective
    return options


def answer_text(content: str) -> str:
    """The answer after any inline thinking: the text after the last </think>, stripped."""
    return content.rpartition("</think>")[2].strip()


def chat(host: str, model: str, system: str, user: str, options: dict[str, int], timeout: int) -> Reply:
    """One non-streaming /api/chat call; failures become a Reply with its error set, never an exception."""
    payload = {"model": model,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "stream": False, "options": options}
    try:
        data = post(f"{host}/api/chat", payload, timeout)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        return Reply("", None, f"HTTP {error.code}: {body[:500]}")
    except TimeoutError:
        return Reply("", None, f"timed out after {timeout} seconds")
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            return Reply("", None, f"timed out after {timeout} seconds")
        return Reply("", None, str(error))
    except (OSError, ValueError) as error:
        return Reply("", None, str(error))
    message = data.get("message") or {}
    return Reply(answer_text(str(message.get("content") or "")), data.get("done_reason"), None)
