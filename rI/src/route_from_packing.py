#!/usr/bin/env python3
"""Packing certificate -> superpermutation.  Each chosen trail (word, g) is the closed trail
g * shape(word); its chains (start, end-of-run, l) are listed cyclically, then relink.solve picks one
opening per trail and an order minimizing sum (c - 3) over the inter-trail joins (exact CP-SAT,
arcs of cost <= MAXC), relink.build_word concatenates, and the word is written for independent
verification (r0verifyA / r0verifyB)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packing import setup, closed_letters, comp
from relink import solve, build_word
cert, maxc, tl = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
d = json.load(open(cert)); n = d["n"]
I, Fp, T, syl = setup(n)
Rinv = lambda s: s[-1:] + s[:-1]
cycles = []
for tr in d["trails"]:
    g = tuple(tr["g"]); letters = closed_letters(n, tr["word"], I, Fp, T, syl)
    P = I; cy = []
    for l, s in letters:
        st = comp(g, P); last = comp(st, Fp[l - 1])
        cy.append((st, Rinv(last), l))
        P = comp(P, comp(Fp[l - 1], T[s]))
    cycles.append(cy)
st, obj, bd, order, nodes, na, sec = solve(cycles, n, maxc, tl, workers=3)
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
q = sum(len(c) for c in cycles)
print(json.dumps(dict(status=st, link_objective=obj, link_bound=bd, q=q, trails=len(cycles),
                      predicted_length=None if obj is None else CONST - ORB + q + int(obj), sec=sec)), flush=True)
if order:
    word = build_word(cycles, nodes, order, n)
    outp = os.path.join(os.path.dirname(os.path.abspath(cert)), f"word_n{n}_{len(word)}.txt")
    open(outp, "w").write("".join(str(c + 1) for c in word) + "\n")
    print("wrote", outp, "length", len(word))
