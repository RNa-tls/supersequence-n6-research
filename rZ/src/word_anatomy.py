#!/usr/bin/env python3
"""Round Z -- anatomy of a real superpermutation word in Halfar's row model (exact, deterministic).

Reads a word over 8 symbols that contains every permutation.  Every permutation is designated at its first
occurrence; consecutive designated permutations are joined by steps of weight = difference of positions.
  block = maximal run of weight-1 steps inside one rotation class;  row = blocks joined by weight-2 steps;
  seam  = step of weight >= 3 between rows;  chain = rows joined by seams of weight exactly 3.
For every row: moving symbol z = last symbol of its entry (the first permutation of each of its blocks; checked
constant along the row), 2-cycle (z, C) with C the cyclic order of the other seven symbols.
Weight-3 seam from exit y = y1..y8 to entry y4..y8 pi(y1 y2 y3) has type
  c (z v2 v1), b (v1 z v2), e (v1 v2 z), f (v2 z v1), d (v2 v1 z)      (y1 = z, v1 = y2, v2 = y3);
b, c, f change the moving symbol, d, e keep it.
Outputs (JSON): rows by size and by world, used 2-cycles per world U_s, extra rows M of split 2-cycles, overlap
W = sum_X (g(X) - 1), the check Delta = W + 7 M, seams by type, label changes, one-symbol segments, runs of full rows
and the seams around 6-runs, 6-rows by their seams (S6 test), hole pairs of 5-rows (which world covers each hole),
and per chain r, d, v1 = 4r - 9d, v2 = 17r - 38d, label changes, segments.
usage: word_anatomy.py WORD.txt [OUT.json]"""
import sys, json, collections

w = open(sys.argv[1]).read().strip()
n = 8
syms = sorted(set(w)); assert len(syms) == n
first = {}
for i in range(len(w) - n + 1):
    s = w[i:i + n]
    if len(set(s)) == n and s not in first:
        first[s] = i
seq = sorted(first.items(), key=lambda t: t[1]); assert len(seq) == 40320
perm = [p for p, _ in seq]; pos = [q for _, q in seq]
steps = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]


def cls(p):                       # rotation class, canonical: rotate to start with the smallest symbol
    k = p.index(syms[0]); return p[k:] + p[:k]


def cyc(s):                       # canonical rotation of a cyclic sequence (string)
    k = s.index(min(s)); return s[k:] + s[:k]


# blocks
blocks = []; cur = [0]
for i, st in enumerate(steps):
    if st == 1 and cls(perm[i]) == cls(perm[i + 1]):
        cur.append(i + 1)
    else:
        blocks.append(cur); cur = [i + 1]
blocks.append(cur)
for b in blocks:
    assert len({cls(perm[j]) for j in b}) == 1
after = [steps[b[-1]] if b[-1] < len(steps) else None for b in blocks]
# rows
rows = []; cur = [0]
for bi in range(len(blocks) - 1):
    if after[bi] == 2:
        cur.append(bi + 1)
    else:
        rows.append(cur); cur = [bi + 1]
rows.append(cur)
R = len(rows)
row_z, row_G, row_size, row_cls = [], [], [], []
partial_rows = []
for r in rows:
    ents = [perm[blocks[b][0]] for b in r]
    fulls = [perm[blocks[b][0]] for b in r if len(blocks[b]) == 8] or ents
    z = fulls[0][-1]
    C = cyc(fulls[0][:-1])
    bad = [e for b, e in zip(r, ents) if len(blocks[b]) == 8 and (e[-1] != z or cyc(e[:-1]) != C)]
    assert not bad, "moving symbol or 2-cycle not constant along a row of full blocks"
    if any(len(blocks[b]) != 8 for b in r):
        partial_rows.append(len(row_z))
    row_z.append(z); row_G.append((z, C)); row_size.append(len(r)); row_cls.append([cls(e) for e in ents])
holes = [7 - s for s in row_size]; Delta = sum(holes)


def two_cycle_of(X, z):          # the z-2-cycle of class X
    k = X.index(z); s = X[k + 1:] + X[:k]; return (z, cyc(s))


def two_cycle_classes(G):        # the 7 classes of 2-cycle G = (z, C), in the order z moves forward
    z, C = G; out = []
    for g in range(7):
        out.append(cls(C[g:] + C[:g] + z))       # z just before C[g]... any consistent order
    return out


# seams
def seam_type(y, e):
    if e[:5] != y[3:]:
        return None
    t = e[5:]; a, b, c = y[0], y[1], y[2]     # a = z, b = v1, c = v2
    return {a + c + b: 'c', b + a + c: 'b', b + c + a: 'e', c + a + b: 'f', c + b + a: 'd', a + b + c: '0'}.get(t)


seam_w, seam_t = [], []
for i in range(R - 1):
    lastb = blocks[rows[i][-1]]; y = perm[lastb[-1]]
    e = perm[blocks[rows[i + 1][0]][0]]
    wgt = pos[blocks[rows[i + 1][0]][0]] - pos[lastb[-1]]
    seam_w.append(wgt); seam_t.append(seam_type(y, e) if wgt == 3 else 'X%d' % wgt)
# chains
chains = []; cur = [0]
for i in range(R - 1):
    if seam_w[i] == 3:
        cur.append(i + 1)
    else:
        chains.append(cur); cur = [i + 1]
