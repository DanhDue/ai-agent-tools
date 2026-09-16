#!/usr/bin/env python3
"""Fail if a methodology skill drifts back to an error its source review already corrected.

This repository teaches external methodologies. Every one of them reached the kit through an
LLM's recollection or an LLM-written summary at least once, and every time the result read as
plausible expert advice while contradicting the source. Each such error is cheap to reintroduce
in a one-line edit and expensive to notice, because nothing downstream reads the source.

Each entry in SOURCES pairs a methodology with the files derived from it and the patterns that
catch its known regressions. Evidence, with the authors' own wording, lives in the
`source_fidelity_review.md` of the epic that introduced the source.

Add a source by appending to SOURCES — never by forking this script.
"""

import pathlib
import re
import sys

# Evidence documents quote the errors in order to name them as errors. Scanning them would
# report the correction as the regression, so they are never targets.
EXCLUDED_NAMES = {"source_fidelity_review.md"}

# Each source: name, the globs of files derived from it, and (label, pattern) checks whose
# label states the CORRECT rule, so a failure explains itself without opening another file.
# `required` means the globs must match something — an empty match is a broken glob, not a
# clean bill of health. New sources start unrequired until the skills that use them exist.
SOURCES = [
    {
        "name": "The Lean Product Playbook — Olsen, 2015",
        "evidence": ".devtool/epic/lean_product_suite/source_fidelity_review.md",
        "globs": ["skills/lean-*/**/*.md", "docs/books/*.md"],
        "required": True,
        "checks": [
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
        ],
    },
    {
        "name": "Diátaxis — Daniele Procida, diataxis.fr",
        "evidence": ".devtool/epic/document_lifecycle_suite/source_fidelity_review.md",
        "globs": [
            "skills/doc-*/**/*.md",
            ".devtool/epic/document_lifecycle_suite/*.md",
        ],
        "required": True,
        "checks": [
            (
                "Diátaxis axes are action/cognition and acquisition/application, not theory/practice",
                r"(?i)\btheory\s*[/×x]\s*practice\b|\bstudy\s*[/×x]\s*work\b",
            ),
            (
                "Diátaxis has FOUR types: tutorial, how-to guide, reference, explanation",
                r"(?i)(three|five|3|5)\s+diátaxis\s+(mode|type)s?"
                r"|diátaxis[^\n]{0,15}\b(three|five)\s+(mode|type)s?",
            ),
            (
                "Procida: a how-to guide carries 'no digression, explanation, teaching'",
                r"(?i)how-to\s+guides?[^\n]{0,70}\b(should|must|can|may)\b[^\n]{0,20}\b(explain|teach)",
            ),
        ],
    },
    {
        "name": "Documenting Architecture Decisions — Michael Nygard, 2011",
        "evidence": ".devtool/epic/document_lifecycle_suite/source_fidelity_review.md",
        "globs": [
            "skills/decision-records/**/*.md",
            ".devtool/epic/document_lifecycle_suite/*.md",
        ],
        "required": True,
        "checks": [
            (
                "Rejected alternatives come from later ADR templates — Nygard's 2011 article "
                "does not mention them, so do not cite him for that rule",
                r"(?i)(record|document)\w*\s+the\s+rejected\s+alternatives",
            ),
            (
                "Nygard's section order is Title, Context, Decision, Status, Consequences",
                r"(?i)title\s*/\s*status\s*/\s*context",
            ),
            (
                "Nygard: 'All consequences should be listed here, not just the positive ones' "
                "— positive, negative AND neutral",
                r"(?i)consequences[^\n]{0,50}\bonly\s+(the\s+)?positive",
            ),
        ],
    },
]

# A line that names an error in order to warn against it is the correction working, not a
# regression. Prose wraps, so the disclaimer is looked for in a small window around the match
# rather than on the matching line alone. Keep this list tight: anything it excuses stops
# being checked.
CONTEXT_LINES = 1

DISCLAIMER = re.compile(
    r"(?i)"
    r"not\s+(a\s+rule|attribut\w*|olsen'?s?|nygard'?s?|procida'?s?|in\s+this\s+book|in\s+the\s+source)"
    r"|does\s+\*\*not\*\*|do\s+not\s+attribut|never\s+attribut|do\s+not\s+cite"
    r"|brandon\s+schauer|wrong|harmful|anti-rule|red flag|\[!WARNING\]|\[!CAUTION\]"
    r"|instead\s+of|rather\s+than|will eventually cut"
    r"|later\s+(adr\s+)?template|this kit'?s own addition|divergence"
    r"|không\s+có\s+trong|không\s+phải|ẩn\s+dụ|của\s+Brandon"
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


def targets_for(source) -> list:
    found = []
    for pattern in source["globs"]:
        found += list(ROOT.glob(pattern))
    return sorted({f for f in found if f.is_file() and f.name not in EXCLUDED_NAMES})


def main() -> int:
    bad = 0
    total = 0

    for source in SOURCES:
        targets = targets_for(source)
        if not targets:
            if source.get("required"):
                print(f"  FAIL {source['name']}: no target files — check the glob, not the content")
                bad = 1
            else:
                print(f"  note {source['name']}: no target files yet — checks pending")
            continue
        total += len(targets)

        for label, pattern in source["checks"]:
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

    rules = sum(len(s["checks"]) for s in SOURCES)
    print(f"  checked {total} files against {rules} source-fidelity rules "
          f"from {len(SOURCES)} sources")
    return bad


if __name__ == "__main__":
    sys.exit(main())
