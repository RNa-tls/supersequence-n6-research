#!/usr/bin/env python3
"""Round 174 -- falsification test of the MASTER <-> external-reduction dictionary.

For every archive word (n = 5..9) we compute, from the external definitions
(Superperm7/CheapCover.lean, Orbit.lean, Structural.lean, read for general n):

  r      := |runStartSet| - HEX       runStartSet = perms not entered by a cost-1 edge
  q      := |chainStartSet|           chainStartSet = perms not entered by a cost-1/2 edge
  p      := #(edges of cost >= 4) + 1
  M      := #distinct F-blocks (tau-orbits) of run starts, m := M - ORB
  k_rot  := #connected components of the rotation graph on touched blocks
            (blocks joined when run starts in the same rotation class lie in them)
  a := k_rot - ORB - m + r,  b := q - k_rot,  eta := p - 1,  D := m + a + b + eta

and from our MASTER layer (r156/r160): G, S, h, H, O, k, Z, B*, t.  Claimed identities
(THEOREM 1 of r174/UNIVERSAL_STRUCTURE_REPORT.md):
  r = G,  q = S + 1,  p = h + 1,  M = O,  m = k,  a + b = Z + B*,  D = t - (H - h).
Also recorded: whether a = Z and b = B* individually (NOT claimed)."""
import glob, gzip, json, os, re, sys
from collections import Counter
from math import factorial
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r160" / "src")); sys.path.insert(0, str(ROOT / "r156" / "src"))
import master160 as M160
import extract156 as X
SPL = Path(sys.argv[1])


def strings(p, n):
    raw = open(p, "rb").read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return [t for t in re.findall(r"[1-9]+", raw.decode("utf-8", "replace")) if len(t) >= factorial(n)]


def external(st, n):
    sel, gaps = st["sel"], st["gaps"]
    N = factorial(n); HEX = N // n; ORB = HEX // (n - 1)
    route = [w for _, w in sel]
    cost1_dest = {route[j + 1] for j in range(N - 1) if gaps[j] == 1}
    cheap_dest = {route[j + 1] for j in range(N - 1) if gaps[j] <= 2}
    run_starts = [w for w in route if w not in cost1_dest]
    r = len(run_starts) - HEX
    q = N - len(cheap_dest)
    p = sum(1 for g in gaps if g >= 4) + 1
    blocks = {w: X.orbrep(w, n) for w in run_starts}
    Mb = len(set(blocks.values()))
    m = Mb - ORB
    # rotation graph: union-find over blocks, join blocks of run starts sharing a class
    parent = {b: b for b in set(blocks.values())}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    byhex = {}
    for w in run_starts:
        byhex.setdefault(X.hexrep(w), []).append(blocks[w])
    for bl in byhex.values():
        for b2 in bl[1:]:
            ra, rb = find(bl[0]), find(b2)
            if ra != rb:
                parent[ra] = rb
    k_rot = len({find(b) for b in parent})
    a = k_rot - ORB - m + r
    b = q - k_rot
    eta = p - 1
    return dict(r=r, q=q, p=p, M=Mb, m=m, k_rot=k_rot, a=a, b=b, eta=eta, D=m + a + b + eta,
                guards=dict(a_le_r=a <= r, r_le_n1m=r <= (n - 1) * m, k_le_M=k_rot <= Mb,
                            k_le_q=k_rot <= q, p_le_q=p <= q, a_nonneg=a >= 0, b_nonneg=b >= 0))


rows = []
tally = Counter()
for n in (5, 6, 7, 8, 9):
    seen = set()
    for f in sorted(glob.glob(str(SPL / "superpermutations" / str(n) / "*"))):
        if not os.path.isfile(f):
            continue
        for s in strings(f, n):
            if len(set(s)) != n or s in seen:
                continue
            seen.add(s)
            try:
                st = X.structure(s, n)
            except Exception:
                tally[(n, "not_cover_or_not_fixedrep")] += 1
                continue
            mm = M160.master(st)
            e = external(st, n)
            ident = dict(r_eq_G=e["r"] == mm["G"], q_eq_S1=e["q"] == mm["S"] + 1,
                         p_eq_h1=e["p"] == mm["h"] + 1, M_eq_O=e["M"] == mm["O"],
                         m_eq_k=e["m"] == mm["k"],
                         ab_eq_ZB=e["a"] + e["b"] == mm["Z"] + mm["Bstar"],
                         D_eq_t_minus=e["D"] == mm["t"] - (mm["H"] - mm["h"]))
            ok = all(ident.values()) and all(e["guards"].values())
            tally[(n, "all_identities_and_guards_hold" if ok else "VIOLATION")] += 1
            tally[(n, "a_eq_Z")] += e["a"] == mm["Z"]
            tally[(n, "D2_pos")] += mm["D2"] > 0
            if not ok and len(rows) < 20:
                rows.append(dict(n=n, L=len(s), ident=ident, guards=e["guards"]))
out = dict(tally={f"{k[0]}:{k[1]}": v for k, v in sorted(tally.items())}, first_violations=rows)
(ROOT / "r174/certs/dictionary_174.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out["tally"], indent=1))
