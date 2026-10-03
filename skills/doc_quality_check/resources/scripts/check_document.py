#!/usr/bin/env python3
"""Mechanical checks for a document work item — the Kind: document path of quality_check.

Prose instructions to "check every link resolves" are exactly the kind of step that gets
skipped under load, so the mechanical half of Gate 2 is a script rather than a checklist.

Usage:
  check_document.py FILE [FILE ...]           run the mechanical checks
  check_document.py --require-toc FILE ...    require a complete table of contents
  check_document.py --require-bilingual FILE ... require matching .en.md/.vi.md files
  check_document.py --changed-files F [F ...] apply the refusal rule and exit

--require-toc and --require-bilingual apply to lifecycle deliverables. They are opt-in because
task files, epic records and SKILL.md files are not deliverables and were never meant to carry
either contract.

Exit 0 clean, 1 on any finding.
"""

import argparse
import pathlib
import re
import sys

# Extensions that ship in a build. A document work item that touches one of these is
# development work, whatever the Kind field claims.
SHIPPED_SUFFIXES = {
    ".dart", ".kt", ".kts", ".java", ".swift", ".m", ".mm", ".h", ".c", ".cc", ".cpp",
    ".gradle", ".pbxproj", ".plist", ".xml", ".yaml", ".yml", ".json", ".lock",
    ".ts", ".tsx", ".js", ".jsx", ".py", ".rb", ".go", ".rs",
}
# …except these, which are documentation or workspace infrastructure despite the extension.
SHIPPED_EXCEPTIONS = re.compile(r"(?:^|/)(\.devtool|docs|\.github)/|(?:^|/)CHANGELOG\.md$")

PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|XXX)\b")

TOC_HEADING = re.compile(
    r"^##\s+.*(?:table of contents|contents|mục lục)\s*$", re.IGNORECASE
)


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code spans, preserving line numbering.

    A document that documents the placeholder check would otherwise fail it — observed, not
    hypothetical. verify.sh step 3 strips the same way before checking links.
    """
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def anchor(heading: str) -> str:
    h = re.sub(r"^#+\s*", "", heading).rstrip().lower()
    h = re.sub(r"[^\w\s-]", "", h)
    return "#" + h.replace(" ", "-")


def check_file(path: pathlib.Path, require_toc: bool = False) -> list:
    findings = []
    raw = path.read_text()
    prose = strip_code(raw)
    lines = prose.split("\n")

    for i, line in enumerate(lines, 1):
        m = PLACEHOLDER.search(line)
        if m:
            findings.append((path, i, f"placeholder {m.group(1)} in prose"))

    fences = sum(1 for ln in raw.split("\n") if ln.lstrip().startswith("```"))
    if fences % 2:
        findings.append((path, 0, f"unbalanced code fences ({fences} found)"))

    headings = [anchor(ln) for ln in raw.split("\n") if re.match(r"^#{1,6} ", ln)]
    for i, line in enumerate(lines, 1):
        for link in re.findall(r"\]\(([^)]+)\)", line):
            if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
                continue
            if link.startswith("#"):
                if link.lower() not in headings:
                    findings.append((path, i, f"anchor has no matching heading: {link}"))
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if not target.exists():
                findings.append((path, i, f"link does not resolve: {link}"))

    if require_toc:
        sections = [ln for ln in raw.split("\n") if re.match(r"^##\s+", ln)]
        plan_tasks = [ln for ln in raw.split("\n") if re.match(r"^###\s+Task\s+", ln)]
        navigable_headings = sections + plan_tasks
        toc_sections = [ln for ln in sections if TOC_HEADING.match(ln)]
        linked_anchors = set(re.findall(r"\]\((#[^)]+)\)", prose.lower()))
        if not toc_sections:
            findings.append((path, 0, "no table of contents heading — a reader cannot navigate it"))
        for heading in navigable_headings:
            if TOC_HEADING.match(heading):
                continue
            heading_anchor = anchor(heading)
            if heading_anchor not in linked_anchors:
                findings.append((path, 0,
                                 f"table of contents does not link section: {heading}"))
    return findings


def check_language_pairs(paths: list[pathlib.Path]) -> list:
    """Require every lifecycle document to have matching English and Vietnamese files."""
    findings = []
    normalized = {path.resolve() for path in paths}
    for path in paths:
        name = path.name
        if name.endswith(".en.md"):
            counterpart = path.with_name(name[:-6] + ".vi.md")
        elif name.endswith(".vi.md"):
            counterpart = path.with_name(name[:-6] + ".en.md")
        else:
            findings.append((path, 0,
                             "lifecycle document must use an .en.md or .vi.md language suffix"))
            continue
        if counterpart.resolve() not in normalized:
            state = "missing" if not counterpart.exists() else "not included in this check"
            findings.append((path, 0, f"language counterpart {state}: {counterpart.name}"))
            continue
        if name.endswith(".en.md"):
            english_structure = heading_structure(path)
            vietnamese_structure = heading_structure(counterpart)
            if english_structure != vietnamese_structure:
                findings.append((path, 0,
                                 "English/Vietnamese heading structure differs: "
                                 f"{english_structure} != {vietnamese_structure}"))
    return findings


def heading_structure(path: pathlib.Path) -> list[int]:
    """Return heading levels so translated pairs can be checked without comparing wording."""
    return [len(match.group(1))
            for line in path.read_text().splitlines()
            if (match := re.match(r"^(#{1,6})\s+", line))]


def refusal(changed: list) -> list:
    offenders = []
    for f in changed:
        p = pathlib.PurePosixPath(f)
        if SHIPPED_EXCEPTIONS.search(str(p)):
            continue
        if p.suffix in SHIPPED_SUFFIXES:
            offenders.append(f)
    return offenders


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--changed-files", nargs="*", default=None)
    ap.add_argument("--require-toc", action="store_true",
                    help="require a complete table of contents (lifecycle deliverables)")
    ap.add_argument("--require-bilingual", action="store_true",
                    help="require matching .en.md and .vi.md lifecycle documents")
    args = ap.parse_args()

    if args.changed_files is not None:
        offenders = refusal(args.changed_files)
        if offenders:
            print("  ABORT this is development work, not a document work item:")
            for f in offenders:
                print(f"    ships in the build: {f}")
            print("  Route it through dev-lifecycle. Kind: document cannot verify it.")
            return 1
        print(f"  ok   refusal rule: none of {len(args.changed_files)} changed files ship in the build")
        return 0

    if not args.files:
        print("  FAIL no files given — check the invocation, not the content")
        return 1

    findings = []
    paths = [pathlib.Path(f) for f in args.files]
    for path in paths:
        findings += check_file(path, require_toc=args.require_toc)
    if args.require_bilingual:
        findings += check_language_pairs(paths)
    for path, line, msg in findings:
        where = f"{path}:{line}" if line else str(path)
        print(f"  FAIL {where} — {msg}")
    print(f"  checked {len(args.files)} documents, {len(findings)} findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
