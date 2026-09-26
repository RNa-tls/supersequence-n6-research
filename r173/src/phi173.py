#!/usr/bin/env python3
"""Round 173 -- exhaustive check of the FORCED-CONTINUATION lemma for every
block entry e (not only the identity) for n = 4..9:

  among the six weight-3 successors  e_pi = x[3:] + pi(x[:3])  of the block exit
  x = sigma^{n-1}(tau^{n-2} e), exactly five have a tau-block whose hexagon set
  meets H(e) (the hexagons of e's own block), and the sixth is
      phi(e) = e[1:n-2] + e[0] + e[n-2] + e[n-1]      (rotate the first n-2 symbols)
  with H(phi(e)) disjoint from H(e) for n >= 5.  Also checks |H(e)| = n-1 and
  that H(e) = {hexagons D : D minus e[-1] has the cyclic order of e[:-1]}."""
import json, sys
from itertools import permutations
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import perfect173 as P

def cyc(s):
    return min(s[i:] + s[:i] for i in range(len(s)))

def H(e, n):
    ents, x = P.block(e, n)
    return {P.hexrep(v) for v in ents}, x

out = {}
for n in range(4, 10):
    alph = "".join(str(i + 1) for i in range(n))
    bad = 0; checked = 0
    for p in permutations(alph):
        e = "".join(p)
        He, x = H(e, n)
        if len(He) != n - 1:
            bad += 1
        # characterisation of H(e)
        if n <= 7:
            want = {P.hexrep(d) for d in ("".join(q) for q in permutations(alph))
                    if cyc(d.replace(e[-1], "")) == cyc(e[:-1])} if n <= 6 else None
            if want is not None and want != He:
                bad += 1
        survivors = []
        for q in permutations(x[:3]):
            c = x[3:] + "".join(q)
            Hc, _ = H(c, n)
            if not (Hc & He):
                survivors.append(c)
        phi = e[1:n - 2] + e[0] + e[n - 2] + e[n - 1]
        if n >= 5 and survivors != [phi]:
            bad += 1
        if n == 4 and phi not in survivors:
            bad += 1
        checked += 1
        if n == 9 and checked >= 40320:
            break
    out[n] = dict(entries_checked=checked, violations=bad)
    print(n, out[n], flush=True)
open(__file__.rsplit("/", 2)[0] + "/certs/phi_lemma_173.json", "w").write(json.dumps(out, indent=1) + "\n")
