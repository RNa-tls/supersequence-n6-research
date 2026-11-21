#!/usr/bin/env python3
"""Round Omega -- two-threshold coexistence table Compat(a, b), exact, from a complete base placement list.

Definitions.  FP(t) = first-passage chains of one line (value >= t, every proper prefix < t), canonical start
12345678 (the lists of rZ/csrc/fpdump.c + rZ/src/fp_split.py: `name nb entry_1 .. entry_nb`, entries 8 hex digits).
Compat(a, b) = there are X' in FP(a), Y' in FP(b), an orientation o and g in S8 with
classes(X') and g(classes(Y') or reversed classes(Y')) disjoint.

Reduction (proof).  Let theta <= min(a, b) be the base threshold.  Every FP(a) chain X' has a unique prefix in
FP(theta): its shortest prefix of value >= theta (all proper prefixes of that prefix are < theta, and it is a kept
chain because X' is).  If (X', g(Y')) is disjoint then so is (X, g(Y)) for the two FP(theta) prefixes, because
prefixes have fewer classes.  So every disjoint placement of the pair (X', Y') restricts to a disjoint placement in
the complete FP(theta) pair list (every unordered pair, every g, both orientations; rZ/csrc/disjoint_z.c with
UPPER=1 LIST=1, cross-checked pair by pair by rX/csrc/disjoint_bits.c).  Conversely we test, for every listed
placement (X, Y, o, g) and every pair of extensions, the class sets directly.  The pair list is unordered with X at
the identity; a placement of (Y at identity, g'(X)) is the listed (X, g'^-1(Y)) with the same orientation, so both
role assignments (X' in FP(a), Y' in FP(b)) and (X' in FP(b), Y' in FP(a)) are tested on every listed placement.
Classes are computed here independently of the C tools: class of a word = the cyclic order read after symbol 8.
usage: compat2d.py LINE_COEFFS(a,b e.g. 17,38) BASE_LIST BASE_PAIRS OUT.json  t1:LIST1 t2:LIST2 ..."""
import sys, json, gzip, itertools, collections, hashlib

FACT = [1, 1, 2, 6, 24, 120, 720, 5040, 40320]
def unrank(r):
    avail = list(range(8)); g = []
    for i in range(8):
        f = FACT[7 - i]; d, r = divmod(r, f); g.append(avail.pop(d))
    return g
def digits(e):                      # entry (int) -> symbols 0..7 (symbol 8 -> 7)
    return [((e >> (4 * (7 - i))) & 15) - 1 for i in range(8)]
def exc(c): return ((c & 15) << 28) | (c >> 4)
def door(x): return ((x & 0xFFFFFF) << 8) | (((x >> 24) & 15) << 4) | (x >> 28)
def canon_class(w):                 # cyclic order of 8 symbols, as the tuple read after symbol 7
    p = w.index(7); return tuple(w[(p + i) % 8] for i in range(1, 8))
def rev_class(c):                   # class of the reversed word: reversed cyclic order
    return tuple(reversed(c))
def opener(p): return gzip.open(p, 'rt') if p.endswith('.gz') else open(p)
def load(path):
    out = {}
    for l in opener(path):
        t = l.split()
        if not t or t[0].startswith('#'): continue
        ents = [int(x, 16) for x in t[2:]]; assert len(ents) == int(t[1])
        out[t[0]] = ents
    return out
def row_sizes(ents):
    rows = []
    for q, e in enumerate(ents):
        if q > 0 and e == door(exc(ents[q - 1])): rows[-1] += 1
        else: rows.append(1)
    return rows
