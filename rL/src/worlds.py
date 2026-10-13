"""Round L -- world / orbit / phi-set combinatorics of r = 0 routes (general n, default 8).

Notation (as in rI/rK).  A class = cyclic word on the n symbols (rotation class of a permutation),
identified by its rotation starting with symbol 0.  For a special symbol a, deleting a from the
cyclic word leaves a cyclic word D on the other n-1 symbols; the world-a orbit O(a, D) is the set
of the n-1 classes obtained by inserting a into the n-1 gaps of D.  A chain with special a is a
segment of consecutive gaps of one world-a orbit (the F-step moves a forward by one gap).
For a pair {a, b} and a cyclic word C on the other n-2 symbols, the phi-set P({a,b}, C) is the set
of the (n-2)(n-1) classes whose cyclic word, with a and b deleted, is C.
"""
import itertools
from functools import lru_cache

def canon_cyc(seq):
    """canonical rotation of a cyclic sequence: start at its minimum element"""
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])

class World:
    def __init__(self, n=8):
        self.n = n
        self.reps = sorted({canon_cyc(p) for p in itertools.permutations(range(n))})
        self.cid = {c: i for i, c in enumerate(self.reps)}
        self.M = len(self.reps)
        # orbit index of class i in world a, and the position (gap index) of a inside it
        self.orb = [[None] * self.M for _ in range(n)]
        self.orb_members = [dict() for _ in range(n)]
        for a in range(n):
            for i, c in enumerate(self.reps):
                D = [x for x in c if x != a]
                D = canon_cyc(D)
                self.orb[a][i] = D
            groups = {}
            for i in range(self.M):
                groups.setdefault(self.orb[a][i], []).append(i)
            self.orb_members[a] = groups
        # ordered orbit: the class with a inserted after D[g] (gap g = between D[g] and D[g+1])
        self.phi_key = {}

    def insert(self, D, a, g):
        """class id of D with a inserted after position g (0 <= g < len(D))"""
        s = list(D[:g + 1]) + [a] + list(D[g + 1:])
        return self.cid[canon_cyc(s)]

    def orbit_cycle(self, a, D):
        """classes of O(a, D) in F-order: gap g -> g+1 is one F-step"""
        return [self.insert(D, a, g) for g in range(len(D))]

    def phi_of(self, i, a, b):
        c = self.reps[i]
        C = canon_cyc([x for x in c if x not in (a, b)])
        return (min(a, b), max(a, b), C)

    def phi_sets(self, a, b):
        groups = {}
        for i in range(self.M):
            groups.setdefault(self.phi_of(i, a, b), []).append(i)
        return groups
