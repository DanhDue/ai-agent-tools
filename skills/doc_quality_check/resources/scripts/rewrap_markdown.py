import re, sys, pathlib

WIDTH = 100
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
            out.append(cur); cur = ""
    if cur: out.append(cur)
    return out

def wrap(text, first="", sub=None):
    sub = first if sub is None else sub
    toks, lines, cur = atoms(text), [], []
    if not toks: return []
    for t in toks:
        pref = first if not lines else sub
        if cur and len(pref) + len(" ".join(cur + [t])) > WIDTH:
            cut = len(cur)
            for j in range(len(cur) - 1, max(0, len(cur) - 4) - 1, -1):
                if cur[j].rstrip("*`)").endswith(CLAUSE_END): cut = j + 1; break
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

def rewrap(path):
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
            out += wrap(" ".join(buf), pre, " " * len(pre))
        else:
            buf = []
            while i < len(src) and src[i].strip() and not src[i].startswith(("|", "#", ">", "```")) \
                  and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", src[i]):
                buf.append(src[i].strip()); i += 1
            out += wrap(" ".join(buf))
        if i == start:
            raise RuntimeError(f"{path}: parser stalled at line {i+1}: {src[i]!r}")
    return "\n".join(out)

for path in sys.argv[1:]:
    before = pathlib.Path(path).read_text()
    after = rewrap(path)
    def norm(t):
        # line-leading > is blockquote markup, and rewrapping legitimately moves it
        return " ".join(" ".join(re.sub(r"^>\s?", "", l) for l in t.split("\n")).split())
    if norm(before) != norm(after):
        print(f"  REFUSED {path}: content would change, not just wrapping"); continue
    pathlib.Path(path).write_text(after)
    print(f"  rewrapped {path}")
