#!/usr/bin/env python3
"""Fail if the Lean Product suite drifts back to its corrected errors.

Six behaviour-changing errors reached this repository through LLM-written summaries of
*The Lean Product Playbook* and propagated through four layers of derived artefacts before
anyone opened the book. Each is cheap to reintroduce in a one-line edit and expensive to
notice, because every one of them still reads as plausible product-management advice.

Evidence, with the author's own wording:
.devtool/epic/lean_product_suite/source_fidelity_review.md
"""

import pathlib
import re
import sys

# (label, pattern) — label states the correct rule, so a failure explains itself.
CHECKS = [
    (
        "PMF Pyramid has FIVE layers; the Lean Product Process has six STEPS",
        r"(?i)(six|6)[- ]layer\w*\s+(product-market fit\s+)?pyramid"
        r"|pyramid\w*\s+(has|with)\s+(six|6)\s+layers"
        r"|kim tự tháp\s+\w*\s*6 tầng",
    ),
    (
        "Ulwick's bar is > 15; >= 10 is the floor of the UNATTRACTIVE band",
        r"(?i)\bOS\b\s*(>=|≥|\\ge)\s*10"
        r"|opportunity score\s*(>=|≥|\\ge)\s*10",
    ),
    (
        "Figure 7.1 is Jussi Pasanen's; the cupcake metaphor is Brandon Schauer's, not Olsen's",
        r"(?i)cupcake",
    ),
    (
        "MVP membership follows the composition rule, not an ROI rank cut-off",
        r"(?i)cells?\s*1\s*[-–]\s*3|ô\s*1\s*[-–]\s*3",
    ),
    (
        "Guardrail 1 is capture-convert-park; Olsen's rule is separate and alternate, not forbid",
        r"(?i)guardrail 1[^\n]{0,90}\b(ban|banned|forbid|refus\w*|reject\w*)\b",
    ),
]

# A line that names an error in order to warn against it is the correction working, not a
# regression. Prose wraps, so the disclaimer is looked for in a small window around the match
# rather than on the matching line alone. Keep this list tight: anything it excuses stops
# being checked.
CONTEXT_LINES = 1

DISCLAIMER = re.compile(
    r"(?i)"
    r"not\s+(a\s+rule|attribut\w*|olsen'?s?|in\s+this\s+book)"
    r"|does\s+\*\*not\*\*|do\s+not\s+attribut|never\s+attribut"
    r"|brandon\s+schauer|wrong|harmful|anti-rule|red flag|\[!WARNING\]"
    r"|instead\s+of|rather\s+than|will eventually cut"
    r"|không\s+có\s+trong|không\s+phải|ẩn\s+dụ|của\s+Brandon"
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    targets = sorted(
        list((ROOT / "skills").glob("lean-*/**/*.md"))
        + list((ROOT / "docs" / "books").glob("*.md"))
    )
    if not targets:
        print("  FAIL no Lean Product files found — check the glob, not the content")
        return 1

    bad = 0
    for label, pattern in CHECKS:
        rx = re.compile(pattern)
        for f in targets:
            lines = f.read_text().split("\n")
            for idx, line in enumerate(lines):
                if not rx.search(line):
                    continue
                lo = max(0, idx - CONTEXT_LINES)
                window = " ".join(lines[lo:idx + CONTEXT_LINES + 1])
                if DISCLAIMER.search(window):
                    continue
                rel = f.relative_to(ROOT)
                print(f"  FAIL {rel}:{idx + 1} — {label}")
                print(f"       {line.strip()[:110]}")
                bad = 1

    print(f"  checked {len(targets)} files against {len(CHECKS)} source-fidelity rules")
    return bad


if __name__ == "__main__":
    sys.exit(main())
