import re, sys, pathlib

WIDTH = 100
MIN_FILL = 85
SLACK = 10      # characters a short line may run over rather than strand a span on its own
MAX_ATOM = 80   # longest span kept unbroken; measured against these docs, only 4 spans sit in 61-80
CLAUSE_END = tuple(",;:.—?!")

# Vietnamese writes compounds as separate syllables, so a whitespace wrapper cannot see that
# "cấu trúc" is one word. Ending a line on any of these strands half a word or a bare classifier.
NEVER_END = {
    "một", "các", "những", "mỗi", "từng", "cái", "chiếc", "bộ", "bản",
    "sự", "việc", "điều", "cách", "thứ", "vấn", "cấu", "bất", "khả", "nội", "đơn",
    "kiểm", "phân", "quyết", "thực", "kết", "công", "tài", "quy", "giải", "tham",
    "phê", "xác", "bao", "trao", "hoàn", "tiến", "chuyển", "định", "hiện", "phát",
}

def _balanced(chunk):
    """True when no markdown span is left open across a line break."""
    if chunk.count("`") % 2: return False
    if chunk.count("**") % 2: return False
    if (chunk.count("*") - 2 * chunk.count("**")) % 2: return False
    if chunk.count("[") != chunk.count("]"): return False
    if chunk.count("](") and chunk.count("(") != chunk.count(")"): return False
    return True

def atoms(text):
    """Whitespace tokens, merged until every markdown span closes.

    Vietnamese is monosyllabic, so a greedy wrap splits inside phrases constantly; keeping
    emphasis and code spans whole is the minimum that stops a line ending mid-`**bold`.
    """
    out, cur = [], ""
    for tok in text.split():
        cur = tok if not cur else cur + " " + tok
        if _balanced(cur):
            # A long span held whole forces everything around it onto stub lines, and markdown
            # renders **a\nb** as bold anyway — so keeping it intact buys readability only while
            # it is short. Past that, let it wrap like ordinary words.
            # A link must never break — the syntax would stop working. Emphasis and code spans
            # may, because markdown still renders them across a line break.
            is_link = "](" in cur
            out += [cur] if (is_link or len(cur) <= MAX_ATOM) else cur.split()
            cur = ""
    if cur: out += cur.split()
    return out

def wrap(text, first="", sub=None):
    sub = first if sub is None else sub
    toks, lines, cur = atoms(text), [], []
    if not toks: return []
    for t in toks:
        pref = first if not lines else sub
        # A span that will not fit would otherwise leave a stub line in front of it. Allow a
        # bounded overflow instead — capped, because an unbounded version produced 231-character
        # lines the first time this was tried.
        proposed = len(pref) + len(" ".join(cur + [t]))
        room = WIDTH + (SLACK if cur and len(pref) + len(" ".join(cur)) < MIN_FILL else 0)
        if cur and proposed > room:
            cut = len(cur)
            # Back off to a clause boundary only when it is nearly free. English puts a comma
            # within a few words of almost any position, so an unconditional preference shortens
            # every line and leaves the right margin ragged — 39 characters next to 97.
            for j in range(len(cur) - 1, max(0, len(cur) - 4) - 1, -1):
                if not cur[j].rstrip("*`)").endswith(CLAUSE_END): continue
                if len(pref) + len(" ".join(cur[:j + 1])) >= MIN_FILL:
                    cut = j + 1
                break
            # never strand a compound's first syllable or a bare classifier at a line end
            while cut > 1 and cur[cut - 1].strip("*`_").lower() in NEVER_END:
                cut -= 1
            lines.append(pref + " ".join(cur[:cut])); cur = cur[cut:] + [t]
        else:
            cur.append(t)
    if cur: lines.append((first if not lines else sub) + " ".join(cur))
    # Pull a word down onto a stubby final line — but never at the cost of stranding a compound
    # head on the line above. Fixing an orphan by creating a split word is a worse trade.
    if len(lines) > 1 and len(lines[-1].strip()) - len(sub.strip()) < 24:
        prev = lines[-2].split()
        if len(prev) > 3 and prev[-2].strip("*`_").lower() not in NEVER_END:
            moved = prev.pop()
            lines[-2] = " ".join(prev)
            lines[-1] = sub + moved + " " + lines[-1][len(sub):].lstrip()
    return lines


MASK = re.compile(r"`[^`]+`|\[[^\]]+\]\([^)]+\)")

