#!/usr/bin/env python3
"""Round X -- the Klein relabelings of the public selection map the letter arcs of every trail onto the letter arcs of
its image trail (same cost, head and tail relabeled) and the chain ends (Q tail, N0 head) of every host onto those of
its image host.  Overlaps, hence join costs, are invariant under relabeling, so the host-split values J17 / J19 of a
pair equal those of its image pair: hosts in one orbit ({0,4,8,11}, {1,3,6,10}, {2,5,7,9}, {12,13,14,15}) need one
representative.  usage: check_symmetry.py BASE_LETTER_ARCS SPLITDIR"""
import sys, collections, json
arcsp, sd = sys.argv[1:3]
G = {"01543267": {0: 11, 1: 10, 2: 7, 3: 6, 4: 8, 5: 9, 6: 3, 7: 2, 8: 4, 9: 5, 10: 1, 11: 0, 12: 13, 13: 12, 14: 15, 15: 14},
     "10243567": {0: 4, 1: 6, 2: 5, 3: 10, 4: 0, 5: 2, 6: 1, 7: 9, 8: 11, 9: 7, 10: 3, 11: 8, 12: 15, 13: 14, 14: 13, 15: 12},
     "10534267": {0: 8, 1: 3, 2: 9, 3: 1, 4: 11, 5: 7, 6: 10, 7: 5, 8: 0, 9: 2, 10: 6, 11: 4, 12: 14, 13: 15, 14: 12, 15: 13}}
arcs = collections.defaultdict(set)
for l in open(arcsp):
    t, s, k, c, h, tl = l.split(); arcs[int(t)].add((int(c), h, tl))
res = {}
for g, tm in G.items():
    mp = dict(zip("01234567", g)); f = lambda w: "".join(mp[ch] for ch in w)
    a_ok = all({(c, f(h), f(tl)) for c, h, tl in arcs[t]} == arcs[tm[t]] for t in range(16))
    e_ok = all({(f(x[5]), f(x[6])) for x in (l.split() for l in open("%s/chains_%d.txt" % (sd, h)))} ==
               {(x[5], x[6]) for x in (l.split() for l in open("%s/chains_%d.txt" % (sd, tm[h])))} for h in range(16))
    res[g] = dict(trail_map=tm, letter_arcs_invariant=a_ok, chain_ends_invariant=e_ok)
print(json.dumps(res))
