#!/usr/bin/env python3
"""Round T -- slice structure of closed trails given as cyclic words: maximal chains of runs linked by weight-2 steps
(slices), with the distinguished letter d of each slice (the letter that keeps its place while the other seven rotate),
and the number of classes c.  Used to compare the old 6A+24phi family with the public selection.
usage: slice_structure.py old FAMILY.json | new SEL TSV BASE"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model
N = 8
def slices(c):
    rs = model.runs_of(c); R = len(c); d = c + c
    # rotate so that we start after a weight-3 link
    i0 = next(i for i in range(len(rs)) if rs[i - 1][2] == 3)
    rs = rs[i0:] + rs[:i0]; out = []; cur = []
    for r in rs:
        cur.append(r)
        if r[2] == 3: out.append(cur); cur = []
    assert not cur
    res = []
    for sl in out:
        p0 = d[sl[0][0]:sl[0][0] + N]
        if len(sl) == 1: res.append((None, 1, sl[0][1])); continue
        p1 = d[sl[1][0]:sl[1][0] + N]
        # weight-2 step: abcdefgh -> cdefgh b a ; within a slice b d b / b[t] d rot: the distinguished letter is the one
        # that is at the same position (index 7) in the first permutations of consecutive classes
        same = [x for x in "01234567" if p0.index(x) == p1.index(x)]
        res.append((same[0] if len(same) == 1 else "?", len(sl), sl[0][1]))
    return res
def expand(w):
    """old family format: 8 letters per class visit (the first permutation of the run) -> cyclic letter word"""
    ps = [w[i:i + 8] for i in range(0, len(w), 8)]; out = ""
    for a, b in zip(ps, ps[1:] + ps[:1]):
        last = a[7] + a[:7]; k = next(k for k in range(7, -1, -1) if last[8 - k:] == b[:k] or k == 0)
        out += a + a[:7 - k] if k <= 7 else ""
        # letters of this run that are not overlapped by the next run's first permutation: 15 - k
    return out
if __name__ == "__main__":
    if sys.argv[1] == "old":
        fam = json.load(open(sys.argv[2])); cycs = {}
        for t in fam["trails"]:
            for v, w in enumerate(t["versions"]): cycs[(t["trail"], v)] = expand(w)
    else:
        cycs = {(t, 0): c for t, c in enumerate(model.load(*sys.argv[2:5]))}
    tot = collections.Counter(); nat3 = collections.Counter()
    for key, c in sorted(cycs.items()):
        sl = slices(c); h = collections.Counter((d, n) for d, n, _ in sl); tot.update(h)
        if key[1] == 0: nat3[len(c)] += len(sl)
        if key[0] in (0, 1, 12, 29) or len(c) > 500 and key[0] < 3: print(key, "R", len(c), "runs", sum(n for _, n, _ in sl), "slices", len(sl), dict(sorted(h.items(), key=str)))
    print("total (d, c) histogram:", dict(sorted(tot.items(), key=str))); print("weight-3 natural links per R (version 0):", dict(nat3))