def semantic_units(text):
    """Split prose where the sentence itself breaks, never at an arbitrary column.

    Sentences first. A sentence that still overruns the margin is split again at its own
    semicolons and em-dashes — a pressure valve, so short sentences stay on one line.
    """
    keep = []
    def hide(m):
        keep.append(m.group(0)); return "\x00%d\x00" % (len(keep) - 1)
    masked = MASK.sub(hide, text)
    restore = lambda p: re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], p).strip()
    out = []
    for sent in re.split(r"(?<=[.?!])\s+(?=[A-Z\x00*>])", masked):
        if not sent.strip(): continue
        out += _relieve([sent])
    return [restore(u) for u in out if u.strip()]


# Applied in order, and only while a unit still overruns the margin. Each is a weaker join than
# the one before, so a sentence breaks at its strongest internal seam first.
SEAMS = [
    r"(?<=;)\s+|\s+(?=— )",                                   # semicolon, em-dash
    r"(?<=:)\s+(?=[a-z\x00*])",                                # colon introducing a clause
    r"(?<=,)\s+(?=(?:so|and|but|or|which|while|rather|because|then)\b)",
    r"(?<=,)\s+",                                             # any comma, last resort
]


def _relieve(units, depth=0):
    if depth >= len(SEAMS):
        return units
    out = []
    for u in units:
        if len(u) <= WIDTH:
            out.append(u)
        else:
            parts = [c for c in re.split(SEAMS[depth], u) if c.strip()]
            out += _relieve(parts, depth + 1) if len(parts) > 1 else _relieve([u], depth + 1)
    return out

def pack_semantic(text, first="", sub=None):
    sub = first if sub is None else sub
    lines, cur = [], ""
    for u in semantic_units(text):
        pref = first if not lines else sub
        if cur and len(pref) + len(cur) + 1 + len(u) > WIDTH:
            lines.append(pref + cur); cur = u
        else:
            cur = u if not cur else cur + " " + u
    if cur: lines.append((first if not lines else sub) + cur)
    return lines

def rewrap(path, semantic=False):
    src = pathlib.Path(path).read_text().split("\n")
    out, i, fence = [], 0, False
    while i < len(src):
        start = i
        ln = src[i]
        if ln.lstrip().startswith("```"):
            fence = not fence; out.append(ln); i += 1
        elif fence or ln.startswith(("|", "#")) or not ln.strip():
            out.append(ln); i += 1
        elif ln.startswith(">"):
            buf = []
            while i < len(src) and src[i].startswith(">"):
                body = re.sub(r"^>\s?", "", src[i]); i += 1
                if body.strip(): buf.append(body)
                else:
                    if buf: out += wrap(" ".join(buf), "> ", "> "); buf = []
                    out.append(">")
            if buf: out += wrap(" ".join(buf), "> ", "> ")
        elif re.match(r"^\s*(?:[-*]|\d+\.)\s+", ln):
            pre = re.match(r"^(\s*(?:[-*]|\d+\.)\s+)", ln).group(1)
            buf = [ln[len(pre):]]; i += 1
            while i < len(src) and src[i].strip() and src[i].startswith(" " * len(pre)) \
                  and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", src[i]):
                buf.append(src[i].strip()); i += 1
            out += (pack_semantic if semantic else wrap)(" ".join(buf), pre, " " * len(pre))
        else:
            buf = []
            while i < len(src) and src[i].strip() and not src[i].startswith(("|", "#", ">", "```")) \
                  and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", src[i]):
                buf.append(src[i].strip()); i += 1
            out += (pack_semantic if semantic else wrap)(" ".join(buf))
        if i == start:
            raise RuntimeError(f"{path}: parser stalled at line {i+1}: {src[i]!r}")
    return "\n".join(out)

SEMANTIC = "--semantic" in sys.argv
for path in [a for a in sys.argv[1:] if not a.startswith("--")]:
    before = pathlib.Path(path).read_text()
    after = rewrap(path, semantic=SEMANTIC)
    def norm(t):
        # line-leading > is blockquote markup, and rewrapping legitimately moves it
        return " ".join(" ".join(re.sub(r"^>\s?", "", l) for l in t.split("\n")).split())
    if norm(before) != norm(after):
        print(f"  REFUSED {path}: content would change, not just wrapping"); continue
    pathlib.Path(path).write_text(after)
    print(f"  rewrapped {path}")
