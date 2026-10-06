#!/usr/bin/env python3
"""Final attack -- shortest single-special kernels with an exact target score (iterative deepening on
the number of rows), n given.  Row lengths in {n-3, n-2, n-1} (charge 2, 1, 0).  Distinct words."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernels import next_start, canon

def find(n, target, maxlen, want=5):
    out = []
    for L in range(1, maxlen + 1):
        path = []; words = set()
        def dfs(p, score):
            if len(out) >= want: return
            rem = L - len(path)
            if rem == 0:
                if score == target: out.append(list(path))
                return
            if score + rem < target: return              # max gain +1 per row
            w = canon(p[:n - 1])
            if w in words: return
            for l in (n - 1, n - 3, n - 2):
                words.add(w); path.append(l)
                dfs(next_start(p, l, n), score + l - (n - 2))
                path.pop(); words.discard(w)
                if len(out) >= want: return
        dfs(tuple(range(n)), 0)
        if out: return L, out
    return None, []

if __name__ == "__main__":
    n = int(sys.argv[1])
    for t in [int(a) for a in sys.argv[2:]]:
        L, ks = find(n, t, 80)
        print(f"n={n} score {t}: shortest length {L}:", ["".join(map(str, k)) for k in ks[:3]], flush=True)
