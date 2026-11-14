#!/usr/bin/env python3
"""Round Z -- classification of the disjoint placements listed by rZ/csrc/disjoint_z.c (LIST=1), exact.
For every placement (X, g(Y)) or (X, g(rev Y)) it records: the image s = g(8) (same or cross symbol), the orientation,
the values and rows of X and Y, the seam types, the number of world-8 2-cycles used by X and by the placed copy (the
two sets are disjoint when all rows have >= 4 blocks), the size of their union out of 720, and the number of
{8,x}-blocks (x = 1..7, 840 blocks) that contain rows of both (the "contact" of the two chains in the symbol world).
usage: placement_classify.py FPLIST DISJOINT_Z_OUTPUT LINE(1|2) OUT.json"""
import sys, json, collections
fpl, dz, line, outp = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
fact = [1, 1, 2, 6, 24, 120, 720, 5040, 40320]
def unrank(r):
    avail = list(range(8)); g = []
    for i in range(8):
        f = fact[7 - i]; d, r = divmod(r, f); g.append(avail.pop(d))
    return g
def exc(c): return ((c & 15) << 28) | (c >> 4)
def door(x): return ((x & 0xFFFFFF) << 8) | (((x >> 24) & 15) << 4) | (x >> 28)
def digits(e): return [((e >> (4 * (7 - i))) & 15) - 1 for i in range(8)]       # symbols 0..7 (7 = the symbol 8)
def rev(w): return list(reversed(w))
def canon(t): k = t.index(min(t)); return tuple(t[k:] + t[:k])
def rows_of(ents):
    rows = []
    for q, e in enumerate(ents):
        if q > 0 and e == door(exc(ents[q - 1])): rows[-1].append(e)
        else: rows.append([e])
    return rows
def seamtypes(rows):
    out = collections.Counter()
    for i in range(len(rows) - 1):
        y = exc(rows[i][-1]); e = rows[i + 1][0]
        a, b, c = y >> 28, (y >> 24) & 15, (y >> 20) & 15; t = ((e >> 8) & 15, (e >> 4) & 15, e & 15)
        out[{(a, c, b): 'c', (b, a, c): 'b', (b, c, a): 'e', (c, a, b): 'f', (c, b, a): 'd'}.get(t, '?')] += 1
    return out
info = {}
for l in open(fpl):
    t = l.split(); name = t[0]; ents = [int(x, 16) for x in t[2:]]
    rws = rows_of(ents)
    G = []          # (2-cycle as canonical 7-tuple of the symbols after 7, size) for world-7 rows; reversed copy too
    Gr = []
    for r in rws:
        w = digits(r[0])
        if w[7] != 7: continue
        G.append((canon(w[:7]), len(r)))
        Gr.append((canon(list(reversed(w[:7]))), len(r)))
    v = int(name.split('v')[1].split('_')[0]); rr = int(name.split('_r')[1].split('_')[0]); dd = int(name.split('_d')[1].split('_')[0])
    info[name] = dict(v=v, r=rr, d=dd, G=G, Gr=Gr, seams=dict(seamtypes(rws)), five=sum(1 for r in rws if len(r) == 5))
def blocks_of(cycles):
    out = set()
    for C, _ in cycles:
        for x in range(7):
            D = [s for s in C if s != x]; out.add((x, canon(D)))
    return out
rec = []; by_s = collections.Counter(); by_o = collections.Counter(); pairs = 0; contact = []
for l in open(dz):
    if l.startswith('#') or not l.strip(): continue
    head, _, tail = l.partition('|'); h = head.split(); X, Y = h[0], h[1]; pairs += 1
    for p in tail.split():
        o, s, rank = map(int, p.split(':')); by_s['same' if s == 7 else 'cross'] += 1; by_o[o] += 1
        g = unrank(rank); src = info[Y]['Gr'] if o else info[Y]['G']
        img = [(canon([g[c] for c in C]), sz) for C, sz in src] if s == 7 else []
        gx = {C for C, _ in info[X]['G']}; gy = {C for C, _ in img}
        cb = len(blocks_of(info[X]['G']) & blocks_of(img)) if s == 7 else None
        rec.append(dict(X=X, Y=Y, o=o, s=s, vX=info[X]['v'], vY=info[Y]['v'], rX=info[X]['r'], rY=info[Y]['r'], fiveX=info[X]['five'], fiveY=info[Y]['five'],
                        cyclesX=len(gx), cyclesY=len(gy), shared_cycles=len(gx & gy), union_cycles=len(gx | gy), contact_blocks=cb,
                        seamsX=info[X]['seams'], seamsY=info[Y]['seams']))
res = dict(line=line, pairs_with_placements=pairs, placements=len(rec), by_image_of_8=dict(by_s), by_orientation={str(k): v for k, v in by_o.items()},
           shared_world8_cycles_max=max((r['shared_cycles'] for r in rec), default=None),
           union_cycles_range=[min((r['union_cycles'] for r in rec), default=None), max((r['union_cycles'] for r in rec), default=None)],
           contact_blocks_range=[min((r['contact_blocks'] for r in rec), default=None), max((r['contact_blocks'] for r in rec), default=None)],
           value_pairs=dict(collections.Counter('%d+%d' % (r['vX'], r['vY']) for r in rec).most_common(12)),
           seam_types_in_placed_chains=dict(collections.Counter(k for r in rec for k in list(r['seamsX']) + list(r['seamsY']))),
           placements_detail=rec)
json.dump(res, open(outp, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'placements_detail'}))
