#!/usr/bin/env python3
"""Round P -- build the single-opening word of a trail order (options from the exact fixed-order DP) and
write it in the record format (symbols 1..8, newline).  The word is the greedy overlap concatenation of
the permutation route: each trail piece contributes its runs start, start+1, ... (cyclic), each run being
the 8 left rotations of its first permutation (same convention as rM/src/opening_rebuild.py).
usage: build_word.py FAMILY.json E.npy ORDER(comma list) OUT.txt OUT_DESCRIPTION.json"""
import sys, os, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rO", "src")); sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src"))
import fixed_order as FA

def main():
    fam_p, E_p, ordtxt, out, outd = sys.argv[1:6]
    order = [int(x) for x in ordtxt.split(",")]
    fo = FA.FixedOrder(fam_p, E_p)
    F, ch = fo.F(order, True)
    desc = [[fo.opts[o]["t"], fo.opts[o]["v"], fo.opts[o]["k"], fo.opts[o]["m"]] for o in ch]
    fam = json.load(open(fam_p)); T = {}
    for tr in fam["trails"]:
        for v, s in enumerate(tr["versions"]): T[tr["trail"], v] = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
    route = []
    for t, v, i, ln in desc:
        st = T[t, v]
        for k in range(ln):
            p = st[(i + k) % len(st)]; route += [p[j:] + p[:j] for j in range(8)]
    assert len(route) == 40320 and len(set(route)) == 40320
    word = route[0]
    for x, y in zip(route, route[1:]):
        k = next(k for k in range(1, 9) if k == 8 or x[k:] == y[:8 - k]); word += y[8 - k:]
    data = ("".join(chr(ord(c) + 1) for c in word) + "\n").encode()
    open(out, "wb").write(data)
    json.dump(dict(order=order, F=F, J=77 + F, description=desc, length=len(word), sha256=hashlib.sha256(data).hexdigest()), open(outd, "w"), indent=1)
    print(json.dumps(dict(F=F, J=77 + F, length=len(word), sha256=hashlib.sha256(data).hexdigest())))

if __name__ == "__main__":
    main()
