#!/usr/bin/env python3
"""Round J -- exact chain-ordering model, written from scratch (no code shared with rI/chain_atsp_lp).

THE PROBLEM.  Fix an r = 0 chain set K (chain c = (start s_c, run end e_c), the chains' classes
partition all classes).  A route on K is an ordering c_1..c_q of all chains; its word length is
    L = n + (n-1) HEX + 2 (HEX - q) + sum_{i<q} cost(e_{c_i}, s_{c_{i+1}})
      = BASE + sum_{i<q} w(c_i, c_{i+1}),    w(a,b) = cost(e_a, s_b) - 3,  BASE = CONST - ORB + q.
(Any ordering is a valid superpermutation: every class is a full run, so all n! permutations occur.)

THE MODEL (exact).  Nodes: chains 0..q-1, depot D = q (path start/end), hub H = q+1.
Arcs: a->b for a != b with overlap >= 1 (w = cost - 3 in {-1..n-4}); a->H (w = n-3) and H->b (w = 0)
replace the no-overlap links (cost n, w = n-3); D->b and a->D (w = 0).  All variables are binary:
a chain has out-degree 1 (so a->H <= 1) and in-degree 1 (so H->b <= 1).
Constraints: out(v) = in(v) = 1 for chains and D;  out(H) = in(H);
SUBTOUR CUTS  x(delta^+(S)) >= 1  for every node set S with D not in S and S containing a chain.
Validity of a cut for EVERY route: the route is a walk D -> ... -> D through all chains (hub visits
inserted for no-overlap links); after its last visit to S the walk must leave S because D is not in S.
Exactness: a route gives a feasible solution of the same weight; conversely an integer solution
satisfying all cuts has every node reaching D and balanced degrees, hence an Euler circuit from D;
deleting hub visits gives an ordering whose real joins at former hub visits cost <= n (w <= n-3).
"""
import sys, os, math, json, random

def load_word(path):
    w = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(w)); mp = {c: i for i, c in enumerate(al)}
    return [mp[c] for c in w], len(al)

def ov_cost(x, y, n):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n

def chains_from_word(w, n):
    """Independent chain extraction: permutations in first-occurrence order must form full runs
    (r = 0); consecutive runs joined by cost 2 belong to the same chain."""
    N = math.factorial(n); seen = set(); route = []
    for i in range(len(w) - n + 1):
        t = tuple(w[i:i + n])
        if len(set(t)) == n and t not in seen: seen.add(t); route.append(t)
    assert len(route) == N
    R = lambda s: s[1:] + s[:1]
    runs = []; i = 0
    while i < N:
        s = route[i]
        for k in range(n): assert route[i + k] == (s if k == 0 else R(route[i + k - 1]))
        runs.append(s); i += n
    Fm = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    chains = [[runs[0]]]
    for a, b in zip(runs, runs[1:]):
        if b == Fm(a): chains[-1].append(b)
        else: chains.append([b])
    Rinv = lambda s: s[-1:] + s[:-1]
    return [(ch[0], Rinv(ch[-1]), len(ch)) for ch in chains]

class Model:
    def __init__(self, chains, n):
        self.n = n; self.ch = chains; q = self.q = len(chains)
        self.D, self.H = q, q + 1; self.V = q + 2
        HEX = math.factorial(n - 1); ORB = math.factorial(n - 2)
        CONST = math.factorial(n) + HEX + ORB + n - 3
        self.BASE = CONST - ORB + q
        byprefix = {}
        for b, (s, _, _) in enumerate(chains):
            for j in range(1, n): byprefix.setdefault(s[:j], []).append(b)
        arcs = []; self.arc_id = {}
        for a, (_, e, _) in enumerate(chains):
            got = set()
            for j in range(n - 1, 0, -1):
                for b in byprefix.get(e[n - j:], []):
                    if b != a and b not in got:
                        got.add(b); arcs.append((a, b, ov_cost(e, chains[b][0], n) - 3))
        for a in range(q): arcs.append((a, self.H, n - 3)); arcs.append((a, self.D, 0))
        for b in range(q): arcs.append((self.H, b, 0)); arcs.append((self.D, b, 0))
        self.arcs = arcs
        for i, (a, b, _) in enumerate(arcs): self.arc_id[(a, b)] = i
        self.out_of = [[] for _ in range(self.V)]; self.in_of = [[] for _ in range(self.V)]
        for i, (a, b, _) in enumerate(arcs): self.out_of[a].append(i); self.in_of[b].append(i)

    def route_arcs(self, order):
        """arc multiset (list of arc ids) of the route visiting chains in `order`."""
        ids = [self.arc_id[(self.D, order[0])]]
        for a, b in zip(order, order[1:]):
            if (a, b) in self.arc_id: ids.append(self.arc_id[(a, b)])
            else: ids.append(self.arc_id[(a, self.H)]); ids.append(self.arc_id[(self.H, b)])
        ids.append(self.arc_id[(order[-1], self.D)])
        return ids

    def route_weight(self, order):
        return sum(ov_cost(self.ch[a][1], self.ch[b][0], self.n) - 3 for a, b in zip(order, order[1:]))

    def cut_ok_on(self, S, arc_ids):
        """number of route arcs leaving S (must be >= 1 for a valid cut)."""
        return sum(1 for i in arc_ids if self.arcs[i][0] in S and self.arcs[i][1] not in S)

    @staticmethod
    def cut_structurally_valid(S, q):
        D = q
        return (D not in S) and any(v < q for v in S)

def reference_orders(model, word_order, k_random=200, seed=0):
    """reference routes for cut testing: the word's own order, its reverse-rotations, random orders."""
    rng = random.Random(seed); q = model.q
    refs = [list(word_order)]
    for _ in range(k_random):
        o = list(range(q)); rng.shuffle(o); refs.append(o)
    # random 'cycle-respecting' orders: rotate the word order at random points (still valid routes)
    for _ in range(20):
        i = rng.randrange(q); refs.append(list(word_order[i:]) + list(word_order[:i]))
    return refs

if __name__ == "__main__":
    w, n = load_word(sys.argv[1])
    ch = chains_from_word(w, n)
    M = Model(ch, n)
    order = list(range(M.q))
    print(json.dumps(dict(q=M.q, arcs=len(M.arcs), BASE=M.BASE, word_route_weight=M.route_weight(order),
                          predicted_length=M.BASE + M.route_weight(order), word_length=len(w))))
