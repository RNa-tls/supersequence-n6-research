#!/usr/bin/env python3
"""Round Omega -- coexistence table from a CROSS placement list (two different base lists, ordered pairs).

Base lists BX = FP_x(tx) and BY = FP_y(ty) (first-passage lists of the line(s) of X and Y; the two lines may differ),
and the complete ordered placement list of rZ/csrc/disjoint_z.c LIST=1 run as `disjoint_z BX BY` (X at the
identity, every g in S8, both orientations of Y).  For thresholds a >= tx (X side) and b >= ty (Y side),
Compat(a, b) = there are X' in FP_x(a), Y' in FP_y(b), o, g with classes(X') and g(classes(Y') or reversed) disjoint.
Reduction as in compat2d.py: the FP_x(tx)-prefix X of X' and the FP_y(ty)-prefix Y of Y' form a listed placement, so
testing every listed placement with every pair of extensions is exact.  Classes are computed here independently.
usage: compat_cross.py ca_x,cb_x ca_y,cb_y BASE_X BASE_Y PAIRS OUT.json  x:t:LIST ... y:t:LIST ..."""
import sys, json, gzip, collections, hashlib
FACT = [1, 1, 2, 6, 24, 120, 720, 5040, 40320]
def unrank(r):
    avail = list(range(8)); g = []
    for i in range(8):
        f = FACT[7 - i]; d, r = divmod(r, f); g.append(avail.pop(d))
    return g
def digits(e): return [((e >> (4 * (7 - i))) & 15) - 1 for i in range(8)]
def exc(c): return ((c & 15) << 28) | (c >> 4)
def door(x): return ((x & 0xFFFFFF) << 8) | (((x >> 24) & 15) << 4) | (x >> 28)
def canon_class(w):
    p = w.index(7); return tuple(w[(p + i) % 8] for i in range(1, 8))
def opener(p): return gzip.open(p, 'rt') if p.endswith('.gz') else open(p)
def load(path):
    out = {}
    for l in opener(path):
        t = l.split()
        if not t or t[0].startswith('#'): continue
        ents = [int(x, 16) for x in t[2:]]; assert len(ents) == int(t[1]); out[t[0]] = ents
    return out
def row_sizes(ents):
    rows = []
    for q, e in enumerate(ents):
        if q > 0 and e == door(exc(ents[q - 1])): rows[-1] += 1
        else: rows.append(1)
    return rows
def fp_prefix(ents, th, ca, cb):
    v = 0; q = 0
    for s in row_sizes(ents):
        v += ca - cb * (7 - s); q += s
        if v >= th: return q
    return None
def main():
    lx = tuple(map(int, sys.argv[1].split(','))); ly = tuple(map(int, sys.argv[2].split(',')))
    BX = load(sys.argv[3]); BY = load(sys.argv[4]); pairs = sys.argv[5]; outp = sys.argv[6]
    lists = {'x': {}, 'y': {}}
    for spec in sys.argv[7:]:
        side, t, p = spec.split(':', 2); lists[side][int(t)] = load(p)
    def val(ents, ca, cb): return sum(ca - cb * (7 - s) for s in row_sizes(ents))
    tx = min(val(e, *lx) for e in BX.values()); ty = min(val(e, *ly) for e in BY.values())
    for e in BX.values(): assert fp_prefix(e, tx, *lx) == len(e)
    for e in BY.values(): assert fp_prefix(e, ty, *ly) == len(e)
    keys = {'x': {tuple(e): n for n, e in BX.items()}, 'y': {tuple(e): n for n, e in BY.items()}}
    ext = {'x': {}, 'y': {}}
    for side, base_t, coef in (('x', tx, lx), ('y', ty, ly)):
        for t, L in lists[side].items():
            assert t >= base_t
            d = collections.defaultdict(list)
            for n, e in L.items():
                assert fp_prefix(e, t, *coef) == len(e), (side, t, n)
                q = fp_prefix(e, base_t, *coef); key = tuple(e[:q]); assert key in keys[side], (side, t, n)
                d[keys[side][key]].append(n)
            ext[side][t] = d
    def image(cs, g): return [canon_class([g[x] for x in [7] + list(c)]) for c in cs]
    cache = {}
    def classes(side, t, name, rev):
        k = (side, t, name, rev)
        if k not in cache:
            ents = lists[side][t][name]; cs = [canon_class(digits(e)) for e in ents]
            cache[k] = [tuple(reversed(c)) for c in cs] if rev else cs
        return cache[k]
    nplace = 0; found = collections.defaultdict(list)
    for l in opener(pairs):
        if l.startswith('#') or not l.strip(): continue
        head, _, tail = l.partition('|'); h = head.split(); X, Y = h[0], h[1]
        assert len(tail.split()) == sum(int(x) for x in h[2:6]), ('truncated placement list', X, Y)
        for p in tail.split():
            o, s, rank = map(int, p.split(':')); nplace += 1; g = unrank(rank)
            cx = {canon_class(digits(e)) for e in BX[X]}
            cy = image([tuple(reversed(c)) if o else c for c in (canon_class(digits(e)) for e in BY[Y])], g)
            assert not (cx & set(cy)), ('listed placement not disjoint', X, Y, o, rank)
            SX = {t: [(n, set(classes('x', t, n, False))) for n in ext['x'][t].get(X, [])] for t in lists['x']}
            SY = {t: [(n, set(image(classes('y', t, n, bool(o)), g))) for n in ext['y'][t].get(Y, [])] for t in lists['y']}
            for a in lists['x']:
                for b in lists['y']:
                    for nx, sx in SX[a]:
                        for ny, sy in SY[b]:
                            if not (sx & sy): found[(a, b)].append(dict(X=nx, Y=ny, o=o, s=s, rank=rank))
    table = {}
    for a in sorted(lists['x']):
        for b in sorted(lists['y']):
            lst = found.get((a, b), []); u = {(d['X'], d['Y'], d['o'], d['rank']) for d in lst}
            table['%d,%d' % (a, b)] = dict(compatible=bool(u), placements=len(u), examples=lst[:3])
    res = dict(line_x=lx, line_y=ly, base_x=tx, base_y=ty, base_placements=nplace, table=table,
               fp_sizes={side: {str(t): len(L) for t, L in lists[side].items()} for side in lists})
    s = json.dumps(res, indent=1); open(outp, 'w').write(s)
    print('base placements', nplace)
    for a in sorted(lists['x']):
        print('x', a, ' '.join('%d:%s' % (b, ('Y%d' % table['%d,%d' % (a, b)]['placements']) if table['%d,%d' % (a, b)]['compatible'] else 'no') for b in sorted(lists['y'])))
    print('sha256', hashlib.sha256(s.encode()).hexdigest())
main()
