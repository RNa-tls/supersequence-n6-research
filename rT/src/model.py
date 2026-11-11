#!/usr/bin/env python3
"""Round T -- the public 16-trail selection in this project's run language.
A trail's cyclic word is cut into class visits (runs): a run = 8 consecutive permutation windows of one cyclic
class (7 weight-1 steps).  Natural link = step from the last permutation of a run to the first of the next run
(weight 2 or 3; a weight-3 link may pass through one more permutation window, a repeat of the run's first one)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_from_selection import read_sel, trails, canon
N = 8
def isperm(s): return len(set(s)) == N
def load(selp, tsvp, basep):
    """cyclic words in the numbering and rotation of BASE.tsv / BASE.txt, checked against my own reconstruction"""
    tr = trails(read_sel(selp)); mine = {canon(c) for c, _ in tr}
    tab = [l.split("\t") for l in open(tsvp)]; base = open(basep).read().strip(); out = []
    for t in tab:
        c = base[int(t[3]):int(t[3]) + int(t[2])]; assert canon(c) in mine; out.append(c)
    assert len(out) == len(mine) == len(set(canon(c) for c in out))
    return out
def runs_of(c):
    """list of (offset of first window, class, natural link weight to the next run, dup flag)"""
    R = len(c); d = c + c[:N]; ok = [isperm(d[i:i + N]) for i in range(R)]
    def cls(s):
        i = s.index("0"); return s[i:] + s[:i]
    # a run starts at a perm window whose predecessor window is not a perm, or which is a repeat (9th window)
    starts = []
    i0 = next(i for i in range(R) if ok[i] and not ok[i - 1])
    i = i0
    while True:
        starts.append(i); j = (i + N) % R              # 8 windows i..i+7; window i+8 is a repeat if it is a perm
        dup = ok[j]
        if dup: assert d[j:j + N] == d[i:i + N] if j + N <= len(d) and i + N <= len(d) else True
        k = (j + 1) % R if dup else j
        w = 0
        while not ok[k]: k = (k + 1) % R; w += 1
        # weight of the link in run language: letters between last window of the run and first of the next
        wt = ((k - (i + N - 1)) % R)
        starts[-1] = (i, cls(d[i:i + N]), wt, dup)
        i = k
        if i == i0: break
    return starts
if __name__ == "__main__":
    selp, tsvp, basep, outp = sys.argv[1:5]
    cyc = load(selp, tsvp, basep); out = []; allc = set(); tot = {}
    for t, c in enumerate(cyc):
        rs = runs_of(c); allc |= {r[1] for r in rs}
        h = {}
        for r in rs: h[(r[2], r[3])] = h.get((r[2], r[3]), 0) + 1
        for k, v in h.items(): tot[k] = tot.get(k, 0) + v
        out.append(dict(trail=t, R=len(c), runs=len(rs), links={"w%d%s" % (k[0], "dup" if k[1] else ""): v for k, v in sorted(h.items())}))
        print(out[-1])
    print("classes", len(allc), "links", tot, "sum natural", sum(k[0] * v for k, v in tot.items()))
    json.dump(dict(trails=out, classes=len(allc), sum_natural_link_weights=sum(k[0] * v for k, v in tot.items())), open(outp, "w"), indent=1)
