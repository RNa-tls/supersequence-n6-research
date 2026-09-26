#!/usr/bin/env python3
"""Round 174 -- unmarked single-trail capacity M_n(g), for ANY n, in exactly the row
model of jlebar/superperm7-ge-5898 (Superperm7/Rows.lean, RowModel.lean):

  Row      = (start p, length l in 1..n-1); states F^i p (i < l), F = rotate the first
             n-1 symbols left (our tau).  block = F-orbit of p.  classMask = hexagons
             (sigma-classes) of the states.  charge = (n-1) - l.
  beta(x)  = (Rinv lastState)[3:],  Rinv(s) = s[-1] + s[:-1]   (the weight-3 exit)
  alpha(q) = q[:n-3]
  Trail    = rows with beta(x_i) = alpha(x_{i+1}.start), pairwise distinct blocks and
             pairwise disjoint classMasks.
  M_n(g)   = max number of rows of a trail with total charge <= g.

WLOG (simultaneous relabelling) the first row starts at the identity.  Suffix-cap
pruning as in the external repo: a suffix of a trail is a trail (after relabelling),
so rows_after <= M_n(remaining charge) for already-computed values.
Small falsification tool only (no certificate).  usage: trailcap174.py n gmax [cap]"""
import sys, time, json
from itertools import permutations

sys.setrecursionlimit(10000)


def main(n, gmax, node_cap):
    alph = "".join(str(i + 1) for i in range(n))

    def F(s):
        return s[1:n - 1] + s[0] + s[n - 1]

    def hexrep(s):
        return min(s[i:] + s[:i] for i in range(n))

    rows_by_start = {}
    blockrep = {}
    for p in ("".join(t) for t in permutations(alph)):
        st = [p]
        for _ in range(n - 2):
            st.append(F(st[-1]))
        blockrep[p] = min(st)
        lst = []
        for l in range(1, n):
            last = st[l - 1]
            x = last[-1] + last[:-1]
            lst.append((l, x[3:], frozenset(hexrep(s) for s in st[:l])))
        rows_by_start[p] = lst
    M = {}
    stats = {}
    for g in range(gmax + 1):
        best = [0]
        nodes = [0]
        target = [M.get(g - 1, 0) + 1]

        def rec(beta, rows, charge, used_blocks, used_hex):
            nodes[0] += 1
            if nodes[0] > node_cap:
                raise TimeoutError
            for q in ("".join(t) for t in permutations([c for c in alph if c not in beta])):
                p = beta + q
                b = blockrep[p]
                if b in used_blocks:
                    continue
                for l, nb, hs in rows_by_start[p]:
                    c = charge + (n - 1 - l)
                    if c > g or (hs & used_hex):
                        continue
                    r = rows + 1
                    if r > best[0]:
                        best[0] = r
                        if best[0] >= target[0]:
                            return True
                    # suffix cap: rows after this one <= M(g - c) (the suffix starting
                    # at the NEXT row is a trail with charge <= g - c)
                    if r + M.get(g - c, 10 ** 9) < target[0]:
                        continue
                    used_blocks.add(b)
                    ok = rec(nb, r, c, used_blocks, used_hex | hs)
                    used_blocks.discard(b)
                    if ok:
                        return True
            return False

        t0 = time.time()
        # first row: start = identity, any length
        val = M.get(g - 1, 0)
        status = "EXACT"
        try:
            while True:
                target[0] = val + 1
                found = False
                for l, nb, hs in rows_by_start[alph]:
                    c = n - 1 - l
                    if c > g:
                        continue
                    if 1 >= target[0]:
                        found = True
                        break
                    if 1 + M.get(g - c, 10 ** 9) < target[0]:
                        continue
                    if rec(nb, 1, c, {blockrep[alph]}, set(hs)):
                        found = True
                        break
                if not found:
                    break
                val = target[0]
        except TimeoutError:
            status = "NODE_CAP"
        M[g] = val
        stats[g] = dict(M=val, status=status, nodes=nodes[0], seconds=round(time.time() - t0, 1))
        print(n, g, stats[g], flush=True)
        if status != "EXACT":
            break
    return M, stats


if __name__ == "__main__":
    n, gmax = int(sys.argv[1]), int(sys.argv[2])
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 5 * 10 ** 7
    M, stats = main(n, gmax, cap)
    out = sys.argv[4] if len(sys.argv) > 4 else None
    if out:
        json.dump(dict(n=n, M=M, stats=stats), open(out, "w"), indent=1)
