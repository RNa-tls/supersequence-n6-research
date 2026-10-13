#!/usr/bin/env python3
"""Round L -- anatomy of a superpermutation word as a route of permutations.

Route = permutations in order of first occurrence; edge weight w = position difference.
Runs = maximal blocks joined by weight-1 edges (all inside one rotation class).
p_C = number of runs covering class C; R_extra = sum_C (p_C - 1).
First-principles identity (any word whose every window step is accounted):
    L = n + n! + (n-1)! - 2 + R_extra + sum_{w>=2 edges} (w - 2).
Prints the identity check, R_extra, split classes and the local pattern around each split.
usage: python -I route_anatomy.py n WORDFILE [WORDFILE ...]"""
import sys, math, json, re, gzip
from collections import Counter

def read_words(path, n):
    raw = open(path, "rb").read()
    if raw[:2] == b"\x1f\x8b": raw = gzip.decompress(raw)
    return [t for t in re.findall(r"[1-9]+", raw.decode("utf-8", "replace"))
            if len(t) >= math.factorial(n) and len(set(t)) == n]

def route(word, n):
    seen = set(); out = []; pos = []
    for i in range(len(word) - n + 1):
        t = word[i:i + n]
        if len(set(t)) == n and t not in seen:
            seen.add(t); out.append(t); pos.append(i)
    return out, pos

def canon(t):
    k = t.index(min(t)); return t[k:] + t[:k]

def anatomy(word, n):
    r, pos = route(word, n)
    assert len(r) == math.factorial(n), "not a superpermutation"
    w = [pos[i + 1] - pos[i] for i in range(len(r) - 1)]
    L = len(word)
    runs = []; cur = [0]
    for i, x in enumerate(w):
        if x == 1: cur.append(i + 1)
        else: runs.append(cur); cur = [i + 1]
    runs.append(cur)
    pieces = Counter(canon(r[run[0]]) for run in runs)
    R_extra = sum(v - 1 for v in pieces.values())
    excess = sum(x - 2 for x in w if x >= 2)
    ident = n + math.factorial(n) + math.factorial(n - 1) - 2 + R_extra + excess
    # run-level description: (class, run length, weight of the edge leaving the run)
    rl = []
    for k, run in enumerate(runs):
        out_w = w[run[-1]] if run[-1] < len(w) else None
        rl.append((canon(r[run[0]]), len(run), out_w, r[run[0]], r[run[-1]]))
    return dict(L=L, ident=ident, R_extra=R_extra, excess=excess, runs=rl, pieces=pieces,
                wcount=Counter(w))

if __name__ == "__main__":
    n = int(sys.argv[1])
    for path in sys.argv[2:]:
        for word in read_words(path, n)[:1]:
            a = anatomy(word, n)
            split = {c for c, v in a["pieces"].items() if v > 1}
            print(json.dumps(dict(file=path.split("/")[-1], L=a["L"], identity=a["ident"],
                                  R_extra=a["R_extra"], excess=a["excess"],
                                  weights={str(k): v for k, v in sorted(a["wcount"].items())},
                                  split_classes=len(split),
                                  split_piece_lengths=sorted(Counter(tuple(sorted(rl[1] for rl in a["runs"] if rl[0] == c)) for c in split).items()))))
