#!/usr/bin/env python3
"""Round L (section 19) -- linking inside the phi-structure: cost-4 joins between phi-cycle trails.

A phi-cycle of pair {a,b} traversed in world a is 6 full chains whose first run starts have b
immediately before a; opened at one of its 6 BAC joins it is a trail.  Its last run start x has
x0 = b, x7 = a; the trail's last perm is e(x) = x7 x0 .. x6.  A join of weight 4 goes to
t = x3 x4 x5 x6 + (a permutation of x7 x0 x1 x2).
This script checks, for every phi-cycle (all C, both worlds, all 6 cuts; up to relabelling it
suffices to take a = 7, b = 6 and all C, but everything is enumerated), which cost-4 targets are
starts of phi-cycle trails of the SAME pair, and verifies the
LINK LEMMA: such a target exists iff it lies in the phi-set C' = C with (x1, x2) exchanged (the
(n-2)-level F-step of world x1, x1 x2 = the two symbols after b in the end class), in either world,
and the cut of the next phi-cycle is then forced; consequently a sequence of phi-cycle trails of
one pair joined only by cost-4 joins follows (n-2)-level F-steps.
It also tabulates cost-4 targets that are phi-cycle starts of OTHER pairs.
usage: phi_link4.py"""
import itertools, json, os, sys
from collections import Counter

n = 8
def F(p): return p[1:n - 1] + p[:1] + p[n - 1:]
def join(x, s): return x[2:n - 1] + tuple(x[k] for k in s)
BAC = (1, 0, n - 1)
def cyc(seq):
    seq = list(seq); k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def wt(x, y):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n
def last(p): return p[-1:] + p[:-1]

def phi_cycle_trail(start):
    """chains of the phi-cycle trail starting at run start `start` (start[n-2] = b)"""
    p = start; ends = []
    for r in range(n - 2):
        x = p
        for _ in range(n - 2): x = F(x)
        ends.append(x); p = join(x, BAC)
    assert p == start
    return ends[-1]

def main():
    a, b = 7, 6
    others = [s for s in range(n) if s not in (a, b)]
    stats = Counter(); viol = 0; other_pairs = Counter()
    for perm in itertools.permutations(others):
        for world, other in ((a, b), (b, a)):
            start = perm + (other, world)          # run start: ... other world  => phi-cycle of pair {a,b}
            x = phi_cycle_trail(start)
            assert x[0] == other and x[n - 1] == world
            C = cyc([z for z in start if z not in (a, b)])
            e = last(x)
            x1, x2 = x[1], x[2]
            L = list(C); i = L.index(x1); j = (i + 1) % 6
            assert L[j] == x2
            L[i], L[j] = L[j], L[i]; Cp = cyc(L)
            for pi in itertools.permutations(e[:4]):
                t = e[4:] + pi
                if wt(e, t) != 4: continue
                # is t the run start of a phi-cycle trail? (t[n-2] = its pair partner, t[n-1] its world)
                pair = frozenset((t[n - 1], t[n - 2]))
                if pair == frozenset((a, b)):
                    Ct = cyc([z for z in t if z not in (a, b)])
                    ok = (Ct == Cp)
                    if Ct == C: kind = "same phi-set (impossible: own trail)"
                    elif ok: kind = "F-step(x1) phi-set"
                    else: kind = "OTHER"; viol += 1
                    stats[(kind, "world " + ("same" if t[n - 1] == world else "swap"))] += 1
                else:
                    other_pairs[len(pair & frozenset((a, b)))] += 1
    res = dict(phi_cycles_checked=2 * 720, same_pair_cost4_targets={f"{k[0]} / {k[1]}": v for k, v in stats.items()},
               violations=viol, other_pair_targets_by_shared_specials=dict(other_pairs), link_lemma_ok=(viol == 0))
    print(json.dumps(res))
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "phi_link4.json"), "w"), indent=1)

if __name__ == "__main__":
    main()

def chain_lengths():
    """follow cost-4 links between phi-cycle trails of pair {7,6}: state = trail start perm.
    Returns the length distribution of maximal cost-4 chains of distinct phi-sets."""
    a, b = 7, 6
    others = [s for s in range(n) if s not in (a, b)]
    succ = {}
    for perm in itertools.permutations(others):
        for world, other in ((a, b), (b, a)):
            start = perm + (other, world)
            x = phi_cycle_trail(start); e = last(x)
            nxt = []
            for pi in itertools.permutations(e[:4]):
                t = e[4:] + pi
                if wt(e, t) == 4 and frozenset((t[n - 1], t[n - 2])) == frozenset((a, b)):
                    if cyc([z for z in t if z not in (a, b)]) != cyc([z for z in start if z not in (a, b)]):
                        nxt.append(t)
            succ[start] = nxt
    # moving symbol along the chain: x1 of the end
    same_symbol = 0; total = 0
    for s, nx in succ.items():
        u = phi_cycle_trail(s)[1]
        for t in nx:
            total += 1
            if phi_cycle_trail(t)[1] == u: same_symbol += 1
    # longest simple chain of distinct phi-sets (DFS, the graph has out-degree 2)
    best = 0
    def dfs(s, seenC, d):
        nonlocal best
        best = max(best, d)
        for t in succ[s]:
            Ct = cyc([z for z in t if z not in (a, b)])
            if Ct not in seenC: dfs(t, seenC | {Ct}, d + 1)
    for s in list(succ)[:1440]:
        dfs(s, {cyc([z for z in s if z not in (a, b)])}, 1)
    return dict(links=total, links_keeping_moving_symbol=same_symbol, longest_cost4_chain_of_phi_cycles=best)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "chains":
    r = chain_lengths(); print(json.dumps(r))
    d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "phi_link4.json")))
    d.update(r); json.dump(d, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "phi_link4.json"), "w"), indent=1)
