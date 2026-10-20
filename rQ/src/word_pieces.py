#!/usr/bin/env python3
"""Round Q -- independent piece decomposition of a word of the 6A+24phi family.
Splits the run route of the word into PIECES: maximal blocks of consecutive runs of one trail that are consecutive in
one version cycle of that trail (greedy, longest piece first).  A word is single-opening iff it has 30 pieces.
Prints one line per piece (trail, version, first/last run index in the route, length, start index in the version cycle)
and checks that every trail uses one version and that its pieces partition its version cycle.
usage: word_pieces.py WORD FAMILY.json"""
import sys, json
n = 8
def load_word(p):
    t = "".join(ch for ch in open(p).read() if not ch.isspace()); al = sorted(set(t)); return [al.index(c) for c in t]
def starts(w):
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j]
    return st
def canon(p): return min(p[i:] + p[:i] for i in range(n))
w = load_word(sys.argv[1]); fam = json.load(open(sys.argv[2]))
st = starts(w)
loc = {}
for t, tr in enumerate(fam["trails"]):
    for v, s in enumerate(tr["versions"]):
        m = len(s) // 8
        for k in range(m): loc.setdefault(canon(tuple(int(c) for c in s[8 * k:8 * k + 8])), []).append((t, v, k, m))
# each run class belongs to one trail; version = the one whose cycle contains the actual rotation? runs are identified by canon class
# a run's class appears in both versions of its trail; decide pieces greedily: consecutive runs i, i+1 are in one piece iff same trail
# and some version has them consecutive (k, k+1 mod m) -- check consistent version afterwards
cls = [canon(s) for s in st]
pieces = []; i = 0; N = len(st)
while i < N:
    t0 = loc[cls[i]][0][0]
    best = None
    for (t, v, k, m) in loc[cls[i]]:
        j = i
        while j + 1 < N:
            nxt = [x for x in loc[cls[j + 1]] if x[0] == t and x[1] == v]
            cur = [x for x in loc[cls[j]] if x[0] == t and x[1] == v]
            if nxt and cur and nxt[0][2] == (cur[0][2] + 1) % m: j += 1
            else: break
        if best is None or j > best[1]: best = (v, j, k)
    v, j, k = best
    pieces.append((t0, v, i, j, k))
    i = j + 1
vers = {}; cover = {}
for (t, v, i, j, k) in pieces:
    vers.setdefault(t, set()).add(v)
    m = len(fam["trails"][t]["versions"][v]) // 8
    for u in range(j - i + 1): cover.setdefault(t, []).append((k + u) % m)
ok = all(len(vs) == 1 for vs in vers.values()) and len(vers) == 30 and all(sorted(c) == list(range(len(c))) for c in cover.values())
print("runs", N, "pieces", len(pieces), "visits", sum(1 for a, b in zip(pieces, pieces[1:]) if a[0] != b[0]) + 1, "one version per trail and exact cover:", ok)
for p in pieces: print("trail %2d ver %d runs %4d..%4d (len %3d) start idx %d" % (p[0], p[1], p[2], p[3], p[3] - p[2] + 1, p[4]))
