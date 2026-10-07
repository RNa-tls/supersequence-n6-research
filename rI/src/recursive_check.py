#!/usr/bin/env python3
"""The classical recursive superpermutation (length sum_{k<=n} k!) is an r = 0 route whose chains are
all full (score sum = ORB, the maximum possible): the user's S(n) := max score is attained by it,
so max score alone does not determine the length (it is the trail count / linking that matters)."""
import sys, os, json, math, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import analyse
def recursive(n):
    if n == 1: return [1]
    prev = recursive(n - 1); m = n - 1
    perms = []; seen = set()
    for i in range(len(prev) - m + 1):
        t = tuple(prev[i:i + m])
        if len(set(t)) == m and t not in seen: seen.add(t); perms.append(t)
    word = []
    for p in perms:
        piece = list(p) + [n] + list(p)
        if not word: word = piece; continue
        k = max(j for j in range(0, len(piece)) if word[len(word) - j:] == piece[:j] or j == 0)
        word += piece[k:]
    return word
for n in range(4, 9):
    w = [x - 1 for x in recursive(n)]
    out, _ = analyse(w, n)
    print(json.dumps(dict(n=n, length=len(w), sum_fact=sum(math.factorial(k) for k in range(1, n + 1)), f=out["f"],
                          score=out["score_sum"], ORB=math.factorial(n - 2), q=out["q"], trails=out["trails"],
                          eta=out["eta"], E5=out["E5"], W=out["W"])))
