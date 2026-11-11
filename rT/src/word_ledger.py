#!/usr/bin/env python3
"""Round T -- one ledger for both families: any word whose runs are the runs of a family of closed trails.
  L = 35288 + sum of link weights between consecutive runs          (run = 8 windows of a class)
  natural sum N = sum of natural link weights of the closed trails = 10080 + 720 + Q
  L = 46085 + Q + J,   J = sum over cuts (3 - c) + sum over joins (w - 3) + 3 * (pieces - trails) ... see below
With P pieces (P cuts, P - 1 joins):  L = 35288 + N - sum c(cut) + sum w(join)
                                        = 46085 + Q + [ sum_cuts (3 - c) + sum_joins (w - 3) ]      (exact for every P)
usage: word_ledger.py WORD.txt (old FAMILY.json | new SEL TSV BASE) OUT.json"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model, slice_structure as SS
N = 8
def positions(w):
    """for every permutation p: the positions i with w[i:i+8] = p and windows i .. i+7 all permutations"""
    ok = [model.isperm(w[i:i + N]) for i in range(len(w) - N + 1)]; run = [0] * (len(ok) + 1)
    for i in range(len(ok) - 1, -1, -1): run[i] = run[i + 1] + 1 if ok[i] else 0
    pos = {}
    for i in range(len(ok)):
        if run[i] >= N: pos.setdefault(w[i:i + N], []).append(i)
    return pos
if __name__ == "__main__":
    a = sys.argv[1:]; w = "".join(ch for ch in open(a[0]).read() if not ch.isspace()); al = sorted(set(w)); w = "".join(str(al.index(ch)) for ch in w); outp = a[-1]
    if a[1] == "old":
        fam = json.load(open(a[2])); cyc = {(t["trail"], v): SS.expand(x) for t in fam["trails"] for v, x in enumerate(t["versions"])}
    else:
        cyc = {(t, 0): c for t, c in enumerate(model.load(*a[2:5]))}
    pos = positions(w)
    used = {}; nat = {}; where = {}; Nsum = 0; w3 = 0; at = {}
    for (t, v), c in sorted(cyc.items()):
        rs = model.runs_of(c); d = c + c; ent = [d[r[0]:r[0] + N] for r in rs]
        if all(len(pos.get(e, [])) == 1 for e in ent):
            assert t not in used; used[t] = v
            for i, r in enumerate(rs): nat[(ent[i], ent[(i + 1) % len(rs)])] = r[2]; where[ent[i]] = (t, i); at[ent[i]] = pos[ent[i]][0]; Nsum += r[2]; w3 += r[2] == 3
    assert len(used) == len({t for t, _ in cyc}) and len(where) == 5040, (len(used), len(where))
    first = sorted(at, key=at.get); runs = [at[x] for x in first]
    assert runs[0] <= 1 and all(j - i >= N for i, j in zip(runs, runs[1:]))
    Q = w3 - 720
    links = []
    for x, y, i, j in zip(first, first[1:], runs, runs[1:]): links.append((x, y, j - (i + N - 1)))
    joins = [(x, y, wt) for x, y, wt in links if (x, y) not in nat]; kept = {(x, y) for x, y, wt in links if (x, y) in nat}
    for x, y, wt in links:
        if (x, y) in nat: assert nat[(x, y)] == wt
    cuts = [(k, c) for k, c in nat.items() if k not in kept]
    P = len(cuts); assert P == len(joins) + 1
    J = sum(3 - c for _, c in cuts) + sum(wt - 3 for _, _, wt in joins)
    # visits: maximal stretches of the route inside one trail
    seq = [where[x][0] for x in first]; V = 1 + sum(1 for p, q in zip(seq, seq[1:]) if p != q)
    pieces_per_trail = collections.Counter(where[k[1]][0] for k, _ in cuts)
    res = dict(word=os.path.basename(a[0]), length=len(w), trails=len(used), versions="".join(str(used[t]) for t in sorted(used)), Q=Q, natural_sum=Nsum, pieces_P=P, visits_V=V,
               cuts_by_weight={str(k): v for k, v in sorted(collections.Counter(c for _, c in cuts).items())}, joins_by_weight={str(k): v for k, v in sorted(collections.Counter(wt for _, _, wt in joins).items())},
               opening_cost=sum(3 - c for _, c in cuts), join_cost=sum(wt - 3 for _, _, wt in joins), J=J, length_formula=46085 + Q + J,
               sum_link_weights=sum(wt for _, _, wt in links), length_from_links=35288 + sum(wt for _, _, wt in links) + runs[0] + (len(w) - runs[-1] - 15),
               trails_with_more_than_one_piece={str(t): n for t, n in sorted(pieces_per_trail.items()) if n > 1},
               joins_between_same_trail=sum(1 for x, y, _ in joins if where[x][0] == where[y][0]))
    assert res["length_formula"] == len(w) == res["length_from_links"]
    print(json.dumps(res)); json.dump(res, open(outp, "w"), indent=1)
