#!/usr/bin/env python3
"""라운드 122 — 일반 `(k,F)=(1,1)` 과 역사적 Q2/Area-A 모집단 사이의 **다리**.

세 부분:

  A. `(1,1)` 예산을 제1원리에서 다시 유도하고 모든 정수 행을 센다 (§1).
  B. 6,396 아카이브 상태를 **직접 읽어** 상수를 census 한다 (§2, §3).
  C. `G \\ Q` 를 정확히 특징짓는다 (§5, §11, §12).

`G` := NR6 아래 `F=1, k=1, L<=871` 인 일반 walk 전부.
`Q` := 라운드 92/93c 아카이브의 6,396 상태(그리고 그것이 대표하는 모집단).

**이 스크립트는 Q2 를 다시 돌리지 않는다.** 아카이브를 읽고 일반 예산과 대조할 뿐이다.
"""
from __future__ import annotations

import gzip
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
ARCHIVE = OUT / "rr_port_path_hall_archive" / "states.jsonl.gz"

NTAB = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83, 96, 96, 96,
        103, 103, 103, 103, 120, 120, 120, 120]


def bestseg(mmax):
    B = [[0] * len(NTAB) for _ in range(mmax + 1)]
    for m in range(1, mmax + 1):
        for s in range(len(NTAB)):
            B[m][s] = max(NTAB[a] + B[m - 1][s - a] for a in range(s + 1))
    return B


# ------------------------------------------------------------------ A. budget
def budget(k=1, F=1):
    O, P = 24 + k, 120 + F
    D = 5 * O - P
    cap = 871 - (844 + F)
    B = bestseg(14)
    rows = []
    for e in range(0, 8):
        for x in range(0, 6):
            for f in range(0, 3):
                for H in range(0, 6):
                    if f > 1 + e:                       # Lemma E
                        continue
                    r = O + e
                    S = (r - 1) + x - f
                    if S < 0 or S + H > cap:
                        continue
                    shortfall = 5 * r - P
                    if shortfall < 0:
                        continue
                    comps = []

                    def rec(rem, mx, cur):
                        if rem == 0:
                            comps.append(tuple(cur))
                            return
                        for p in range(min(rem, mx), 0, -1):
                            rec(rem - p, p, cur + [p])
                    rec(H, 3, [])
                    for comp in comps:
                        h = len(comp)
                        m = 3 + x + e + h
                        capacity = B[min(m, 14)][min(shortfall, len(NTAB) - 1)]
                        rows.append(dict(
                            e=e, x=x, f_out=f, H=H, N=e + x - f,
                            heavy_weights=[3 + p for p in comp], n_heavy=h,
                            S=S, SH=S + H, r=r, t=h + 1, run_shortfall=shortfall,
                            segments=m, segment_capacity=capacity,
                            dead_by_capacity=capacity < P))
    return dict(k=k, F=F, O=O, P=P, D=D, SH_cap=cap,
                S_formula="(r-1) + x - f_out  with r = 25 + e  ->  S = 24+e+x-f_out",
                core_inequality="e + x + H <= 2 + f_out   (equivalently N + H <= 2)",
                N_formula="N = S + F - O = e + x - f_out",
                L_in_terms_of_N="L = 869 + N + H   (so L<=871 <=> N+H<=2)",
                rows=rows)


# ---------------------------------------------------------------- B. archive
def archive_census():
    recs = [json.loads(l) for l in gzip.open(ARCHIVE, "rt")]
    header, states = recs[0], recs[1:]
    def c(key):
        return {str(k): v for k, v in sorted(Counter(s[key] for s in states).items())}
    ndef = Counter(s["S"] + s["F"] - s["O"] for s in states)
    dcheck = Counter(s["D"] - (5 * s["O"] - s["P"]) for s in states)
    scheck = Counter(s["S"] - (s["O"] - 1) for s in states)
    bc = Counter(s["b"] + s["c"] for s in states)
    return dict(
        header_states=header.get("states"), n_states=len(states),
        F=c("F"), H=c("H"), P=c("P"), O=c("O"), S=c("S"), K=c("K"),
        roots=c("root"), r_count=c("r"), b=c("b"), c=c("c"),
        Ndef={str(k): v for k, v in sorted(ndef.items())},
        D_equals_5O_minus_P={str(k): v for k, v in sorted(dcheck.items())},
        S_equals_O_minus_1={str(k): v for k, v in sorted(scheck.items())},
        b_plus_c={str(k): v for k, v in sorted(bc.items())},
        invariants=dict(
            all_F_equal_1=all(s["F"] == 1 for s in states),
            all_H_zero=all(s["H"] == 0 for s in states),
            all_Ndef_zero=all(s["S"] + s["F"] - s["O"] == 0 for s in states),
            all_P_in_13_14=all(s["P"] in (13, 14) for s in states),
            all_D_equals_5O_minus_P=all(s["D"] == 5 * s["O"] - s["P"] for s in states),
            all_K_equals_25_minus_O=all(s["K"] == 25 - s["O"] for s in states),
            all_roots_are_short=all(s["root"].startswith("short_ell") for s in states),
            b_plus_c_always_5=all(s["b"] + s["c"] == 5 for s in states)))


# -------------------------------------------------- C. the RR macro alphabet
RR_ALPHABET = {(2, False, False): "Z2", (2, True, True): "Z2abandon",
               (3, False, False): "R", (3, False, True): "Z3"}
