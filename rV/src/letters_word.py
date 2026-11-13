#!/usr/bin/env python3
"""Round V -- literal word of a letter-level path of a wrap family: pieces are arcs of the cyclic trail words
(src/fam_letters.py --words), joined with the largest overlap (at most 7).
usage: letters_word.py WORDS.json PATH.json OUT_WORD.txt OUT.json"""
import sys, json, hashlib
words = {int(k): v for k, v in json.load(open(sys.argv[1])).items()}; wit = json.load(open(sys.argv[2]))
w = ""; ev = []
for e in wit["witness"]:
    c = words[e["trail"]]; R = len(c); k = 2 - e["cost"]; s = e["start"]; piece = (c * 3)[s:s + R + 7 - k]
    assert len(set(piece[:8])) == 8 and len(set(piece[-8:])) == 8
    ov = 0
    if w: ov = next((q for q in range(7, 0, -1) if w[-q:] == piece[:q]), 0); assert 5 - ov == e["join"], (5 - ov, e["join"])
    w += piece[ov:]; ev.append(dict(trail=e["trail"], start=s, dropped=k, cost=e["cost"], overlap=ov, piece_letters=len(piece)))
seen = {w[i:i + 8] for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8}
res = dict(length=len(w), J=wit["optimal_J"], length_formula=46149 + wit["optimal_J"], distinct_permutations=len(seen), sha256_with_lf=hashlib.sha256((w + "\n").encode()).hexdigest(), pieces=ev)
assert len(w) == res["length_formula"] and len(seen) == 40320
open(sys.argv[3], "w").write(w + "\n"); json.dump(res, open(sys.argv[4], "w"), indent=1); print({k: v for k, v in res.items() if k != "pieces"})
