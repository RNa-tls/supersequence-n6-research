#!/usr/bin/env python3
"""라운드 121 — `(k,F) = (2,1)` 자원 분류 · 무게-4/5 census · 해석적 배제.

세 부분:

  A. 예산을 **제1원리에서** 다시 유도하고 (`P=121, O=26, D=9, L=845+S+H`)
     `(e, x, f_out, H)` 의 **모든** 정수 행을 센다 (숨은 여유 없음).
  B. 무게-4(13개)·무게-5(71개) tail 을 **엔진과 독립으로** 다시 census 한다.
     라운드 118 census 에 오류가 있었으므로 (라운드 120 이 정정) 처음부터 다시 만든다.
  C. 라운드 115 의 사슬 용량표로 **탐색 없이** 죽는 행을 찾는다.

tail 목록: 무게 `w` 의 이음매는 `z = (y[w], ..., y[5], y[pi(0)], ..., y[pi(w-1)])` 이고
`pi` 는 `{0..w-1}` 의 **분해불가(indecomposable)** 순열이다 (분해가능하면 중간 창이
그 자체로 순열이라 순열 하나를 건너뛰게 되어 pass 분해의 이음매가 아니다).
개수는 1, 1, 3, 13, 71, 461 (w = 1..6) 이고 합이 **550** 이다.
"""
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

WORDS = [tuple(p) for p in itertools.permutations(range(6))]
IDX = {w: i for i, w in enumerate(WORDS)}
NW = 720

sig = lambda w: w[1:] + w[:1]
tau = lambda w: (w[1], w[2], w[3], w[4], w[0], w[5])
rho = lambda w: tuple(reversed(w))


def sigk(w, k):
    for _ in range(k % 6):
        w = sig(w)
    return w


def build_geo():
    hexid, orbid, ph = [-1] * NW, [-1] * NW, [-1] * NW
    nh = no = 0
    for i, w in enumerate(WORDS):
        if hexid[i] < 0:
            x = w
            for _ in range(6):
                hexid[IDX[x]] = nh
                x = sig(x)
            nh += 1
        if orbid[i] < 0:
            x = w
            for j in range(5):
                orbid[IDX[x]] = no
                ph[IDX[x]] = j
                x = tau(x)
            no += 1
    assert (nh, no) == (120, 144)
    return hexid, orbid, ph


HEXID, ORBID, ORBPH = build_geo()
HEXOF_ORB = [set() for _ in range(144)]
for i in range(NW):
    HEXOF_ORB[ORBID[i]].add(HEXID[i])


def indecomposable(w):
    """the indecomposable permutations of {0..w-1}, in the engine's generation order."""
    out = []
    for pi in itertools.product(*[range(w)] * w):
        if len(set(pi)) != w:
            continue
        mx, ok = -1, True
        for j in range(w - 1):
            mx = max(mx, pi[j])
            if mx == j:
                ok = False
                break
        if ok:
            out.append(pi)
    return out


def tails(w):
    """weight-w tails as index actions on the exit word."""
    return [tuple(range(w, 6)) + pi for pi in indecomposable(w)]


def omega(a, b):
    for k in range(1, 6):
        if a[k:] == b[:6 - k]:
            return k
    return 6


# ---------------------------------------------------------------- A. resource rows
NTAB = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83, 96, 96, 96,
        103, 103, 103, 103, 120, 120, 120, 120]


def bestseg_table(mmax):
    B = [[0] * len(NTAB) for _ in range(mmax + 1)]
    for m in range(1, mmax + 1):
        for s in range(len(NTAB)):
            B[m][s] = max(NTAB[a] + B[m - 1][s - a] for a in range(s + 1))
    return B


def resource_rows(k=2, F=1):
    O, P = 24 + k, 120 + F
    D = 5 * O - P
    budget = 844 + F                       # L = 844 + F + S + H
    cap = 871 - budget                     # S + H <= cap
    B = bestseg_table(12)
    rows = []
    for e in range(0, 8):
        for x in range(0, 5):
            for f in range(0, 3):
                for H in range(0, 5):
                    if f > 1 + e:                       # Lemma E
                        continue
                    r = O + e
                    S = (r - 1) + x - f
                    if S < 0 or S + H > cap:
                        continue
                    shortfall = 5 * r - P
                    if shortfall < 0:
                        continue
                    # heavy-joint multiset: H = sum (w-3)+, so the compositions of H into
                    # parts >= 1 give the possible (number of heavy joints, weights)
                    comps = []
                    def rec(rem, mx, cur):
                        if rem == 0:
                            comps.append(tuple(cur))
                            return
                        for p in range(min(rem, mx), 0, -1):
                            rec(rem - p, p, cur + [p])
                    rec(H, 3, [])          # a joint of weight w<=6 gives (w-3)+ <= 3
                    for comp in comps:
                        h = len(comp)
                        m = 3 + x + e + h  # segments: start + 2 short passes + x + e + h
                        capacity = B[min(m, 12)][min(shortfall, len(NTAB) - 1)]
                        rows.append(dict(e=e, x=x, f_out=f, H=H,
                                         heavy_weights=[3 + p for p in comp],
                                         n_heavy=h, S=S, SH=S + H, r=r, t=h + 1,
                                         run_shortfall=shortfall, segments=m,
                                         segment_capacity=capacity,
                                         dead_by_capacity=capacity < P))
    return dict(k=k, F=F, O=O, P=P, D=D, L_formula="844 + F + S + H",
                S_formula="(r-1) + x - f_out  with r = O + e",
                SH_cap=cap, derived_bounds={"x_plus_H_le": None}, rows=rows)


