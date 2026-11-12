#!/usr/bin/env python3
"""Round V -- packings of the 120 loops by images of closed walk types.
 images(type) : all relabelings of the walk (as frozensets of loops, with the rows)
 usage: packing.py TYPES.txt [--lam L] [--maxdens D] ...   (see main)"""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL
PERMS = [dict(zip("012345", p)) for p in itertools.permutations("012345")]
def walk_from(word, x0="012345"):
    rows = []; x = x0
    for ch in word: rows.append((x, int(ch))); x = SL.step(x, int(ch))
    assert x == x0, "not closed"
    return rows
def images(word):
    """distinct images: dict frozenset(loop ids) -> rows (dict state -> v).  Two images with the same loops but
    different rows are kept apart (key = frozenset of (state, v))."""
    base = walk_from(word); out = {}
    for mp in PERMS:
        rows = {"".join(mp[c] for c in x): v for x, v in base}; key = frozenset(rows.items())
        if key not in out: out[key] = (frozenset(SL.LID[SL.canon(x)] for x in rows), rows)
    return list(out.values())
def read_types(path, maxdens=9.0, lam=1.5):
    ts = []
    for l in open(path):
        p = l.split()
        if len(p) < 4: continue
        L, Q, T, w = int(p[0]), int(p[1]), int(p[2]), p[3]
        if (Q + lam * T) / L <= maxdens: ts.append((L, Q, T, w))
    return sorted(set(ts))
if __name__ == "__main__":
    # test: does an image of (466)^4 fit the 12 rowless loops of the public selection?
    pub = SL.read_selection(sys.argv[1]); left = frozenset(SL.LID[l] for l in SL.LOOPS if l not in {SL.canon(x) for x in pub})
    for word in sys.argv[2:]:
        ims = images(word); inside = [im for im in ims if im[0] <= left]
        print(word, "images", len(ims), "inside the 12 rowless loops of the public selection:", len(inside), "meeting them in k loops:", sorted({len(im[0] & left) for im in ims}))
