#!/usr/bin/env python3
"""Round 180 -- special-c_n walks: trails in which every row has the same special symbol
c_n and each row is either full (length n-1) or a short row T (length n-3, charge 2).

State = row start p = w_1 .. w_{n-2} a c_n.  Next start after a full row = phi(p); after a
T row = the exit D+wvz (r176): q0 = a w_1..w_{n-4} w_{n-2} w_{n-3} c_n.  All rows share the
special c_n, so (Lemma U) the trail is a ModelTrail iff all cyclic words W(p) are distinct.
For each number J of T rows we compute the maximum number of rows (exact DFS for small n)
and re-verify the best walk with the direct checker A.
usage: walk180.py n Jmax"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
sys.setrecursionlimit(100000)
n, Jmax = int(sys.argv[1]), int(sys.argv[2])
def phi(s): return s[1:n - 2] + (s[0],) + s[n - 2:]
def tmove(s): return (s[n - 2],) + s[:n - 4] + (s[n - 3], s[n - 4], s[n - 1])
def W(s):
    w = s[:n - 1]; return min(w[i:] + w[:i] for i in range(n - 1))
best = {}
bestwalk = {}
def dfs(s, used, rows, J, path):
    if rows > best.get(J, 0):
        best[J] = rows; bestwalk[J] = list(path)
    for kind, nxt in (("F", phi(s)), ("T", tmove(s))):
        J2 = J + (kind == "T")
        if J2 > Jmax: continue
        w = W(nxt)
        if w in used: continue
        path[-1] = (path[-1][0], kind)
        used.add(w); path.append((nxt, None))
        dfs(nxt, used, rows + 1, J2, path)
        path.pop(); used.discard(w)
    path[-1] = (path[-1][0], None)
p0 = tuple(range(n))
# the first row may itself be T or F: the row type of a state is decided when we leave it;
# the last row's type is free (choose F: charge 0)
dfs(p0, {W(p0)}, 1, 0, [(p0, None)])
A = CheckerA(n)
for J in sorted(best):
    rows = [(s, n - 1 if k in (None, "F") else n - 3, ()) for s, k in bestwalk[J]]
    ok = A.trail(rows)
    ch = sum(A.charge(x) for x in rows)
    print(f"n={n} J={J} (charge {2*J}): max rows {best[J]}   C1 bound {(n-2)+(n-3)*J}   checker A {ok[0]} (charge {ch})")