chains.append(cur)
# coverage, 2-cycles, W, M
cover = collections.defaultdict(list)
for ri in range(R):
    for X in row_cls[ri]:
        cover[X].append(ri)
split_classes = sum(1 for X, l in cover.items() if len(l) > 1)
usedG = collections.Counter(row_G)
M = sum(t - 1 for t in usedG.values())
U = len(usedG)
g = {}
for X in cover:
    g[X] = sum(1 for z in syms if two_cycle_of(X, z) in usedG)
W = sum(v - 1 for v in g.values())
world_rows = collections.Counter(row_z)
world_U = collections.Counter(G[0] for G in usedG)
world_classes = collections.Counter(row_z[ri] for X, l in cover.items() for ri in l)
# label changes, segments
LC = sum(1 for i in range(R - 1) if seam_w[i] == 3 and seam_t[i] in 'bcf')
seg_lengths = []
for ch in chains:
    s = 1
    for a, b in zip(ch, ch[1:]):
        if row_z[a] == row_z[b]:
            s += 1
        else:
            seg_lengths.append(s); s = 1
    seg_lengths.append(s)
# runs of full rows (inside chains) and seams around 6-runs
runs = collections.Counter(); six_run_ctx = collections.Counter()
for ch in chains:
    i = 0
    while i < len(ch):
        if row_size[ch[i]] == 7:
            j = i
            while j + 1 < len(ch) and row_size[ch[j + 1]] == 7:
                j += 1
            L = j - i + 1; runs[L] += 1
            if L >= 6:
                before = 'start' if i == 0 else seam_t[ch[i] - 1]
                aft = 'end' if j == len(ch) - 1 else seam_t[ch[j]]
                six_run_ctx[(L, before, aft)] += 1
            i = j + 1
        else:
            i += 1
# 6-rows: S6 test
six_ctx = collections.Counter()
for ch in chains:
    for k, ri in enumerate(ch):
        if row_size[ri] != 6:
            continue
        before = 'start' if k == 0 else seam_t[ri - 1]
        aft = 'end' if k == len(ch) - 1 else seam_t[ri]
        tag = before + '/' + aft
        if before == 'd' and aft == 'd':
            tag += ' prevG==nextG' if row_G[ch[k - 1]] == row_G[ch[k + 1]] else ' prevG!=nextG'
        six_ctx[tag] += 1
# hole pairs of 5-rows and singles of 6-rows: who covers the holes
hole_cover = collections.Counter()
for ri in range(R):
    if row_size[ri] in (5, 6) and usedG[row_G[ri]] == 1:
        mine = set(row_cls[ri])
        hs = [X for X in two_cycle_classes(row_G[ri]) if X not in mine]
        ws = tuple(sorted(('same' if row_z[cover[X][0]] == row_z[ri] else 'other') for X in hs))
        same_row = len(hs) == 2 and cover[hs[0]][0] == cover[hs[1]][0]
        hole_cover[(row_size[ri], ws, same_row)] += 1
# per chain
cv = []
for ch in chains:
    r = len(ch); d = sum(holes[i] for i in ch)
    lc = sum(1 for a in ch[:-1] if seam_t[a] in ('b', 'c', 'f'))
    ne = sum(1 for a in ch[:-1] if seam_t[a] == 'e')
    zs = collections.Counter(row_z[i] for i in ch)
    pre = [0]
    for i in ch:
        pre.append(pre[-1] + (17 - 38 * holes[i]))
    cv.append(dict(r=r, d=d, v1=4 * r - 9 * d, v2=17 * r - 38 * d, label_changes=lc, e_seams=ne, worlds=len(zs),
                   main_world_rows=zs.most_common(1)[0][1], v2_max_prefix=max(pre), v2_min_prefix=min(pre),
                   sizes=dict(sorted(collections.Counter(row_size[i] for i in ch).items()))))
res = dict(word=sys.argv[1], length=len(w), rows=R, Delta=Delta, Delta_check=7 * R - len(blocks), blocks=len(blocks),
           split_classes=split_classes, rows_with_partial_blocks=partial_rows, partial_block_sizes=sorted(len(b) for b in blocks if len(b) != 8), length_formula=46085 + (R - 720) + sum(x - 3 for x in seam_w),
           row_sizes=dict(sorted(collections.Counter(row_size).items())), used_2cycles=U, M=M, W=W,
           W_plus_7M=W + 7 * M, rows_by_world=dict(sorted(world_rows.items())),
           used_2cycles_by_world=dict(sorted(world_U.items())), classes_by_world=dict(sorted(world_classes.items())),
           seams_by_type=dict(sorted(collections.Counter(seam_t).items())), label_changes=LC,
           chains=len(chains), segments=len(seg_lengths), segment_length_hist=dict(sorted(collections.Counter(seg_lengths).items())),
           full_runs=dict(sorted(runs.items())), runs_ge6_context={str(k): v for k, v in sorted(six_run_ctx.items())},
           six_rows_context=dict(sorted(six_ctx.items())), hole_cover={str(k): v for k, v in sorted(hole_cover.items())},
           chains_detail=cv)
out = json.dumps(res, indent=1)
if len(sys.argv) > 2:
    open(sys.argv[2], 'w').write(out + '\n')
short = {k: v for k, v in res.items() if k != 'chains_detail'}
print(json.dumps(short))
for c in sorted(cv, key=lambda c: -c['r'])[:20]:
    print(c)
