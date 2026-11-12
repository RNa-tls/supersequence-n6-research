#!/usr/bin/env python3
"""Round V -- canonical form of a word under renaming of the symbols and reversal: the symbols are renamed in order of
first occurrence; the smaller of the two strings (word, reversed word) is the canonical form.
usage: word_canon.py WORD.txt ...   prints sha256 of the canonical forms and which words are equivalent"""
import sys, hashlib, json
def ren(w):
    m = {}; out = []
    for ch in w:
        if ch not in m: m[ch] = str(len(m))
        out.append(m[ch])
    return "".join(out)
res = {}
for p in sys.argv[1:]:
    w = "".join(open(p).read().split()); c = min(ren(w), ren(w[::-1])); res[p] = hashlib.sha256(c.encode()).hexdigest()
classes = {}
for p, h in res.items(): classes.setdefault(h, []).append(p)
print(json.dumps(dict(canonical_sha256=res, classes=list(classes.values())), indent=1))
