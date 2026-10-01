#!/usr/bin/env python3
"""Final round -- Egan-length words (D = (n-3)!, k = 1, u = 1): locate the unique hole, its block Bh,
check whether every selected class of Bh has multiplicity 2, count components after deleting Bh, and
test whether some phi-frame (n-2 blocks (W, s) with W minus Y = F) has one block in each component."""
import sys, os, math
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "rF/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word
from run178 import words

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))

def study(route, n):
    N = len(route); R = lambda x: x[1:] + x[:1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    S = {route[0]} | {route[i + 1] for i in range(N - 1) if route[i + 1] != R(route[i])}
    blk = lambda x: (canon(x[:n - 1]), x[n - 1])
    states = lambda b: None
    blocks = defaultdict(set)
    for s in S: blocks[blk(s)].add(s)
    holes = []
    for b, sel in blocks.items():
        x = next(iter(sel))
        for _ in range(n - 1):
            if x not in S: holes.append((b, x))
            x = F(x)
    out = dict(M=len(blocks), holes=len(holes))
    if len(holes) != 1: return out
    Bh, hx = holes[0]
    mult = Counter(canon(s) for s in S)
    sel_classes = [canon(s) for s in blocks[Bh]]
    out["Bh_selected_all_mult2"] = all(mult[c] == 2 for c in sel_classes)
    # components after deleting Bh
    par = {b: b for b in blocks if b != Bh}
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    bycls = defaultdict(list)
    for s in S:
        if blk(s) != Bh: bycls[canon(s)].append(blk(s))
    for c, bl in bycls.items():
        for b in bl[1:]: par[find(b)] = find(bl[0])
    comps = Counter(find(b) for b in par)
    out["components_after"] = len(comps); out["sizes"] = sorted(comps.values())
    compof = {b: find(b) for b in par}
    # phi-frames with all n-2 blocks present and in pairwise distinct components
    frames = defaultdict(list)
    for (W, s) in par:
        for Y in W:
            Fw = [t for t in W if t != Y]
            frames[(canon(tuple(Fw)), Y, s)].append((W, s))
    good = [k for k, v in frames.items() if len(v) == n - 2 and len({compof[b] for b in v}) == n - 2]
    out["rooting_frames"] = len(good)
    out["Bh_special"] = Bh[1]
    return out

if __name__ == "__main__":
    for n in (7, 8, 9):
        ws = words(n, 200)
        f1 = sum(math.factorial(n - i) for i in range(4)) + n - 3
        eg = [w for w in ws if len(w) == f1]
        if not eg: print(n, "no Egan-length word in archive"); continue
        w = eg[0]; mp = {c: i for i, c in enumerate(sorted(set(w)))}
        route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
        print(n, len(w), study(route, n), flush=True)
