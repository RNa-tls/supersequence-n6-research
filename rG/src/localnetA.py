#!/usr/bin/env python3
"""Final attack -- exact LOCAL net saving of one non-full row (no omissions) between two full-row
segments:  [full^a, y, full^b].  Full rows inside a segment are forced (C0: successor = phi), so the
segment before y is phi^{-(a-1)}x .. x and after y is z .. phi^{b-1}z.  Exhaustive over y (start =
identity WLOG), over its length, over the predecessor x and successor z.  Net local saving charged
to y when both segments are exclusively its own:  vis(y) - [(n-2-a) + (n-2-b)].
Checker B for compatibility/disjointness."""
import sys, os
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA as CheckerB

def run(n):
    B = CheckerB(n)
    phi = lambda p: p[1:n - 2] + (p[0],) + p[n - 2:]
    phiinv = lambda p: (p[n - 3],) + p[:n - 3] + p[n - 2:]
    out = {}
    for l in range(1, n - 1):                     # non-full lengths
        y = (tuple(range(n)), l, ())
        best = None
        # predecessors x (full) with beta(x) = y[:n-3]
        pre = []
        for sig in permutations([t for t in range(n) if t not in y[0][1 - 1:0] ]):
            pass
        cands_x = []
        for p in permutations(range(n)):
            x = (p, n - 1, ())
            if B.compatible(x, y) and B.disjoint(x, y): cands_x.append(x)
        beta = B.beta(y); rest = [t for t in range(n) if t not in beta]
        cands_z = [(beta + s, n - 1, ()) for s in permutations(rest)]
        cands_z = [z for z in cands_z if B.disjoint(y, z)]
        for x in cands_x:
            seg_a = [x]
            while len(seg_a) < n - 2:
                w = (phiinv(seg_a[0][0]), n - 1, ())
                if all(B.disjoint(w, r) for r in seg_a + [y]): seg_a.insert(0, w)
                else: break
            for z in cands_z:
                if not all(B.disjoint(z, r) for r in seg_a): continue
                seg_b = [z]
                while len(seg_b) < n - 2:
                    w = (phi(seg_b[-1][0]), n - 1, ())
                    if all(B.disjoint(w, r) for r in seg_a + [y] + seg_b): seg_b.append(w)
                    else: break
                # longest a compatible with this b (seg_a already maximal before z; recheck jointly)
                a, b = len(seg_a), len(seg_b)
                net = l - ((n - 2 - a) + (n - 2 - b))
                if best is None or net > best[0]: best = (net, a, b)
        out[n - 1 - l] = best
    return out

if __name__ == "__main__":
    lines = []
    for n in (6, 7):
        o = run(n)
        line = f"n={n}: charge -> (max local net, a, b): " + ", ".join(f"c={c}:{v}" for c, v in sorted(o.items()))
        print(line, flush=True); lines.append(line)
    open(os.path.join(os.path.dirname(__file__), "..", "certs", "localnetA.txt"), "w").write("\n".join(lines) + "\n")
