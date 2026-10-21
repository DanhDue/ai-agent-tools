#!/usr/bin/env python3
"""Tests for local model review: shared rules, the Ollama transport, slices, the prompt base and rounds.

Every Ollama call goes to a fake server on 127.0.0.1 inside the test; no test reaches a real model.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py
"""
import json
import os
import socket
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import local_review
from test_run_external_review import ReviewCase


class FakeOllama:
    """An in-process Ollama stand-in on 127.0.0.1: tests set its replies, it keeps every request."""

    def __init__(self) -> None:
        self.show: tuple[int, dict[str, Any]] = (200, {"parameters": "temperature 0.2"})
        self.chat_replies: list[tuple[int, str, str]] = []  # (status, content or error body, done_reason)
        self.delay = 0.0
        self.requests: list[tuple[str, dict[str, Any], float, float]] = []  # (path, body, started, finished)
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                self.reply(200, {"version": "0.0.0-fake"})

            def do_POST(self) -> None:
                started = time.monotonic()
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
                if self.path == "/api/show":
                    self.reply(*fake.show)
                else:
                    time.sleep(fake.delay)
                    status, text, reason = fake.chat_replies.pop(0) if fake.chat_replies else (200, "Verdict: PASS", "stop")
                    if status == 200:
                        self.reply(200, {"message": {"role": "assistant", "content": text},
                                         "done": True, "done_reason": reason})
                    else:
                        self.reply(status, text)
                fake.requests.append((self.path, body, started, time.monotonic()))

            def reply(self, status: int, payload: Any) -> None:
                data = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
                try:
                    self.send_response(status)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except OSError:
                    pass  # the client gave up first, as in a timeout test

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.server.block_on_close = False
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def chats(self) -> list[dict[str, Any]]:
        return [body for path, body, _, _ in self.requests if path == "/api/chat"]

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def closed_port() -> int:
    with socket.socket() as probe_socket:
        probe_socket.bind(("127.0.0.1", 0))
        port: int = probe_socket.getsockname()[1]
    return port


class TransportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = FakeOllama()
        self.addCleanup(self.fake.close)

    def test_lmr_hp_06_modelfile_governs_the_context(self) -> None:
        self.fake.show = (200, {"parameters": 'num_ctx                        65536\nstop                           "<|im_end|>"'})
        self.assertEqual(local_review.probe(self.fake.url, "qwen38-reviewer"), 65536)
        self.assertEqual(self.fake.requests[-1][1], {"model": "qwen38-reviewer"})
        self.assertEqual(local_review.chat_options(65536, None, 30000), {"num_predict": 35536})

    def test_lmr_ec_02_context_defaults_and_overrides(self) -> None:
        self.assertIsNone(local_review.probe(self.fake.url, "m"))
        self.assertEqual(local_review.chat_options(None, None, 1000), {"num_ctx": 32768, "num_predict": 31768})
        self.assertEqual(local_review.chat_options(65536, 16384, 1000), {"num_ctx": 16384, "num_predict": 15384})

    def test_lmr_ec_07_inline_thinking_is_never_parsed(self) -> None:
        content = "draft [Critical] a.py:1 — x\nVerdict: CHANGES REQUIRED\n</think>\n## Analysis\nfine\nVerdict: PASS"
        self.assertEqual(local_review.answer_text(content), "## Analysis\nfine\nVerdict: PASS")
        self.fake.chat_replies = [(200, content, "stop")]
        reply = local_review.chat(self.fake.url, "m", "s", "u", {"num_predict": 10}, 5)
        self.assertEqual(reply, local_review.Reply("## Analysis\nfine\nVerdict: PASS", "stop", None))
        self.assertEqual(local_review.answer_text("  Verdict: PASS \n"), "Verdict: PASS")

    def test_lmr_fr_01_probe_failures_name_their_cause(self) -> None:
        port = closed_port()
        with self.assertRaises(local_review.LocalReviewError) as caught:
            local_review.probe(f"http://127.0.0.1:{port}", "m")
        self.assertEqual(str(caught.exception), f"Ollama server not reachable at http://127.0.0.1:{port}")
        self.fake.show = (404, {"error": "model 'ghost' not found"})
        with self.assertRaises(local_review.LocalReviewError) as caught:
            local_review.probe(self.fake.url, "ghost")
        self.assertEqual(str(caught.exception), "model ghost is not installed (ollama list)")

    def test_lmr_fr_03_transport_failures_become_replies(self) -> None:
        self.fake.chat_replies = [(500, "boom", "")]
        self.assertEqual(local_review.chat(self.fake.url, "m", "s", "u", {"num_predict": 10}, 5),
                         local_review.Reply("", None, "HTTP 500: boom"))
        self.fake.delay = 3
        self.assertEqual(local_review.chat(self.fake.url, "m", "s", "u", {"num_predict": 10}, 1),
                         local_review.Reply("", None, "timed out after 1 seconds"))

    def test_chat_sends_the_messages_and_options_without_think(self) -> None:
        local_review.chat(self.fake.url, "qwen38-reviewer", "SYSTEM", "USER", {"num_predict": 7}, 5)
        self.assertEqual(self.fake.chats(), [{
            "model": "qwen38-reviewer",
            "messages": [{"role": "system", "content": "SYSTEM"}, {"role": "user", "content": "USER"}],
            "stream": False,
            "options": {"num_predict": 7},
        }])

    def test_host_comes_from_ollama_host_or_the_default(self) -> None:
        with mock.patch.dict(os.environ, clear=True):
            self.assertEqual(local_review.host_from_env(), "http://localhost:11434")
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "127.0.0.1:11500"}):
            self.assertEqual(local_review.host_from_env(), "http://127.0.0.1:11500")
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "http://box:11434/"}):
            self.assertEqual(local_review.host_from_env(), "http://box:11434")


class SharedRulesTest(ReviewCase):
    def test_lmr_hp_02_shared_rules_reach_the_external_prompt(self) -> None:
        self.install("claude")
        code, _, _ = self.run_review(cli="claude")
        self.assertEqual(code, 0)
        prompt = self.stdin.read_text(encoding="utf-8")
        for title in ("Task-Level vs. Gate 4 Workspace Scope", "No Reconstructed Logic",
                      "Immutable Real Artifacts"):
            self.assertIn(title, prompt)
        self.assertNotIn("$rules", prompt)


if __name__ == "__main__":
    unittest.main()
