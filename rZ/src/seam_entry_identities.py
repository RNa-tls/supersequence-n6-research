#!/usr/bin/env python3
"""Round Z -- exhaustive check of the seam-entry identities (all 40320 exits y = z v1 v2 y4..y8):
  b (entry y4..y8 v1 z v2): its class is the class that follows the exit class in the exit's 2-cycle (z moves past v1);
  e (entry y4..y8 v1 v2 z): same 2-cycle as the exit, two steps on (one class skipped);
  d (entry y4..y8 v2 v1 z): 2-cycle (z, C') with C' = C with v1, v2 exchanged;  c and f enter the same 2-cycle C' of
  world z two steps and one step before the d entry (as classes; their moving symbols are v1).
Prints the number of exits for which each identity holds (must be 40320)."""
import itertools, collections
def cls(p): k = p.index(1); return p[k:] + p[:k]
def zcyc(X, z):        # the 7 symbols after z in class X, rotated canonically: the z-2-cycle of X
    k = X.index(z); t = X[k + 1:] + X[:k]; m = t.index(min(t)); return t[m:] + t[:m]
def zpos(X, z, C):     # position of z in 2-cycle (z, C): index of z's right neighbour in C
    k = X.index(z); return C.index(X[(k + 1) % 8])
ok = collections.Counter()
for y in itertools.permutations(range(1, 9)):
    z, v1, v2 = y[0], y[1], y[2]; rest = y[3:]
    X = cls(y); C = zcyc(X, z); p0 = zpos(X, z, C)
    eb = rest + (v1, z, v2); ee = rest + (v1, v2, z); ed = rest + (v2, v1, z); ec = rest + (z, v2, v1); ef = rest + (v2, z, v1)
    Xb = cls(eb); ok['b: same 2-cycle'] += zcyc(Xb, z) == C; ok['b: next class'] += zpos(Xb, z, C) == (p0 + 1) % 7
    Xe = cls(ee); ok['e: same 2-cycle'] += zcyc(Xe, z) == C; ok['e: two on'] += zpos(Xe, z, C) == (p0 + 2) % 7
    Xd = cls(ed); Cd = zcyc(Xd, z)
    sw = list(C); i1, i2 = sw.index(v1), sw.index(v2); sw[i1], sw[i2] = v2, v1; sw = tuple(sw); m = sw.index(min(sw)); sw = sw[m:] + sw[:m]
    ok['d: swapped 2-cycle'] += Cd == sw
    pd = zpos(Xd, z, Cd)
    Xc = cls(ec); Xf = cls(ef)
    ok['c: in d-target 2-cycle'] += zcyc(Xc, z) == Cd; ok['c: two before d entry'] += zpos(Xc, z, Cd) == (pd - 2) % 7
    ok['f: in d-target 2-cycle'] += zcyc(Xf, z) == Cd; ok['f: one before d entry'] += zpos(Xf, z, Cd) == (pd - 1) % 7
    ok['moving symbol c,f = v1; b = v2'] += (ec[-1] == v1 and ef[-1] == v1 and eb[-1] == v2)
print(dict(ok))
