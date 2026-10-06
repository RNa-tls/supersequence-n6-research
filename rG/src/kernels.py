#!/usr/bin/env python3
"""Final attack, upper thread -- single-special kernels (trails of rows without omissions, all of
special s).  For a single special the successor start is determined by (start, length): the next start
is beta(row) + (y2, y1, s) where y = last state (R182 analysis); disjointness = distinct cyclic words
(Lemma U).  Score v = sum (l_i - (n-2)).  DFS over length sequences; record best score per residue
mod (n-2); keep kernels whose score is a positive multiple of n-2 above n-2 (useful for completion)."""
import sys, os, random, itertools, json

def canon(w): return min(tuple(w[i:] + w[:i]) for i in range(len(w)))

def next_start(p, l, n):
    W = p[:n - 1]; s = p[n - 1]
    st = W[l - 1:] + W[:l - 1]             # last state F^{l-1}p word part (rotation starting at W[l-1])
    y1, y2 = st[0], st[1]
    beta = st[2:]                            # y3..y_{n-1}
    return tuple(beta) + (y2, y1, s)

def search(n, maxrows, nodes, seed, lengths):
    rng = random.Random(seed)
    p0 = tuple(range(n))
    best = {}
    path = []; words = set(); cnt = [0]
    def dfs(p, score):
        cnt[0] += 1
        if cnt[0] > nodes: return
        if path:
            r = score % (n - 2)
            if score > best.get(r, (-10**9,))[0]: best[r] = (score, list(path))
        if len(path) >= maxrows: return
        ls = list(lengths); rng.shuffle(ls); ls.sort(key=lambda l: -l)   # prefer long rows
        for l in ls:
            w = canon(p[:n - 1])
            if w in words: return
            words.add(w); path.append(l)
            dfs(next_start(p, l, n), score + l - (n - 2))
            path.pop(); words.discard(w)
            if cnt[0] > nodes: return
    sys.setrecursionlimit(100000)
    dfs(p0, 0)
    return best

if __name__ == "__main__":
    out = {}
    for n, mr, nodes in ((6, 60, 2 * 10**6), (7, 60, 2 * 10**6), (8, 80, 3 * 10**6)):
        allbest = {}
        for sd in range(3):
            b = search(n, mr, nodes, sd, lengths=range(n - 3, n))     # full, charge-1, charge-2 rows
            for r, (sc, pth) in b.items():
                if sc > allbest.get(r, (-10**9,))[0]: allbest[r] = (sc, pth)
        mult = {r: v for r, v in allbest.items() if r == 0}
        line = f"n={n}: best single-special kernel score overall {max(v[0] for v in allbest.values())}; best multiple of n-2: {mult.get(0, (None,))[0]}"
        print(line, "kernel:", "".join(str(l) for l in mult.get(0, (0, []))[1]), flush=True)
        out[n] = {str(r): v for r, v in allbest.items()}
    json.dump(out, open(os.path.join(HERE := os.path.dirname(os.path.abspath(__file__)), "..", "certs", "kernels.json"), "w"))
