#!/usr/bin/env python3
"""Round 175 -- witness table for Lemma 2 (transition table T): for a length-(n-1)
start p = u B y z and a loop start p = A x y z, list, for each of the six compatible
candidate starts q, every hexagon shared by the FULL position ranges of the two
blocks' rows, as (position in p-row, position in q-row).  Position i = state F^i
(the special symbol sits right after w_i, w_0 := w_{n-1}).  A row of type full sees
0..n-2, loop 0..n-3, mark_j sees 0..n-2 minus j.  Printed symbolically; uniform in n
(checked for the n given)."""
import sys
from itertools import permutations
def run(n):
    def F(s): return s[1:n-1] + (s[0], s[n-1])
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
    def pos(p):
        st=[p]
        for _ in range(n-2): st.append(F(st[-1]))
        return {hexrep(s): i for i, s in enumerate(st)}, min(st)
    p = tuple(range(n)); P, bp = pos(p)
    res = {}
    for kind, beta, names in (("long", p[1:n-2], {p[0]:'u', p[n-2]:'y', p[n-1]:'z'}),
                              ("loop", p[:n-3], {p[n-3]:'x', p[n-2]:'y', p[n-1]:'z'})):
        for tail in permutations(sorted(names)):
            q = beta + tail; Q, bq = pos(q)
            lab = ("B" if kind == "long" else "A") + "+" + "".join(names[t] for t in tail)
            if bq == bp: res[(kind, lab)] = "same block"; continue
            def sym(i): return {0:'0', n-2:'n-2', n-3:'n-3', 1:'1'}.get(i, str(i))
            res[(kind, lab)] = sorted((sym(P[h]), sym(Q[h])) for h in set(P) & set(Q))
    return res
ref = None
for n in map(int, sys.argv[1:] or [6, 7, 8, 9]):
    r = run(n)
    if ref is None: ref = r
    print(n, "same as first n:", r == ref)
for k, v in ref.items(): print(k, v)

# ---- Lemma 7 witnesses: second loops next to a long block (k >= 1) ----------------
def lemma7(n):
    def F(s): return s[1:n-1] + (s[0], s[n-1])
    def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
    def pos(p):
        st=[p]
        for _ in range(n-2): st.append(F(st[-1]))
        return {hexrep(s): i for i, s in enumerate(st)}, min(st)
    def sym(i): return {0:'0', n-2:'n-2', n-3:'n-3', 1:'1'}.get(i, str(i))
    A = tuple(range(n-3)); x, y, z = n-3, n-2, n-1
    cases = {
      # leading cluster: lambda = A x y z (last loop), p_first by swap / 3-cycle route
      "lead swap: lambda'=Ayxz vs p_first=Ayxz": (A+(y,x,z), A+(y,x,z)),
      "lead 3cyc: lambda'=Ayxz vs p_first=Ayzx": (A+(y,x,z), A+(y,z,x)),
      "lead swap: lambda'=Axzy (X) vs p_first=Ayxz": (A+(x,z,y), A+(y,x,z)),
      "lead 3cyc: lambda'=Axzy (X) vs p_first=Ayzx": (A+(x,z,y), A+(y,z,x)),
      # trailing cluster: mu1 = A x y z (first loop), p_last = x A y z (phi) or x A z y (psi)
      "trail phi: mu2=Ayxz (Y) vs p_last=xAyz": (A+(y,x,z), (x,)+A+(y,z)),
      "trail psi: mu2=Ayxz (Y) vs p_last=xAzy": (A+(y,x,z), (x,)+A+(z,y)),
      "trail phi: mu2=Azyx (Z) vs p_last=xAyz": (A+(z,y,x), (x,)+A+(y,z)),
      "trail psi: mu2=Azyx (Z) vs p_last=xAzy": (A+(z,y,x), (x,)+A+(z,y)),
    }
    out = {}
    for name, (lp, longp) in cases.items():
        L, bl = pos(lp); P, bp = pos(longp)
        if bl == bp: out[name] = "same block"; continue
        out[name] = sorted((sym(L[h]), sym(P[h])) for h in set(L) & set(P))
    return out
ref7 = None
for n in map(int, sys.argv[1:] or [6, 7, 8, 9]):
    r = lemma7(n)
    if ref7 is None: ref7 = r
    print(n, "Lemma 7 table same as first n:", r == ref7)
for k, v in ref7.items(): print("  ", k, "(loop pos, long pos):", v)
