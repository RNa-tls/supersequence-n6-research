"""Round K -- core trail algebra for r = 0 routes (n = 8 by default).

A run starting at perm p visits the n rotations of p's cyclic class.  A chain of length l from p
visits the classes of p, pF, ..., pF^(l-1)  (F = rotation of positions 0..n-2, a cost-2 step).
A cost-3 join leaves the chain's last run start x = pF^(l-1) to t = x o T_sigma, with
T_sigma = (2, 3, ..., n-2) + sigma and sigma a permutation of (0, 1, n-1); sigma = (n-1, 0, 1)
gives t = R^2 x (same class, never legal).  Perms are tuples; composition (p o q)[i] = p[q[i]].
S_n acts on the left (relabelling), so the validity of a letter sequence does not depend on the
start perm.  A class is identified by its rotation with 0 in front."""
import itertools
N = 8
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def setup(n=N):
    I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
    Fp = [I]
    for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
    sig = {s: tuple(list(range(2, n - 1)) + list(s)) for s in itertools.permutations((0, 1, n - 1))}
    BAC = (1, 0, n - 1); RR = (n - 1, 0, 1)
    sigmas = [s for s in sig if s != RR]                 # the 5 legal cost-3 transition types
    return I, F, Fp, sig, BAC, sigmas
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
