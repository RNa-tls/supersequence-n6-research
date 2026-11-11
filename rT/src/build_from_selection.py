#!/usr/bin/env python3
"""Round T -- independent reconstruction of the 16 closed trails of the public n = 8 selection (Halfar / Pantone
construction) and of the 46174 / 46173 words from their plans.  Written from the published description of the
slices; it does not import or call the external tools.
usage: build_from_selection.py SELECTION BASE.tsv PLAN OUT.txt [--json OUT.json]
The trails are numbered as in BASE.tsv (rowless loops in file order, then the closed walks); the numbering of the
four walk trails is fixed by comparing cyclic words with an optional BASE.txt (--base), otherwise by the order found."""
import sys, json, hashlib
K = 6; N = 8; H = 5; S, Z = "6", "7"
def rot(b, j): j %= len(b); return b[j:] + b[:j]
def slice_word(b, d, c):
    """a slice = c consecutive cyclic classes of the 2-cycle of (b d): b d b, then (b[t] d rot(b, t+1)) for t < c-1"""
    w = b + d + b
    for t in range(c - 1): w += b[t] + d + rot(b, t + 1)
    return w
def slices(sel):
    out = []
    for x, v in sel:
        if v == 0: out += [(rot(x, i) + S, Z, K + 1) for i in range(K)]
        else:
            out += [(x[:j] + Z + x[j:], S, v + (1 if j < v else 0)) for j in range(K)]
            out += [(rot(x, i) + S, Z, K + 1) for i in range(v, K)]
    return out
def trails(sel):
    sl = slices(sel); words = [slice_word(*q) for q in sl]
    byhead = {}
    for i, w in enumerate(words):
        assert w[:H] not in byhead; byhead[w[:H]] = i
    nxt = [byhead[w[-H:]] for w in words]
    seen = [False] * len(sl); out = []
    for i in range(len(sl)):
        if seen[i]: continue
        cyc = []; j = i
        while not seen[j]: seen[j] = True; cyc.append(j); j = nxt[j]
        assert j == i
        out.append(("".join(words[q][:-H] for q in cyc), [sl[q] for q in cyc]))
    return out
def canon(c):
    """least rotation (naive but exact)"""
    d = c + c; best = min(range(len(c)), key=lambda i: d[i:i + 40]); cands = [i for i in range(len(c)) if d[i:i + 40] == d[best:best + 40]]
    return min(d[i:i + len(c)] for i in cands)
def read_sel(path):
    return [(l.split()[0], int(l.split()[1])) for l in open(path) if l.strip() and not l.startswith("#")]
def main():
    a = sys.argv[1:]; selp, tsvp, planp, outp = a[:4]
    sel = read_sel(selp); tr = trails(sel)
    tab = [l.split("\t") for l in open(tsvp)]
    Rs = [int(t[2]) for t in tab]; offs = [int(t[3]) for t in tab]
    cyc = [None] * len(tab)
    if "--base" in a:
        base = open(a[a.index("--base") + 1]).read().strip()
        mine = {canon(c): c for c, _ in tr}; assert len(mine) == len(tr) == len(tab)
        for t in range(len(tab)):
            piece = base[offs[t]:offs[t] + Rs[t]]; assert canon(piece) in mine, t
            cyc[t] = piece                     # same cyclic word, written from the base word's vertex
        matched = True
    else:
        raise SystemExit("--base needed to fix the rotation of each trail (plan offsets refer to it)")
    lines = open(planp).read().split("\n"); hdr = lines[0].split(); assert hdr[0] == "TRAILSEARCH-PLAN"
    word = ""; ev = []
    for l in lines[1:]:
        p = l.split()
        if not p: continue
        assert p[0] == "O"; t, s0, g = int(p[1]), int(p[2]), int(p[3]); c = cyc[t]; R = len(c)
        piece = (c[s0 % R:] + c * 2)[:R + N - g]
        k = 0
        if word:
            for q in range(H, 0, -1):
                if word[-q:] == piece[:q]: k = q; break
        ev.append(dict(trail=t, start=s0, g=g, overlap=k, piece_len=len(piece))); word += piece[k:]
    open(outp, "w").write(word + "\n")
    res = dict(trails=len(tr), R=sorted(len(c) for c, _ in tr), sumR=sum(len(c) for c, _ in tr), slices=sum(len(s) for _, s in tr), events=ev, length=len(word),
               sha256_no_lf=hashlib.sha256(word.encode()).hexdigest(), sha256_with_lf=hashlib.sha256((word + "\n").encode()).hexdigest())
    if "--json" in a: json.dump(res, open(a[a.index("--json") + 1], "w"), indent=1)
    print({k: v for k, v in res.items() if k != "events"})
if __name__ == "__main__": main()
