#!/usr/bin/env python3
"""Per-arrangement grid view of a 46188 bundle.  For a class in P({a,b},C) with C = (c_0..c_{m-1})
(canonical rotation, m = n-2), record (slot of a in C, slot of b in C, order if same slot).  For each C
of long trail 0 list its chains: special, length, the slots covered, and the trail position."""
import sys, os, json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
A, B = 0, n - 1
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
F = tuple(list(range(1, n - 1)) + [0, n - 1])
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def coords(p):
    """cyclic word p -> (C, slot_a, slot_b, order) ; slot j = gap before C[j] in C."""
    k = p.index(A); w_ = list(p[k:] + p[:k])            # starts with a
    C = cyc_canon([x for x in w_ if x not in (A, B)])
    m = len(C)
    # walk the cyclic word from the element after a; find which C-element follows a and b
    def slot_of(sym):
        k2 = w_.index(sym); j = (k2 + 1) % len(w_)
        while w_[j] in (A, B): j = (j + 1) % len(w_)
        return C.index(w_[j])
    sa, sb = slot_of(A), slot_of(B)
    order = None
    if sa == sb:
        ia, ib = w_.index(A), w_.index(B)
        order = "ab" if (ib - ia) % len(w_) == 1 else "ba"
    return C, sa, sb, order
t = [t for t in trails if len(t) == 104][0]
grid = defaultdict(list)
for pos, ch in enumerate(t):
    s = S[ch[0]]; l = len(ch); x = s; cells = []
    for _ in range(l): cells.append(coords(x)); x = comp(x, F)
    C = cells[0][0]
    assert all(c[0] == C for c in cells)
    sp = "a" if s[n - 1] == A else "b"
    fixed = cells[0][2] if sp == "a" else cells[0][1]
    run = [c[1] if sp == "a" else c[2] for c in cells]
    grid[C].append(dict(pos=pos, sp=sp, l=l, fixed_slot=fixed, run=run, orders=[c[3] for c in cells]))
Cs = list(grid)
for C in Cs[:3]:
    print("C =", C)
    for e in sorted(grid[C], key=lambda e: (e["sp"], e["fixed_slot"])):
        print(f"   pos {e['pos']:3d} {e['sp']}{e['l']} fixed {'b' if e['sp']=='a' else 'a'}-slot {e['fixed_slot']} run {e['run']} {e['orders']}")
