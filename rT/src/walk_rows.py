#!/usr/bin/env python3
"""Round T -- read the closed walk of rows out of a closed trail.
A class (cyclic order of 8 letters) belongs to the loop obtained by deleting the two special letters {s, z}.
For each trail: the cyclic sequence of loops it passes (consecutive runs of one loop merged), the number of slices
(maximal weight-2 chains) per loop, v(loop) = 12 - slices, and the row word = v along the first pass of the walk.
usage: walk_rows.py old FAMILY.json OUT.json | new SEL TSV BASE OUT.json"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model, slice_structure as SS
def loop_of(cls, sz):
    x = "".join(ch for ch in cls if ch not in sz); m = min(x); i = x.index(m); return x[i:] + x[:i]
def analyse(c, sz):
    rs = model.runs_of(c); i0 = next(i for i in range(len(rs)) if rs[i - 1][2] == 3); rs = rs[i0:] + rs[:i0]
    loops = [loop_of(r[1], sz) for r in rs]; nsl = collections.Counter(); cnt = collections.Counter(loops)
    for r, lp in zip(rs, loops):
        if r[2] == 3: nsl[lp] += 1
    seq = [lp for i, lp in enumerate(loops) if lp != loops[i - 1]] or [loops[0]]
    v = {lp: 12 - nsl[lp] for lp in cnt}
    # period of the loop sequence = the walk
    m = next(p for p in range(1, len(seq) + 1) if len(seq) % p == 0 and seq == seq[p:] + seq[:p])
    walk = seq[:m]
    return dict(R=len(c), runs=len(rs), loops=len(cnt), classes_per_loop=sorted(set(cnt.values())), passes=len(seq) // m if m else 0, walk_len=m,
                walk_is_simple=len(set(walk)) == len(walk), row_word="".join(str(v[lp]) for lp in walk), Q=sum(6 - v[lp] for lp in cnt if v[lp] > 0), walk=walk)
def canon_word(s): return min(s[i:] + s[:i] for i in range(len(s)))
if __name__ == "__main__":
    if sys.argv[1] == "old":
        fam = json.load(open(sys.argv[2])); outp = sys.argv[3]; res = []
        for t in fam["trails"]:
            for ver, w in enumerate(t["versions"]):
                c = SS.expand(w); a = analyse(c, "07"); a.update(trail=t["trail"], version=ver); res.append(a)
    else:
        outp = sys.argv[5]; res = []
        for t, c in enumerate(model.load(*sys.argv[2:5])): a = analyse(c, "67"); a.update(trail=t, version=0); res.append(a)
    types = collections.Counter((a["version"], a["R"], a["loops"], a["passes"], canon_word(a["row_word"]), a["Q"]) for a in res)
    for k, n in sorted(types.items()): print(n, "x", k)
    cover = collections.Counter()
    for a in res:
        if a["version"] == 0: cover.update(a["walk"] if a["loops"] > 1 else [a["walk"][0]] if a["walk"] else [])
    print("loops covered (version 0):", len(cover), "max multiplicity", max(cover.values()))
    json.dump(res, open(outp, "w"), indent=1)