# ---------------------------------------------------------------- B. heavy census
def heavy_census(w):
    acts = tails(w)
    rows = {}
    for i, a in enumerate(acts):
        f = lambda q, a=a: tuple(q[j] for j in a)
        wt = {omega(y, f(y)) for y in WORDS}
        intra = {}
        samehex = {}
        phase = {}
        overlap = {}
        for ell in range(6):
            s = h = 0
            ph = Counter()
            ov = Counter()
            for u in WORDS:
                y = sigk(u, ell)
                z = f(y)
                if ORBID[IDX[z]] == ORBID[IDX[u]]:
                    s += 1
                    ph[(ORBPH[IDX[z]] - ORBPH[IDX[u]]) % 5] += 1
                if HEXID[IDX[z]] == HEXID[IDX[u]]:
                    h += 1
                ov[len(HEXOF_ORB[ORBID[IDX[u]]] & HEXOF_ORB[ORBID[IDX[z]]])] += 1
            intra[ell] = s
            samehex[ell] = h
            phase[ell] = {str(kk): v for kk, v in sorted(ph.items())}
            overlap[ell] = {str(kk): v for kk, v in sorted(ov.items())}
        rows[f"W{w}_{i}"] = dict(action=list(a), weights_observed=sorted(wt),
                                 intra_orbit=intra, same_hexagon=samehex,
                                 phase_shift_when_intra=phase,
                                 source_target_hexagon_overlap=overlap)
    classes = {}
    for name, r in rows.items():
        key = (tuple(r["intra_orbit"][e] for e in range(6)),
               tuple(r["same_hexagon"][e] for e in range(6)),
               tuple(sorted(r["source_target_hexagon_overlap"][5].items())))
        classes.setdefault(str(key), []).append(name)
    return dict(weight=w, n_tails=len(acts), per_tail=rows,
                homogeneous_classes={k: v for k, v in classes.items()},
                n_classes=len(classes),
                all_weights_exact=all(r["weights_observed"] == [w] for r in rows.values()),
                intra_orbit_only_at_ell5=all(
                    all(r["intra_orbit"][e] == 0 for e in range(5)) for r in rows.values()),
                never_returns_to_source_hexagon=all(
                    all(r["same_hexagon"][e] == 0 for e in range(6)) for r in rows.values()),
                intra_orbit_at_ell5=sorted(n for n, r in rows.items()
                                           if r["intra_orbit"][5] == NW),
                partially_intra_at_ell5=sorted(n for n, r in rows.items()
                                               if 0 < r["intra_orbit"][5] < NW))


def main():
    tail_counts = {w: len(tails(w)) for w in range(1, 7)}
    rep = dict(round=121, cell=[2, 1],
               tail_catalogue={"counts_by_weight": tail_counts,
                               "total": sum(tail_counts.values())},
               budget=resource_rows(2, 1),
               weight4=heavy_census(4),
               weight5=heavy_census(5))
    b = rep["budget"]
    rows = b["rows"]
    rep["summary"] = dict(
        D=b["D"], O=b["O"], P=b["P"], SH_cap=b["SH_cap"],
        n_subcases=len(rows),
        n_distinct_rows=len({(r["e"], r["x"], r["f_out"], r["H"]) for r in rows}),
        max_H=max(r["H"] for r in rows),
        max_x=max(r["x"] for r in rows),
        max_e=max(r["e"] for r in rows),
        max_x_plus_H=max(r["x"] + r["H"] for r in rows),
        dead_by_capacity=[{kk: r[kk] for kk in ("e", "x", "f_out", "H", "heavy_weights",
                                                "segments", "segment_capacity")}
                          for r in rows if r["dead_by_capacity"]],
        n_dead=sum(r["dead_by_capacity"] for r in rows),
        heavy_weight_multisets_needed=sorted({tuple(r["heavy_weights"]) for r in rows}))
    rep["label"] = "ROUND-121 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED"
    rep["disclaimer"] = "This project has not proved L6 >= 872."
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_f1_k2_budget_121.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep["tail_catalogue"], ensure_ascii=False))
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=1))
    for w in (4, 5):
        c = rep[f"weight{w}"]
        print(f"weight {w}: {c['n_tails']} tails, {c['n_classes']} homogeneous classes, "
              f"weights exact {c['all_weights_exact']}, intra-orbit only at ell=5 "
              f"{c['intra_orbit_only_at_ell5']}, never returns to source hexagon "
              f"{c['never_returns_to_source_hexagon']}")
        print(f"   fully intra-orbit at ell=5: {c['intra_orbit_at_ell5']}")
        print(f"   partially intra at ell=5:   {c['partially_intra_at_ell5']}")


if __name__ == "__main__":
    main()
