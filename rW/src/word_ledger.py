#!/usr/bin/env python3
"""Round W -- Halfar's row accounting computed directly from a word over 0..7 that contains all permutations.

Designate every permutation at its first occurrence; consecutive designated permutations (in order of position) are
joined by steps of weight = difference of positions, so  L = 8 + sum of weights.
  block  = a maximal run of weight-1 steps inside one rotation class (a full block has 8 permutations)
  row    = blocks joined by steps of weight 2;  holes of a row = 7 - (number of blocks)      (full blocks only)
  seam   = a step of weight >= 3 between rows;  heavy seam = weight >= 4
  chain  = rows joined by seams of weight exactly 3 (Halfar's exact weight-three chain);  value v1 = 4 r - 9 d,
           v2 = 17 r - 38 d  (r rows, d holes)
For a word in which every class is one full block:  L = 46085 + (R - 720) + sum over seams of (w - 3).
usage: word_ledger.py WORD.txt [OUT.json]"""
import sys, json, collections
w = open(sys.argv[1]).read().strip(); n = 8
first = {}
for i in range(len(w) - n + 1):
    s = w[i:i + n]
    if len(set(s)) == n and s not in first: first[s] = i
seq = sorted(first.items(), key=lambda t: t[1]); assert len(seq) == 40320
def cls(p):
    z = p.index("0"); return p[z:] + p[:z]
steps = [seq[i + 1][1] - seq[i][1] for i in range(len(seq) - 1)]
hist = collections.Counter(steps)
# blocks: maximal runs of weight-1 steps; check class constancy
blocks = []; cur = [0]
for i, st in enumerate(steps):
    if st == 1: cur.append(i + 1)
    else: blocks.append(cur); cur = [i + 1]
blocks.append(cur)
full = sum(1 for b in blocks if len(b) == 8); partial = [len(b) for b in blocks if len(b) != 8]
for b in blocks: assert len({cls(seq[j][0]) for j in b}) == 1
classes_split = sum(1 for c, k in collections.Counter(cls(seq[b[0]][0]) for b in blocks).items() if k > 1)
# rows: blocks joined by weight-2 steps; seams: steps of weight >= 3 between blocks
links = [steps[b[-1]] if b[-1] < len(steps) else None for b in blocks]     # step after each block
rows = []; cur = [0]
for bi in range(len(blocks) - 1):
    if links[bi] == 2: cur.append(bi + 1)
    else: rows.append(cur); cur = [bi + 1]
rows.append(cur)
seams = [links[r[-1]] for r in rows[:-1]]
R = len(rows); holes = [7 - len(r) for r in rows]; D = sum(holes)
# chains: rows joined by seams of weight 3
chains = []; cur = [0]
for ri in range(R - 1):
    if seams[ri] == 3: cur.append(ri + 1)
    else: chains.append(cur); cur = [ri + 1]
chains.append(cur)
cv = []
for ch in chains:
    r = len(ch); d = sum(holes[i] for i in ch); cv.append((r, d, 4 * r - 9 * d, 17 * r - 38 * d))
L = len(w)
res = dict(length=L, steps_by_weight={str(k): v for k, v in sorted(hist.items())}, blocks=len(blocks), full_blocks=full, partial_blocks=sorted(partial), classes_in_two_or_more_blocks=classes_split,
           rows=R, holes=D, holes_check_7R_minus_blocks=7 * R - len(blocks), seams_by_weight={str(k): v for k, v in sorted(collections.Counter(seams).items())},
           seam_excess=sum(s - 3 for s in seams), N=R - 720, formula_46085_plus_N_plus_excess=46085 + (R - 720) + sum(s - 3 for s in seams),
           chains=len(chains), heavy_seams=sum(1 for s in seams if s >= 4),
           chain_values_v1_hist={str(k): v for k, v in sorted(collections.Counter(c[2] for c in cv).items())},
           chain_max_v1=max(c[2] for c in cv), chain_max_v2=max(c[3] for c in cv), sum_v1=sum(c[2] for c in cv), sum_v2=sum(c[3] for c in cv),
           line1_sum_slack=sum(56 - c[2] for c in cv), line2_sum_slack=sum(264 - c[3] for c in cv),
           longest_chains=sorted(cv, key=lambda c: -c[0])[:8], row_length_hist={str(k): v for k, v in sorted(collections.Counter(len(r) for r in rows).items())})
print(json.dumps({k: v for k, v in res.items() if k != "longest_chains"}))
print("longest chains (r, d, v1, v2):", res["longest_chains"])
if len(sys.argv) > 2: json.dump(res, open(sys.argv[2], "w"), indent=1)