def main():
    ca, cb = map(int, sys.argv[1].split(','))
    base = load(sys.argv[2]); base_pairs = sys.argv[3]; outp = sys.argv[4]
    lists = {}
    for spec in sys.argv[5:]:
        t, p = spec.split(':', 1); lists[int(t)] = load(p)
    theta = None
    # value of a chain on the line: sum over rows of ca - cb * (7 - size)
    def value(ents): return sum(ca - cb * (7 - s) for s in row_sizes(ents))
    def fp_prefix(ents, th):        # number of entries of the shortest prefix (whole rows) with value >= th
        v = 0; q = 0
        for s in row_sizes(ents):
            v += ca - cb * (7 - s); q += s
            if v >= th: return q, v
        return None, v
    bvals = {n: value(e) for n, e in base.items()}
    theta = min(bvals.values())
    for n, e in base.items():       # the base list is FP(theta): value >= theta, proper prefixes < theta
        q, v = fp_prefix(e, theta); assert q == len(e), n
    bkey = {tuple(e): n for n, e in base.items()}
    ext = {t: collections.defaultdict(list) for t in lists}   # ext[t][base name] = names in FP(t) extending it
    for t, L in lists.items():
        assert t >= theta
        for n, e in L.items():
            q, v = fp_prefix(e, t); assert q == len(e), (t, n)          # it is FP(t)
            qb, vb = fp_prefix(e, theta); key = tuple(e[:qb])
            assert key in bkey, (t, n)                                   # its FP(theta) prefix is in the base list
            ext[t][bkey[key]].append(n)
    cls_cache = {}
    def classes(name, t, rev):
        k = (name, t, rev)
        if k not in cls_cache:
            ents = lists[t][name] if t is not None else base[name]
            cs = [canon_class(digits(e)) for e in ents]
            cls_cache[k] = [rev_class(c) for c in cs] if rev else cs
        return cls_cache[k]
    def image(cs, g):               # apply relabelling g (g[i] = image of symbol i) to classes
        out = []
        for c in cs:
            w = [7] + list(c); w2 = [g[x] for x in w]; out.append(canon_class(w2))
        return out
    placements = []
    for l in opener(base_pairs):
        if l.startswith('#') or not l.strip(): continue
        head, _, tail = l.partition('|'); h = head.split(); X, Y = h[0], h[1]
        lst = tail.split(); assert len(lst) == sum(int(x) for x in h[2:6]), ('truncated placement list', X, Y)
        for p in lst:
            o, s, rank = map(int, p.split(':')); placements.append((X, Y, o, s, rank))
    ths = sorted(lists)
    found = {(a, b): [] for a in ths for b in ths if a >= b}
    for (X, Y, o, s, rank) in placements:
        g = unrank(rank)
        # base disjointness re-check (independent of the C tool)
        cx = set(classes(X, None, False)); cy = image(classes(Y, None, bool(o)), g)
        assert not (cx & set(cy)), ('base placement not disjoint', X, Y, o, rank)
        SX = {t: [(Xp, set(classes(Xp, t, False))) for Xp in ext[t].get(X, [])] for t in ths}
        SY = {t: [(Yp, set(image(classes(Yp, t, bool(o)), g))) for Yp in ext[t].get(Y, [])] for t in ths}
        for tx in ths:
            for ty in ths:
                key = (max(tx, ty), min(tx, ty))
                for Xp, sx in SX[tx]:
                    for Yp, sy in SY[ty]:
                        if not (sx & sy):
                            found[key].append(dict(X=Xp, tX=tx, Y=Yp, tY=ty, o=o, s=s, rank=rank, baseX=X, baseY=Y))
    table = {}
    for (a, b), lst in sorted(found.items()):
        uniq = {(d['X'], d['Y'], d['o'], d['rank']) for d in lst}
        table['%d,%d' % (a, b)] = dict(compatible=bool(uniq), placements=len(uniq), examples=lst[:3])
    res = dict(line=[ca, cb], base_threshold=theta, base_list_chains=len(base), base_placements=len(placements),
               thresholds=ths, fp_sizes={str(t): len(L) for t, L in lists.items()}, table=table)
    s = json.dumps(res, indent=1); open(outp, 'w').write(s)
    print('base placements', len(placements), 'thresholds', ths)
    for a in ths:
        print(a, ' '.join('%d:%s' % (b, ('Y%d' % table['%d,%d' % (a, b)]['placements']) if table['%d,%d' % (a, b)]['compatible'] else 'no') for b in ths if b <= a))
    print('sha256', hashlib.sha256(s.encode()).hexdigest())
main()
