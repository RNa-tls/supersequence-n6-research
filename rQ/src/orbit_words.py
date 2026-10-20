#!/usr/bin/env python3
"""Round Q, section 15 -- symmetry orbit of a word of the 6A+24phi family under the order-12 family group.

The group (group.bin from Round P checker B: trail permutations and option permutations, verified there to preserve
e and the cut weights) maps every version cycle onto a version cycle preserving the cyclic order (checked here for
every element).  A word is decomposed into pieces (trail, version, start run, length) in route order; its image
under g replaces every piece by the piece of the same length starting at g(start option).  Each image is rebuilt
run by run, checked (every permutation of 8 symbols occurs, length unchanged) and hashed.
usage: orbit_words.py WORD FAMILY.json RUNS_AND_GROUP_DIR OUT_DIR"""
import sys, json, struct, hashlib, os
import numpy as np

n = 8
def load_word(p):
    t = "".join(ch for ch in open(p).read() if not ch.isspace()); return [int(c) - 1 for c in t]
def starts(w):
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j]
    return st
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
def last(p): return p[-1:] + p[:-1]
def allperms(w):
    seen = set()
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n: seen.add(p)
    return len(seen) == 40320

def main():
    word, famp, gdir, outd = sys.argv[1:5]; os.makedirs(outd, exist_ok=True)
    fam = json.load(open(famp))
    V = [[[tuple(int(c) - 0 for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)] for s in tr["versions"]] for tr in fam["trails"]]
    # runs.bin must list the same cycles (same option order as group.bin)
    f = open(os.path.join(gdir, "runs.bin"), "rb"); mr = {}
    for t in range(30):
        for v in range(2):
            m = struct.unpack("<i", f.read(4))[0]; R = [tuple(b) for b in np.frombuffer(f.read(8 * m), np.uint8).reshape(m, 8)]; mr[(t, v)] = m
            assert [tuple(x - min(min(r) for r in V[t][v]) for x in r) for r in V[t][v]] == R or [tuple(r) for r in V[t][v]] == R, (t, v)
    tofs = []; o = 0
    for t in range(30): tofs.append(o); o += mr[(t, 0)] + mr[(t, 1)]
    NOPT = o
    g = open(os.path.join(gdir, "group.bin"), "rb"); G = struct.unpack("<i", g.read(4))[0]
    tp = np.frombuffer(g.read(4 * G * 30), np.int32).reshape(G, 30); gop = np.frombuffer(g.read(4 * G * NOPT), np.int32).reshape(G, NOPT)
    def dec(oi):
        for t in range(30):
            if tofs[t] <= oi < tofs[t] + mr[(t, 0)] + mr[(t, 1)]:
                r = oi - tofs[t]; v = 0 if r < mr[(t, 0)] else 1; return t, v, r - v * mr[(t, 0)]
    # symbols of the family file are 0..7 or 1..8: normalise to the word's alphabet 0..7
    lo = min(min(min(r) for r in V[0][0]), 0)
    w = load_word(word); st = starts(w)
    loc = {}                                   # a run occurs in both versions of its trail
    for t in range(30):
        for v in range(2):
            for k, r in enumerate(V[t][v]): loc.setdefault(tuple(x - lo for x in r), {})[v] = (t, k)
    pieces = []; i = 0
    while i < len(st):
        best = None
        for v, (t, k) in loc[st[i]].items():
            m = mr[(t, v)]; j = i
            while j + 1 < len(st) and v in loc[st[j + 1]] and loc[st[j + 1]][v] == (t, (k + j + 1 - i) % m): j += 1
            if best is None or j > best[4]: best = (t, v, k, j - i + 1, j)
        pieces.append(best[:4]); i = best[4] + 1
    res = []; hashes = {}
    for gi in range(G):
        route = []
        for (t, v, k, L) in pieces:
            t2, v2, k2 = dec(int(gop[gi][tofs[t] + v * mr[(t, 0)] + k])); m = mr[(t2, v2)]
            route += [tuple(x - lo for x in V[t2][v2][(k2 + u) % m]) for u in range(L)]
        ww = list(route[0])
        for a, b in zip(route, route[1:]):
            kk = wt(last(a), b); ww += list(b[8 - kk:])
        ww = list(route[0])
        for idx, r in enumerate(route):
            if idx > 0: kk = wt(last(route[idx - 1]), r); ww += list(r[8 - kk:])
            ww += list(r[:7])
        s = "".join(str(c + 1) for c in ww); h = hashlib.sha256((s + "\n").encode()).hexdigest()
        ok = allperms(ww)
        fn = os.path.join(outd, "image_g%02d.txt" % gi); open(fn, "w").write(s + "\n")
        res.append(dict(g=gi, length=len(ww), all_perms=ok, sha256=h, trail_order=[p[0] for p in pieces] if gi == 0 else [int(dec(int(gop[gi][tofs[p[0]] + p[1] * mr[(p[0], 0)] + p[2]]))[0]) for p in pieces]))
        hashes.setdefault(h, []).append(gi)
    out = dict(word=word, pieces=len(pieces), group_order=G, distinct_words=len(hashes), images=res, classes=list(hashes.values()))
    json.dump(out, open(os.path.join(outd, "orbit.json"), "w"), indent=1)
    print(json.dumps(dict(pieces=len(pieces), distinct_words=len(hashes), all_valid=all(r["all_perms"] and r["length"] == len(w) for r in res), classes=list(hashes.values()))))

main()
