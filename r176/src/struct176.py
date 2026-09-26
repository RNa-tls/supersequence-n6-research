#!/usr/bin/env python3
"""Round 176 -- structured falsification search for S1 (uses Lemma R176-1, proved in the
report: a charge-<=2 ModelTrail with >= n rows is R x R' with ONE charge-2 row x and
R, R' runs of unmarked full rows).

x ranges over all charge-2 row types at start = identity (WLOG by relabelling):
  T      length n-3, no omission
  L_i    length n-2, omitted {i}, 1 <= i <= n-4
  M_ij   length n-1, omitted {i, j}, 1 <= i < j <= n-3
R  = full rows r_{a-1}, ..., r_1, r_0 before x (r_0 any of the 6 compatible predecessors,
     r_{t+1} = the unique full row whose successor-compatible start is r_t, i.e.
     phi^{-1}; the full-row successor lemma makes a full-row run a phi-chain),
R' = full rows q_0, phi q_0, ... after x (q_0 any of the 6 compatible successors).
All pairs are checked directly on hexagon sets (no frame logic).  Reports the maximum
a + 1 + b and the configurations attaining it (symbolic labels).
usage: struct176.py n [n ...]"""
import sys
from itertools import permutations, combinations


def run(n):
    def F(s): return s[1:n - 1] + (s[0], s[n - 1])
    def Rinv(s): return (s[n - 1],) + s[:n - 1]
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
    def phi(s): return s[1:n - 2] + (s[0],) + s[n - 2:]
    def phiinv(s): return (s[n - 3],) + s[:n - 3] + s[n - 2:]

    def row(p, l, om=()):
        st = [p]
        for _ in range(n - 2):
            st.append(F(st[-1]))
        return dict(p=p, block=min(st), beta=Rinv(st[l - 1])[3:],
                    vis=frozenset(hexrep(st[i]) for i in range(l) if i not in om))
    p = tuple(range(n))
    xs = [("T", row(p, n - 3))]
    xs += [("L%d" % i, row(p, n - 2, (i,))) for i in range(1, n - 3)]
    xs += [("M%d,%d" % (i, j), row(p, n - 1, (i, j))) for i, j in combinations(range(1, n - 2), 2)]

    def ok_pair(r1, r2):
        return r1["block"] != r2["block"] and not (r1["vis"] & r2["vis"])
    best, where = 0, []
    per = {}                         # (type class, entry label, exit label) -> max rows
    c = {i + 1: p[i] for i in range(n)}
    def tclass(name):
        if name == "T": return "T"
        if name[0] == "L": return "L_i"
        i, j = map(int, name[1:].split(","))
        return "M_%s,%s" % ("1" if i == 1 else "i", "n-3" if j == n - 3 else "j")
    def lab_pred(r):   # predecessor r = u + alpha + (y z): name the tail of x.start in r's letters
        if r is None: return "-"
        u, y, z = r["p"][0], r["p"][n - 2], r["p"][n - 1]
        nm = {u: "u", y: "y", z: "z"}
        return "B+" + "".join(nm[t] for t in p[n - 3:])
    def lab_succ(x, q):
        if q is None: return "-"
        rest = q["p"][n - 3:]
        return "tail:" + ",".join("c%d" % (p.index(t) + 1) for t in rest)
    for name, x in xs:
        alpha = p[:n - 3]
        # predecessors: full rows r with beta(r) = alpha(x.start): r = u + alpha + y z
        rest = [c for c in range(n) if c not in alpha]
        preds = [row((t[0],) + alpha + t[1:], n - 1) for t in permutations(rest)]
        preds = [r for r in preds if r["beta"] == alpha and ok_pair(r, x)]
        rest2 = [c for c in range(n) if c not in x["beta"]]
        succs = [row(x["beta"] + t, n - 1) for t in permutations(rest2)]
        succs = [q for q in succs if ok_pair(x, q)]
        for r0 in [None] + preds:
            R = []
            if r0 is not None:
                R = [r0]
                while len(R) < n - 2:
                    nxt = row(phiinv(R[-1]["p"]), n - 1)
                    if nxt["beta"] != R[-1]["p"][:n - 3]: raise AssertionError("phi^-1")
                    if not ok_pair(nxt, x) or not all(ok_pair(nxt, y) for y in R): break
                    R.append(nxt)
            for q0 in [None] + succs:
                Rp = []
                if q0 is not None:
                    Rp = [q0]
                    while len(Rp) < n - 2:
                        nxt = row(phi(Rp[-1]["p"]), n - 1)
                        if not ok_pair(nxt, x) or not all(ok_pair(nxt, y) for y in Rp): break
                        Rp.append(nxt)
                # the longest mutually compatible prefix combination: R uses its first a rows
                # (closest to x), R' its first b rows
                for a in range(len(R) + 1):
                    for b in range(len(Rp) + 1):
                        if all(ok_pair(u, v) for u in R[:a] for v in Rp[:b]):
                            tot = a + 1 + b
                            key = (tclass(name), lab_pred(r0), lab_succ(x, q0))
                            per[key] = max(per.get(key, 0), tot)
                            lab = (name, "pred:" + ("-" if r0 is None else "".join(map(str, r0["p"]))),
                                   "succ:" + ("-" if q0 is None else "".join(map(str, q0["p"]))), a, b)
                            if tot > best: best, where = tot, [lab]
                            elif tot == best: where.append(lab)
    return best, where, per


if __name__ == "__main__":
    for n in [int(a) for a in sys.argv[1:] if not a.startswith('-')]:
        best, where, per = run(n)
        types = sorted({w[0][0] for w in where})
        print(f"n={n}: max rows with one charge-2 row = {best} (2n-5 = {2*n-5}); "
              f"attained by x types {types}; {len(where)} configurations; e.g. {where[:4]}")
        if "--per" in sys.argv[1:] or True:
            agg = {}
            for (tc, e, x), v in per.items():
                agg.setdefault(tc, 0); agg[tc] = max(agg[tc], v)
            print("   per type max:", {k: (v, "n-2" if v == n - 2 else "2n-5" if v == 2*n-5 else v) for k, v in sorted(agg.items())})
            print("   T per (entry, exit):", sorted(((e, x), v - (n - 2)) for (tc, e, x), v in per.items() if tc == "T"))
