#!/usr/bin/env python3
"""Round 147 Phase 6 (part 1) -- INDEPENDENT reconstruction of the chain
searcher's geometry, from string algebra alone.

The C searcher builds its catalogue by enumerating the 720 permutations with a
digit-rank function and comparing memory buffers.  This module rebuilds every
table it uses from plain string operations on the permutations of "123456", with
no reference to the C code's data layout, and compares field by field.

The rules being reconstructed (read off the C source, then re-derived here):

  end(v)      = sigma^{-1}(v) = v[5] + v[0:5].
  gap(v, t)   = least k in 1..5 with end(v)[k:] a prefix of t, else 6.
                (the max-overlap distance from end(v) to t)
  spelling    = end(v) + t[6-gap:]   (length 6 + gap)
  interior    = the windows spelling[o:o+6] for 0 < o < gap that are
                permutations; `hid` is their list.
  gap == 2    no interior permutation           -> the FREE E edge
              one interior permutation, == v    -> type A dirty edge (sigma)
  gap == 3    two interior permutations, the first == v and hex(t) == hex(v)
                                                -> type B dirty edge (sigma^2)
              otherwise a PAID edge, of kind
                120 / 201 / 210  when there is no interior permutation, by the
                    positions of t[3], t[4], t[5] inside end(v)[0:3];
                E_SIGMA          when the single interior permutation is v;
                SIGMA_E          when the single interior permutation x has
                                 t == sigma(x).
  gap >= 4    HEAVY connector, cost gap - 3, excluding t == v and t == end(v).

  hex(v)  = the sigma-rotation class of v (6 rotations, 120 classes)
  orb(v)  = the tau-rotation class (rotate the first five letters, 144 classes)
  phase(v)= which of the five tau-rotations of the class representative v is
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

PERMS = ["".join(p) for p in itertools.permutations("123456")]
IDX = {p: i for i, p in enumerate(PERMS)}
N = len(PERMS)


def sigma(s):
    return s[1:] + s[0]


def tau(s):
    return s[1:-1] + s[0] + s[-1]


def rot_sigma(s):
    out, q = [], s
    for _ in range(6):
        out.append(q)
        q = sigma(q)
    return out


def rot_tau(s):
    out, q = [], s
    for _ in range(5):
        out.append(q)
        q = tau(q)
    return out


def classes():
    hexid, orbid, phase = [None] * N, [None] * N, [None] * N
    hmap, omap = {}, {}
    for p in PERMS:
        rep = min(IDX[x] for x in rot_sigma(p))
        hexid[IDX[p]] = hmap.setdefault(rep, len(hmap))
        orep = min(IDX[x] for x in rot_tau(p))
        orbid[IDX[p]] = omap.setdefault(orep, len(omap))
        base = PERMS[orep]
        ph = [i for i, x in enumerate(rot_tau(base)) if x == p]
        assert len(ph) == 1, (p, ph)
        phase[IDX[p]] = ph[0]
    return hexid, orbid, phase


HEX, ORB, PHASE = classes()


def end(v):
    return v[5] + v[:5]


def gap(e, t):
    for k in range(1, 6):
        if t.startswith(e[k:]):
            return k
    return 6


def catalogue():
    free = [-1] * N
    dA = [-1] * N
    dB = [-1] * N
    paid = [[-1] * 5 for _ in range(N)]
    kind = [[-1] * 5 for _ in range(N)]
    heavy = [[] for _ in range(N)]
    KINDNAME = {0: "120", 1: "201", 2: "210", 3: "E_SIGMA", 4: "SIGMA_E"}
    for vi, v in enumerate(PERMS):
        e = end(v)
        np_ = 0
        for ti, t in enumerate(PERMS):
            g = gap(e, t)
            if g >= 4:
                if t != v and t != e:
                    heavy[vi].append([ti, g - 3])
                continue
            if g not in (2, 3):
                continue
            spell = e + t[6 - g:]
            hid = [IDX[spell[o:o + 6]] for o in range(1, g)
                   if len(set(spell[o:o + 6])) == 6]
            if g == 2:
                if not hid:
                    free[vi] = ti
                elif len(hid) == 1 and hid[0] == vi:
                    dA[vi] = ti
                continue
            # g == 3
            if len(hid) == 2 and hid[0] == vi and HEX[ti] == HEX[vi]:
                dB[vi] = ti
                continue
            k = -1
            if not hid:
                d0 = [e[:3].index(t[3 + j]) if t[3 + j] in e[:3] else -1
                      for j in range(3)]
                code = 100 * d0[0] + 10 * d0[1] + d0[2]
                k = {120: 0, 201: 1, 210: 2}.get(code, -1)
            elif len(hid) == 1 and hid[0] == vi:
                k = 3
            elif len(hid) == 1 and sigma(PERMS[hid[0]]) == t:
                k = 4
            if k < 0:
                continue
            assert np_ < 5, (v, np_)
            paid[vi][np_] = ti
            kind[vi][np_] = k
            np_ += 1
        assert free[vi] >= 0 and dA[vi] >= 0 and dB[vi] >= 0 and np_ == 5, (
            v, free[vi], dA[vi], dB[vi], np_)
        assert HEX[dA[vi]] == HEX[vi] and HEX[dB[vi]] == HEX[vi]
        _ = KINDNAME
    return free, dA, dB, paid, kind, heavy


def main():
    free, dA, dB, paid, kind, heavy = catalogue()
    mine = dict(n=N, words=PERMS, hexid=HEX, orbid=ORB, phase=PHASE,
                freetgt=free, dirtyA=dA, dirtyB=dB, paidtgt=paid,
                paidkind=kind, heavy=heavy)
    ref = json.loads((Path(__file__).resolve().parent.parent /
                      "tables" / "catalogue_C147.json").read_text())
    diffs = []
    for k in mine:
        if k not in ref:
            diffs.append(f"{k}: missing from the C dump")
        elif mine[k] != ref[k]:
            if isinstance(mine[k], list):
                bad = [i for i in range(len(mine[k]))
                       if i < len(ref[k]) and mine[k][i] != ref[k][i]]
                diffs.append(f"{k}: {len(bad)} entries differ, first at "
                             f"{bad[:3]} mine={[mine[k][i] for i in bad[:3]]} "
                             f"C={[ref[k][i] for i in bad[:3]]}")
            else:
                diffs.append(f"{k}: {mine[k]} vs {ref[k]}")
    out = dict(fields=sorted(mine), agree=not diffs, diffs=diffs,
               hexagons=len(set(HEX)), orbits=len(set(ORB)),
               heavy_total=sum(len(h) for h in heavy))
    (Path(__file__).resolve().parent.parent / "certs" /
     "catalogue_agreement_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["agree"] else 1


if __name__ == "__main__":
    sys.exit(main())