KNOWN_OUTSIDE = {(2, True, False): "A2 (U-branch, charge 1)",
                 (3, True, True): "A3 (U-branch, charge 1)",
                 (3, True, False): "J  (J-branch, charge 2)",
                 (2, False, True): "weight-2 into a fresh orbit, no abandonment"}


def alphabet_table():
    rows = []
    for w in (2, 3, 4, 5, 6):
        for ab in (False, True):
            for nw in (False, True):
                key = (w, ab, nw)
                inside = key in RR_ALPHABET
                rows.append(dict(weight=w, abandonment=ab, new_orbit=nw,
                                 name=RR_ALPHABET.get(key, KNOWN_OUTSIDE.get(
                                     key, "heavy" if w >= 4 else "unnamed")),
                                 inside_RR_alphabet=inside,
                                 dS=int(w >= 3), dH=max(w - 3, 0),
                                 dO=int(nw), dN=int(w >= 3) - int(nw)))
    return dict(rows=rows,
                inside=[r["name"] for r in rows if r["inside_RR_alphabet"]],
                outside=[r["name"] for r in rows if not r["inside_RR_alphabet"]],
                n_inside=sum(r["inside_RR_alphabet"] for r in rows),
                n_outside=sum(not r["inside_RR_alphabet"] for r in rows),
                every_heavy_joint_is_outside=all(
                    not r["inside_RR_alphabet"] for r in rows if r["weight"] >= 4))


# ------------------------------------------------------- n = 4 control (S10)
def n4_first_pass_control(maxlen=37):
    """Is 'the first pass is short' implied by F = 1?  Exhaustive n=4 control."""
    perms = [tuple(p) for p in itertools.permutations(range(4))]
    idx = {p: i for i, p in enumerate(perms)}
    s4 = lambda w: w[1:] + w[:1]

    def om4(a, b):
        for k in range(1, 4):
            if a[k:] == b[:4 - k]:
                return k
        return 4

    W = [[om4(a, b) for b in perms] for a in perms]
    out = []

    def dfs(cur, used, seq, total):
        if len(seq) == 24:
            out.append((4 + total, tuple(seq)))
            return
        if 4 + total + (24 - len(seq)) > maxlen:
            return
        for j in range(24):
            if used >> j & 1:
                continue
            w = W[cur][j]
            if 4 + total + w + (24 - len(seq) - 1) > maxlen:
                continue
            seq.append(j)
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    dfs(0, 1, [0], 0)
    stat = Counter()
    for L, seq in out:
        om = [W[seq[i]][seq[i + 1]] for i in range(len(seq) - 1)]
        lens, cur = [], 1
        for w in om:
            if w >= 2:
                lens.append(cur)
                cur = 1
            else:
                cur += 1
        lens.append(cur)
        F = len(lens) - 6
        if F != 1:
            continue
        stat["F1_walks"] += 1
        stat["first_pass_short" if lens[0] < 4 else "first_pass_full"] += 1
        stat["last_pass_short" if lens[-1] < 4 else "last_pass_full"] += 1
        if lens[0] == 4 and lens[-1] == 4:
            stat["both_ends_full"] += 1
    return dict(maxlen=maxlen, walks_scanned=len(out), **stat)


def main():
    bud = budget()
    arch = archive_census()
    alph = alphabet_table()
    ctrl = n4_first_pass_control()
    rows = bud["rows"]
    rep = dict(
        round=122, cell=[1, 1],
        budget=bud, archive=arch, rr_alphabet=alph, n4_first_pass_control=ctrl,
        summary=dict(
            n_subcases=len(rows),
            n_distinct_rows=len({(r["e"], r["x"], r["f_out"], r["H"]) for r in rows}),
            n_dead=sum(r["dead_by_capacity"] for r in rows),
            n_live_subcases=sum(not r["dead_by_capacity"] for r in rows),
            n_live_rows=len({(r["e"], r["x"], r["f_out"], r["H"]) for r in rows
                             if not r["dead_by_capacity"]}),
            max_H=max(r["H"] for r in rows), max_x=max(r["x"] for r in rows),
            max_e=max(r["e"] for r in rows),
            max_x_plus_H=max(r["x"] + r["H"] for r in rows),
            heavy_multisets=sorted({tuple(r["heavy_weights"]) for r in rows}),
            rows_with_H_ge_1=len({(r["e"], r["x"], r["f_out"], r["H"]) for r in rows
                                  if r["H"] >= 1 and not r["dead_by_capacity"]}),
            off_by_one=dict(
                generic_requirement="N + H <= 2   (L <= 871)",
                historical_final_target="Ndef + H <= 3   (L <= 872)",
                relation="the Q2 slab is one length shell WIDER, so it is a superset "
                         "in the resource direction - favourable, never a gap")),
        label="ROUND-122 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        disclaimer="This project has not proved L6 >= 872.")
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_f1_k1_bridge_122.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=1))
    print("\narchive invariants:", json.dumps(arch["invariants"], ensure_ascii=False))
    print("archive roots:", json.dumps(arch["roots"], ensure_ascii=False))
    print("archive P:", json.dumps(arch["P"], ensure_ascii=False))
    print("\nRR alphabet inside:", alph["inside"])
    print("RR alphabet outside:", alph["outside"])
    print("\nn=4 control:", json.dumps(ctrl, ensure_ascii=False))


if __name__ == "__main__":
    main()
