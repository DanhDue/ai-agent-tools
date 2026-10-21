#!/usr/bin/env python3
"""Tests for local model review: shared rules, the Ollama transport, slices, the prompt base and rounds.

Every Ollama call goes to a fake server on 127.0.0.1 inside the test; no test reaches a real model.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py
"""
import json
import os
import re
import socket
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import local_review
from run_external_review import EXCLUDES
from task_contract import section
from test_run_external_review import ReviewCase, git

EPIC = ".devtool/epic/demo"
TICKS = "`" * 3
TWO_SCENARIOS = (f"# Scenarios\n\n{TICKS}gherkin\n"
                 "Scenario: [DEMO-HP-01] [Tier C - Integration] First\n  Given one\n  Then first-marker\n\n"
                 "Scenario: [DEMO-HP-02] [Tier C - Integration] Second\n  Given two\n  Then second-marker\n"
                 f"{TICKS}\n")
TASK_FILE = "# Task 1: Demo\n\n### BDD SCENARIOS\n\nCovers: DEMO-HP-01\n"
TAIL = [f"tail-{number:02d}" for number in range(1, 41)]


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


class EpicRepoCase(unittest.TestCase):
    """A throwaway epic repository: a base commit, the epic documents, then task and other commits."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve() / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "demo@example.com")
        git(self.root, "config", "user.name", "Demo")
        self.write("README.md", "demo\n")
        self.commit("Start")
        self.base = git(self.root, "rev-parse", "HEAD")
        self.write(f"{EPIC}/demo.en.md", "# Demo HLD\n\nhld-marker\n")
        self.write(f"{EPIC}/2026-01-01-demo-design.en.md", "# Demo Spec\n\nspec-marker\n")
        self.write(f"{EPIC}/bdd_scenarios.en.md", TWO_SCENARIOS)
        self.write(f"{EPIC}/task_1_demo.md", TASK_FILE)
        self.commit("Epic")

    def write(self, name: str, text: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)

    def task_commit(self, files: dict[str, str], task: str = "task_1_demo") -> None:
        for name, text in files.items():
            self.write(name, text)
        row = {"id": "V2", "phase": "GREEN", "command": "python3 -m unittest demo", "expect": "exit 0",
               "exit": 0, "outcome": "PASS", "output_tail": TAIL}
        red = dict(row, id="V1", phase="RED", expect="exit 1", exit=1, output_tail=["red-only"])
        evidence = {"schema": 1, "task": task, "runs": {"red": {"rows": [red]}, "verify": {"rows": [row]}}}
        self.write(f"{EPIC}/evidence/{task}.json", json.dumps(evidence))
        self.commit(f"Task {task}")

    def slices(self) -> list[local_review.Slice]:
        sha = git(self.root, "rev-parse", "HEAD")
        return local_review.build_slices(self.root, "demo", self.base, sha, "audit-output", "results-output",
                                         EXCLUDES)


def section_of(text: str, heading: str) -> str:
    """The body under one `## ` heading of a rendered user message."""
    return text.split(f"{heading}\n", 1)[1].split("\n## ", 1)[0]


class SliceTest(EpicRepoCase):
    def test_lmr_hp_04_a_task_slice_carries_everything_the_reviewer_may_judge(self) -> None:
        self.task_commit({"src/a.py": "print('a')\n"})
        task, epic = self.slices()
        self.assertEqual((task.label, task.kind, task.paths, task.omitted), ("task_1_demo", "task", ("src/a.py",), ()))
        self.assertEqual((epic.label, epic.kind), ("epic", "epic"))
        user = local_review.render_user(task)
        short = git(self.root, "rev-parse", "--short", "HEAD")
        headings = ["## Task file", "## Scenarios covered", "## Evidence", f"## Diff of {short}", "## Not shown"]
        self.assertEqual([user.index(f"{heading}\n") for heading in headings],
                         sorted(user.index(f"{heading}\n") for heading in headings))
        self.assertIn("Covers: DEMO-HP-01", section_of(user, "## Task file"))
        scenarios = section_of(user, "## Scenarios covered")
        self.assertIn("[DEMO-HP-01]", scenarios)
        self.assertIn("first-marker", scenarios)
        self.assertNotIn("DEMO-HP-02", scenarios)
        evidence = section_of(user, "## Evidence")
        self.assertEqual([line for line in TAIL if line in evidence], TAIL[25:])
        self.assertIn("red-only", evidence)
        self.assertIn("python3 -m unittest demo", evidence)
        diff = section_of(user, f"## Diff of {short}")
        self.assertIn("+print('a')", diff)
        self.assertNotIn(".devtool/", diff)
        self.assertEqual(section_of(user, "## Not shown").strip(), "None.")

    def test_lmr_ec_03_an_oversized_task_diff_drops_its_largest_file_first(self) -> None:
        self.task_commit({"big.py": "b = 1\n" * 1500, "small.py": "s = 1\n" * 50})
        task = self.slices()[0]
        full = local_review.estimate_tokens(local_review.render_user(task))
        fitted = local_review.fit(task, full - 2000)
        user = local_review.render_user(fitted)
        self.assertIn("+s = 1", user)
        self.assertNotIn("+b = 1", user)
        self.assertIn("- big.py", section_of(user, "## Not shown"))
        self.assertEqual(fitted.omitted, ("big.py",))
        self.assertLessEqual(local_review.estimate_tokens(user), full - 2000)

    def test_lmr_ec_04_never_cut_content_larger_than_the_budget(self) -> None:
        self.write(f"{EPIC}/task_1_demo.md", TASK_FILE + "x" * 4000 + "\n")
        self.task_commit({"src/a.py": "print('a')\n"})
        with self.assertRaises(local_review.LocalReviewError) as caught:
            local_review.fit(self.slices()[0], 1000)
        self.assertIn("task_1_demo needs", str(caught.exception))
        self.assertIn("but the budget is 1000; raise --num-ctx", str(caught.exception))

    def test_lmr_ec_06_a_legacy_task_joins_the_epic_slice(self) -> None:
        self.task_commit({"src/a.py": "print('a')\n"})
        self.write("src/legacy.py", "legacy = True\n")
        self.commit("Legacy work")
        task, epic = self.slices()
        self.assertEqual(task.paths, ("src/a.py",))
        self.assertEqual(epic.paths, ("src/legacy.py",))
        outside = section_of(local_review.render_user(epic), "## Commits outside tasks")
        self.assertIn("Legacy work", outside)
        self.assertIn("+legacy = True", outside)
        self.assertNotIn("print('a')", outside)

    def test_the_epic_slice_drops_outside_commits_then_the_spec_then_the_hld(self) -> None:
        self.write(f"{EPIC}/2026-01-01-demo-design.en.md", "# Demo Spec\n\nspec-marker\n" + "s" * 3000 + "\n")
        self.write(f"{EPIC}/demo.en.md", "# Demo HLD\n\nhld-marker\n" + "h" * 3000 + "\n")
        self.task_commit({"src/a.py": "print('a')\n"})
        self.write("src/legacy.py", "legacy = True\n")
        self.commit("Legacy work")
        short = git(self.root, "rev-parse", "--short", "HEAD")
        epic = self.slices()[1]
        user = local_review.render_user(epic)
        for heading, marker in (("## Spec", "spec-marker"), ("## HLD", "hld-marker"), ("## Audit", "audit-output"),
                                ("## Traceability", "results-output"), ("## Diff stat", "src/legacy.py")):
            self.assertIn(marker, section_of(user, heading))
        full = local_review.estimate_tokens(user)
        self.assertEqual(local_review.fit(epic, full - 1).omitted, (f"{short} Legacy work",))
        self.assertEqual(local_review.fit(epic, full - 600).omitted,
                         (f"{short} Legacy work", "2026-01-01-demo-design.en.md"))
        floor = local_review.fit(epic, full - 1600)
        self.assertEqual(floor.omitted, (f"{short} Legacy work", "2026-01-01-demo-design.en.md", "demo.en.md"))
        self.assertIn("audit-output", section_of(local_review.render_user(floor), "## Audit"))


SKILLS = Path(__file__).resolve().parents[3]
REFERENCES = SKILLS / "dev-implementation" / "references"
RULE_ID = re.compile(r"`([A-Z]+(?:-[A-Z]+)*-\d{2})`")
BOLD = re.compile(r"\*\*(.+?)\*\*")


class PromptBaseTest(unittest.TestCase):
    def platforms(self) -> str:
        return (REFERENCES / "local-review-platforms.md").read_text(encoding="utf-8")

    def test_lmr_hp_05_the_system_message_fits_its_pass_type(self) -> None:
        task = local_review.Slice("task_1_demo", "task", ("lib/a.dart",), ())
        system = local_review.render_system(task)
        checklists = (REFERENCES / "local-review-checklists.md").read_text(encoding="utf-8")
        for expected in ("Decisions Already Made", "No Reconstructed Logic", "Verdict: PASS",
                         local_review.platform_sections(["lib/a.dart"])[0], "## Task pass",
                         (section(checklists, "Task pass") or "missing").strip()):
            self.assertIn(expected, system)
        for placeholder in ("$rules", "$platform_rules", "$checklist"):
            self.assertNotIn(placeholder, system)
        epic = local_review.render_system(local_review.Slice("epic", "epic", (), ()))
        self.assertIn("## Epic pass", epic)
        self.assertIn((section(checklists, "Epic pass") or "missing").strip(), epic)
        self.assertNotIn("## Task pass", epic)

    def test_lmr_hp_07_every_quoted_platform_rule_exists_in_the_kit(self) -> None:
        audits = {name: (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                  for name in ("architecture-audit", "code-health-audit", "security-audit")}
        rows = [line for text in audits.values() for line in text.splitlines() if "Blocker" in line]
        for platform, family in (("Flutter", "-FLUTTER-"), ("Android", None), ("iOS", "-IOS-")):
            ids = RULE_ID.findall(section(self.platforms(), platform) or "")
            self.assertGreater(len(ids), 0, platform)
            for rule in ids:
                self.assertTrue(any(f"**{rule}**" in row for row in rows), f"{rule} is not a Blocker row")
                if family:
                    self.assertIn(family, rule)
                else:
                    self.assertNotRegex(rule, "-(FLUTTER|IOS)-")
        for platform, reference, count in (
                ("Rust", "rust-quality-check/references/rust-architecture-governance.md", 5),
                ("Python", "python-quality-check/references/python-architecture-governance.md", 4)):
            names = BOLD.findall(section(self.platforms(), platform) or "")
            self.assertEqual(len(names), count, platform)
            source = (SKILLS / reference).read_text(encoding="utf-8")
            for name in names:
                self.assertIn(f"**{name}**", source)

    def test_lmr_ec_05_platform_sections_follow_the_touched_extensions(self) -> None:
        found = local_review.platform_sections(["app/lib/a.dart", "native/src/b.rs"])
        self.assertEqual([text.splitlines()[0] for text in found], ["## Flutter", "## Rust"])
        self.assertEqual(local_review.platform_sections(["README.md", "web/x.ts"]), [])
        self.assertEqual(len(local_review.platform_sections(["a/B.kt", "build.gradle.kts"])), 1)
        system = local_review.render_system(local_review.Slice("task_1_demo", "task", ("README.md", "web/x.ts"), ()))
        self.assertIn("No platform rules apply to this slice.", system)


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
