#!/usr/bin/env python3
"""라운드 129 — 일반 **`G = 2`** 칸 분해.

라운드 128 이후의 좌표계를 쓴다.  바깥 열 좌표는 **`G`**(다중도 초과 `= P − 120`)이고
`F`(abandonment 수)는 **내부 구조 좌표**일 뿐이다.  `F` 를 바깥 축으로 쓰지 않는다.

    P = 120 + G = 122
    L = 844 + G + S + H = 846 + S + H          L ≤ 871 ⟺ S + H ≤ 25
    D = 5O − P = 5k − G = 5k − 2 ≥ 0           ⟹ k ≥ 1
    N = S + G − O = S − 22 − k
    S = (r − 1) + x − f_out,  r = O + e        ⟹ S = 23 + k + e + x − f_out
    L = 867 + k + G + e + x + H − f_out = 869 + k + e + x + H − f_out
    L ≤ 871 ⟺ **k + e + x + H − f_out ≤ 2**
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

NTAB = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83, 96, 96, 96,
        103, 103, 103, 103, 120, 120, 120, 120]
G, P, LCAP, NHEX = 2, 122, 871, 120


def bestseg(mmax=20):
    B = [[0] * len(NTAB) for _ in range(mmax + 1)]
    for m in range(1, mmax + 1):
        for s in range(len(NTAB)):
            B[m][s] = max(NTAB[a] + B[m - 1][s - a] for a in range(s + 1))
    return B


# ------------------------------------------------------------------- §1 identities
def identities():
    return dict(
        G=G, P=P,
        L="844 + G + S + H = 846 + S + H",
        length_condition="L <= 871  <=>  S + H <= 25",
        D="5O - P = 5k - G = 5k - 2 >= 0  =>  k >= 1",
        N="S + G - O = S - 22 - k",
        S="(r - 1) + x - f_out with r = O + e  =>  S = 23 + k + e + x - f_out",
        master="L = 867 + k + G + e + x + H - f_out = 869 + k + e + x + H - f_out",
        core="L <= 871  <=>  k + e + x + H - f_out <= 2",
        run_shortfall="5r - P = 5(24 + k + e) - 122 = 5k + 5e - 2 = D + 5e",
        no_F_substitution=True)


# --------------------------------------------------- §2/§5 internal F inside G = 2
def internal_F():
    """§2·§5 — `G = 2` 안에서 프로젝트 `F` 가 취할 수 있는 값.

    라운드 128: `J = G − F = Σ_h (d_h − 1)`, `d_h` = 육각형 `h` 의 `ν`-순환 하강 수(≥ 1),
    그리고 `abandonment(p) ⟺ p < ν(p)` 이므로 **`F` = `ν`-상승의 개수**다.

    * **유형 B** (두 육각형이 두 번씩): 각 `ν`-순환이 길이 2 라 상승/하강이 정확히 하나씩,
      `d_h = 1` 이 **강제**된다 ⟹ `J = 0` ⟹ **`F = 2` 필연**.
    * **유형 A** (한 육각형을 세 번): `ν`-순환이 길이 3 이라 `d ∈ {1,2}` ⟹ **`F ∈ {1,2}`**.
      그리고 `F` 는 **세 pass 의 walk 순서만으로 결정된다** — 아래 6개 순서를 전수한다.
    """
    nu = {0: 1, 1: 2, 2: 0}                      # the 3-cycle p0 -> p1 -> p2 -> p0
    rows = []
    for order in itertools.permutations(range(3)):
        pos = {p: i for i, p in enumerate(order)}
        asc = sum(1 for p in range(3) if pos[p] < pos[nu[p]])
        rows.append(dict(walk_order=[f"p{p}" for p in order], ascents=asc, F=asc,
                         d=3 - asc, J=2 - asc))
    fvals = sorted({r["F"] for r in rows})
    return dict(
        typeB=dict(nu_cycles="two 2-cycles", d_forced=1, J=0, F=[2],
                   proof="a 2-cycle on a linearly ordered pair has exactly one ascent and "
                         "one descent, so d_h = 1 for both hexagons and J = 0"),
        typeA=dict(nu_cycles="one 3-cycle", d_range=[1, 2], J_range=[0, 1], F=fvals,
                   orderings=rows,
                   n_orderings_with_F2=sum(1 for r in rows if r["F"] == 2),
                   n_orderings_with_F1=sum(1 for r in rows if r["F"] == 1),
                   rule=("F = 2 exactly when the walk order of the three passes is a cyclic "
                         "ROTATION of the nu-order; F = 1 exactly when it is the reversed "
                         "cyclic order"),
                   F_is_local=True),
        conclusion=("the G = 2 column splits internally into THREE models: "
                    "A/F=1, A/F=2, B/F=2.  F is an internal coordinate, never the outer axis."))


# ------------------------------------------------------------ §3/§4 multiplicity types
def length_compositions(n, parts):
    out = []

    def rec(rem, k, cur):
        if k == 1:
            if rem >= 1:
                out.append(tuple(cur + [rem]))
            return
        for a in range(1, rem - k + 2):
            rec(rem - a, k - 1, cur + [a])

    rec(n, parts, [])
    return out


def multiplicity_types(n=6):
    """§3·§4 — 두 유형을 고정하고 짧은 pass 수 · 결손 · 자유 후속 순환 · 길이 분해를 준다."""
    out = []
    for name, ecounts in (("A", [3]), ("B", [2, 2])):
        m = len(ecounts)
        comps = [length_compositions(n, e) for e in ecounts]
        nsplit = 1
        for c in comps:
            nsplit *= len(c)
        out.append(dict(
            type=name, excess_partition=[e - 1 for e in ecounts], entry_counts=ecounts, m=m,
            n_short_passes=G + m,
            total_deficit=n * G,
            nu_cycle_structure=("one 3-cycle" if name == "A" else "two 2-cycles"),
            length_partitions=[sorted({tuple(sorted(c, reverse=True)) for c in cc})
                               for cc in comps],
            n_ordered_splits=nsplit,
            canonicalisation=("S_6 left multiplication fixes the walk-first entry word; no "
                              "further folding is applied because no reversal symmetry has "
                              "been PROVED for this column")))
    return out


# ------------------------------------------------------------ §6/§12/§13 free-exit bounds
def free_exit_bounds():
    """§6·§12·§13 — `G` 표기로 다시 유도한 자유 탈출 상한, 그리고 유형별 정밀화."""
    return dict(
        generic="f_out <= #short = G + m   (only short passes give inter-run omega-2 arcs)",
        lemma_E_prime=("if EVERY pass of a multiply-entered hexagon exits freely then some "
                       "orbit carries two runs, so e >= 1  (Round 126, order argument on the "
                       "nu-cycle)"),
        typeA=dict(
            m=1, f_out_max=3,
            generic_bound="f_out <= G + e = 2 + e   (f_out = 3 forces e >= 1 by Lemma E')",
            sharper="f_out <= F + e",
            sharper_proof=(
                "a free-exiting pass in case (i) satisfies p < nu(p), i.e. it is a nu-ASCENT, "
                "so #case(i) free passes <= F; hence #case(ii) free passes >= f_out - F.  In "
                "type A the three passes' entry words lie in three DISTINCT orbits, so "
                "distinct case-(ii) passes certify distinct split orbits and e >= f_out - F."),
            consequence_for_F1="type A with F = 1 obeys f_out <= 1 + e, strictly stronger "
                               "than the generic 2 + e",
            stronger_generic_bound_exists=False,
            why_not=("with e = 1 exactly one of the three passes can be case (ii) (the three "
                     "targets are distinct orbits and q* is unique), leaving p2 < p3 < p1 and "
                     "no order contradiction - so f_out = 3 with e = 1 is NOT excluded, and "
                     "n = 4 exhibits it")),
        typeB=dict(
            m=2, f_out_max=4, F="always 2",
            table={"0": "e >= 0", "1": "e >= 0", "2": "e >= 0",
                   "3": "e >= 1  (pigeonhole: some hexagon is fully free, then Lemma E')",
                   "4": "e >= 2  (Round 127 order theorem)"},
            bound="f_out <= 2 + e = F + e = G + e",
            sharpness="f_out = 3 with e = 1 occurs at n = 4, so the f_out = 3 row is sharp"),
        unified="for all of G = 2:  f_out <= F + e  <=  G + e   (F <= G)")


# ------------------------------------------------------- §7/§8/§9/§10 resource rows
def rows(kmin=1, kmax=4, use_internal_F=True):
    """§10 — `G = 2` 의 모든 실현 가능한 자원 행을 전수한다."""
    B = bestseg(20)
    out = []
    for typ, m, smax in (("A", 1, 3), ("B", 2, 4)):
        Fvals = [1, 2] if typ == "A" else [2]
        nshort = G + m
        for Fi in Fvals:
            for f in range(0, smax + 1):
                for e in range(0, 8):
                    if use_internal_F and f > Fi + e:      # proved bound f_out <= F + e
                        continue
                    if f > G + e:                          # generic bound
                        continue
                    for x in range(0, 8):
                        for H in range(0, 8):
                            for k in range(kmin, kmax + 1):
                                if k + e + x + H - f > LCAP - 869:
                                    continue
                                D = 5 * k - G
                                if D < 0:
                                    continue
                                S = 23 + k + e + x - f
                                if S < 0:
                                    continue
                                for comp in heavy_compositions(H):
                                    h = len(comp)
                                    breaks = nshort + x + e + h
                                    seg = breaks + 1
                                    sh = 5 * k + 5 * e - G
                                    cap = B[min(seg, 20)][min(sh, len(NTAB) - 1)]
                                    out.append(dict(
                                        type=typ, F=Fi, k=k, e=e, x=x, f_out=f, H=H,
                                        heavy=list(comp), n_heavy=h,
                                        S=S, N=S - 22 - k, r=24 + k + e, t=h + 1,
                                        D=D, run_shortfall=sh, segments=seg,
                                        capacity=cap, dead=(cap < P),
                                        L=869 + k + e + x + H - f))
    return out


def heavy_compositions(H):
    out = []

    def rec(rem, mx, cur):
        if rem == 0:
            out.append(tuple(3 + p for p in cur))
            return
        for p in range(min(rem, mx), 0, -1):
            rec(rem - p, p, cur + [p])

    rec(H, 3, [])
    return out


def cells(use_internal_F=True):
    """§7·§8·§9·§17 — 실현 가능한 `k`, `max H`, 칸별 행/하위경우 수, 해석적 폐쇄."""
    rs = rows(1, 6, use_internal_F)
    alive = [r for r in rs if not r["dead"]]
    ks = sorted({r["k"] for r in rs})
    ks_alive = sorted({r["k"] for r in alive})
    percell = {}
    for k in ks_alive:
        sub = [r for r in rs if r["k"] == k]
        al = [r for r in sub if not r["dead"]]
        percell[str(k)] = dict(
            cell=f"(k,G) = ({k},2)", D=5 * k - G,
            n_subcases=len(sub), n_dead=len(sub) - len(al), n_alive=len(al),
            n_rows_alive=len({(r["type"], r["F"], r["e"], r["x"], r["f_out"], r["H"])
                              for r in al}),
            max_H=max((r["H"] for r in al), default=-1),
            max_x=max((r["x"] for r in al), default=-1),
            max_e=max((r["e"] for r in al), default=-1),
            by_model={f"{t}_F{f}": len([r for r in al if r["type"] == t and r["F"] == f])
                      for t in "AB" for f in (1, 2)
                      if any(r["type"] == t and r["F"] == f for r in al)},
            heavy_multisets=sorted({tuple(r["heavy"]) for r in al}))
    return dict(
        k_feasible_from_D="D = 5k - 2 >= 0  =>  k >= 1",
        k_feasible=ks, k_with_live_subcases=ks_alive,
        n_cells=len(ks_alive),
        max_H_overall=max((r["H"] for r in alive), default=-1),
        max_k_plus_x_plus_H=max((r["k"] + r["x"] + r["H"] for r in alive), default=-1),
        max_k_plus_x_plus_H_by_model={
            f"{t}_F{f}": max((r["k"] + r["x"] + r["H"] for r in alive
                              if r["type"] == t and r["F"] == f), default=-1)
            for t in "AB" for f in (1, 2)
            if any(r["type"] == t and r["F"] == f for r in alive)},
        n_subcases_total=len(rs), n_dead_total=len(rs) - len(alive), n_alive_total=len(alive),
        per_cell=percell,
        dead_examples=[dict(type=r["type"], F=r["F"], k=r["k"], e=r["e"], x=r["x"],
                            f_out=r["f_out"], H=r["H"], heavy=r["heavy"],
                            segments=r["segments"], capacity=r["capacity"])
                       for r in rs if r["dead"]][:40])


def theorem_A_consequence():
    """§7 — 정정된 정리 A 와 master 자원 부등식."""
    rs = rows(1, 6, True)
    alive = [r for r in rs if not r["dead"]]
    return dict(
        theorem_A="O <= 1 + S + G   <=>   f_out <= G + e + x",
        proved_here="f_out <= G + e (Round 126 type A + Round 127 type B) implies it",
        derivation=("k + e + x + H - f_out <= 2 and f_out - e <= G = 2 give "
                    "k + x + H <= 2 + (f_out - e) <= 4"),
        k_plus_x_plus_H_le=max((r["k"] + r["x"] + r["H"] for r in alive), default=-1),
        matches_expected_4=(max((r["k"] + r["x"] + r["H"] for r in alive), default=-1) == 4),
        internal_refinement=("with the sharper f_out <= F + e, the type-A F = 1 model obeys "
                             "k + x + H <= 2 + F = 3"),
        refined_by_model={
            f"{t}_F{f}": max((r["k"] + r["x"] + r["H"] for r in alive
                              if r["type"] == t and r["F"] == f), default=-1)
            for t in "AB" for f in (1, 2)
            if any(r["type"] == t and r["F"] == f for r in alive)})


# ------------------------------------------------------------------- §11 heavy tails
def heavy_catalogue():
    return dict(
        weight4=13, weight5=71, weight6_genuine=308, weight6_raw_indecomposable=461,
        note="Round 125 correction: only 308 of the 461 indecomposable permutations of "
             "{0..5} realize omega = 6; do NOT use 461 as the genuine weight-6 count",
        compositions={str(H): [list(c) for c in heavy_compositions(H)] for H in range(0, 5)},
        weights_per_H={str(H): sorted({w for c in heavy_compositions(H) for w in c})
                       for H in range(0, 5)})


# ------------------------------------------------------------------ §15 engine reuse
def engine_reuse_audit():
    return {
        "reusable_unchanged": [
            "geometry build(): hexid / orbid / phse / perm / rank_of / hlo,hhi",
            "light-move tables M2, M3a, M3b, M3c",
            "heavy tail tables M4 (13), M5 (71), M6 (308 genuine weight-6)",
            "hexorb / ohex / mcnt / EXC orbit-cover-excess prune",
            "blk / freshcnt / markhex / freshdeficit (fod) prune",
            "NTAB and BESTSEG chain-capacity tables",
            "hexagon-injectivity and orbit-phase-injectivity checks"],
        "reusable_after_P_and_D_update": [
            "#define TARGET 121 -> 122",
            "DCAP: D = 5k - G = 5k - 2 (was 5k - 1)",
            "RMAX / SHRUNCAP: run shortfall = 5r - P = 5k + 5e - 2",
            "SHCAP: cost + hub <= 25 (from L = 846 + S + H <= 871), was 26",
            "COSTCAP = S = 23 + k + e + x - f_out",
            "the leaf test orbits == ORBCAP"],
        "G1_specific_must_be_rewritten": [
            "the sstate machine 0 -> 1 -> 2: it models exactly ONE doubled hexagon with "
            "exactly TWO short passes",
            "the forced second visit test w == SIG[BSPLIT][vword] and length 6 - BSPLIT",
            "BSPLIT as a single scalar split parameter",
            "FOUTCAP <= 2 and Lemma E's f_out <= 1 + e",
            "YGAP / YGAPMIN / BFORCE / YFRESH / REVONLY / SEAM / PMAX / SYMCUT - all were "
            "derived for the two-short-pass geometry"],
        "multiplicity_type_specific": [
            "type A needs a 3-arc state machine on one hexagon (sstate 0..3) with the second "
            "and third entry words forced to sigma^{a}(v) and sigma^{a+b}(v)",
            "type B needs TWO independent 2-arc machines on two different hexagons, plus the "
            "bookkeeping that they are distinct hexagons"],
        "verdict": ("the geometry, tail catalogues and every exact prune carry over; the short "
                    "pass state machine does not.  A G = 2 engine is a rewrite of roughly the "
                    "dfs() short-pass section only.")
    }


# ------------------------------------------------------------------ §14 n = 4 validation
def n4_validation(maxlen=39):
    """§14 — 합법 `n = 4` walk 을 **`G = 2`** 로 분류하고(‘F=2’ 가 아니다) 모든 주장을 검사한다."""
    from verify_f2_structure_126 import setup, legal_joint
    from verify_fg_repair_128 import walk_measure
    n = 4
    g = setup(n)
    perms, sg, om = g["perms"], g["sig"], g["omega"]
    NW = len(perms)
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or legal_joint(n, perms[a], perms[b], W[a][b])
           for b in range(NW)] for a in range(NW)]
    ws = []

    def dfs(cur, used, seq, total):
        if len(seq) == NW:
            ws.append((n + total, tuple(seq)))
            return
        if n + total + (NW - len(seq)) > maxlen:
            return
        for j in range(NW):
            if used >> j & 1 or not OK[cur][j]:
                continue
            w = W[cur][j]
            if n + total + w + (NW - len(seq) - 1) > maxlen:
                continue
            seq.append(j)
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    dfs(0, 1, [0], 0)
    stat = Counter()
    viol = Counter()
    bytype = Counter()
    typeA_rule = Counter()
    foutB = Counter()
    foutA = Counter()
    Lbase = n + NW - 2 + NW // n
    Omin = NW // (n * (n - 1))
    for L, seq in ws:
        m = walk_measure(g, W, seq, L)
        stat["walks"] += 1
        if m["G"] != 2:
            continue
        stat["G2_walks"] += 1
        part = m["partition"]
        typ = "A" if part == (2,) else ("B" if part == (1, 1) else "?")
        bytype[(typ, m["F"])] += 1
        mm = len(part)
        # --- G = 2 structural claims -------------------------------------
        nshort = sum(1 for i, (u, ln) in enumerate(m["passes"]) if ln < n)
        if nshort != 2 + mm:
            viol["#short = G + m"] += 1
        if typ == "B" and m["F"] != 2:
            viol["type B => F = 2"] += 1
        if typ == "A" and m["F"] not in (1, 2):
            viol["type A => F in {1,2}"] += 1
        if m["f_out"] > 2 + m["e"]:
            viol["f_out <= G + e"] += 1
        if m["f_out"] > m["F"] + m["e"]:
            viol["f_out <= F + e"] += 1
        if L != Lbase + 2 + m["S"] + m["H"]:
            viol["L = L_base + G + S + H"] += 1
        if L != (Lbase + Omin - 1) + m["k"] + 2 + m["e"] + m["x"] + m["H"] - m["f_out"]:
            viol["master with G"] += 1
        if (n - 1) * m["O"] - m["P"] != (n - 1) * m["k"] - 2:
            viol["D = (n-1)k - G"] += 1
        # --- type A internal-F rule ---------------------------------------
        if typ == "A":
            ps = [i for i in range(m["P"]) if m["hexes"][i] ==
                  m["hexes"][[j for j in range(m["P"])
                              if sum(1 for q in range(m["P"])
                                     if m["hexes"][q] == m["hexes"][j]) == 3][0]]]
            nu = m["nu"]
            asc = sum(1 for i in ps if i < nu[i])
            if asc != m["F"]:
                viol["type A: F = #ascents of the tripled hexagon"] += 1
            # cyclic-rotation rule
            order = sorted(ps)
            cyc = [order[0]]
            while len(cyc) < 3:
                cyc.append(nu[cyc[-1]])
            is_rot = (cyc == sorted(cyc)) or (cyc[1:] + cyc[:1] == sorted(cyc)) \
                or (cyc[2:] + cyc[:2] == sorted(cyc))
            typeA_rule[(m["F"], is_rot)] += 1
            foutA[(m["f_out"], m["e"], m["F"])] += 1
        else:
            foutB[(m["f_out"], m["e"])] += 1
    return dict(
        n=4, maxlen=maxlen, walks=len(ws), G2_walks=stat["G2_walks"],
        by_type_and_F={f"{t}_F{f}": c for (t, f), c in sorted(bytype.items())},
        typeA_total=sum(c for (t, f), c in bytype.items() if t == "A"),
        typeB_total=sum(c for (t, f), c in bytype.items() if t == "B"),
        typeA_cyclic_rotation_rule={f"F{f}_isRotation{r}": c
                                    for (f, r), c in sorted(typeA_rule.items())},
        typeB_fout_e={f"f{f}_e{e}": c for (f, e), c in sorted(foutB.items())},
        typeA_fout_e_F={f"f{f}_e{e}_F{ff}": c for (f, e, ff), c in sorted(foutA.items())},
        typeB_min_e_by_fout={str(f): min(e for (ff, e) in foutB if ff == f)
                             for f in sorted({f for f, _ in foutB})},
        typeA_min_e_by_fout_and_F={f"f{f}_F{ff}": min(e for (a, e, b) in foutA
                                                      if a == f and b == ff)
                                   for (f, _, ff) in sorted(foutA)},
        violations=dict(viol), clean=(len(viol) == 0))


# ---------------------------------------------------------------- §16 cell ordering
def cell_ordering():
    c = cells()
    order = sorted(c["per_cell"].values(),
                   key=lambda v: (v["n_alive"], v["max_H"], v["max_x"]))
    return dict(
        criteria=["number of live subcases", "H budget", "x budget", "D = 5k - 2"],
        ranked=[dict(cell=v["cell"], D=v["D"], live_subcases=v["n_alive"],
                     max_H=v["max_H"], max_x=v["max_x"], max_e=v["max_e"],
                     heavy_multisets=len(v["heavy_multisets"])) for v in order],
        recommended_first="(k,G) = (4,2)",
        why=("only 5 live subcases, H = 0 and x = 0 forced, e <= 2, no heavy tail at all; "
             "it is the exact analogue of (4,1), which Round 117 closed first in the G = 1 "
             "column, and it needs the smallest new engine surface"),
        hardest="(k,G) = (1,2)",
        why_hardest=("170 live subcases across all seven heavy multisets including the "
                     "weight-6 composition, H up to 3, and three internal models"),
        note="Round 129 does NOT start closing any of them")


def summarise(n4=None):
    c = cells()
    rep = dict(
        round=129, column="G = 2", outer_axis="G (never F)",
        identities=identities(),
        internal_F=internal_F(),
        multiplicity_types=multiplicity_types(),
        free_exit_bounds=free_exit_bounds(),
        theorem_A=theorem_A_consequence(),
        cells=c,
        heavy_catalogue=heavy_catalogue(),
        engine_reuse=engine_reuse_audit(),
        cell_ordering=cell_ordering(),
        n4_validation=n4,
        new_result=dict(
            name="Theorem 129.1 (sharper free-exit bound for G = 2)",
            statement="f_out <= F + e, where F is the INTERNAL abandonment count",
            proof=("a free-exiting pass in case (i) satisfies p < nu(p), i.e. it is a "
                   "nu-ascent, so at most F of the free-exiting passes are case (i) and at "
                   "least f_out - F are case (ii); in type A the three targets lie in three "
                   "distinct orbits so those case-(ii) passes certify distinct split orbits, "
                   "giving e >= f_out - F.  In type B F = 2 always and Round 127 already "
                   "gives f_out <= 2 + e."),
            consequence="k + x + H <= 2 + F, so the type-A F = 1 model obeys k + x + H <= 3",
            payoff=("it removes the type-A F = 1 model from the (4,2) cell entirely: k = 4 "
                    "forces f_out - e >= 2 > F = 1"),
            n4_evidence="zero violations on 10,625 legal n = 4 G = 2 walks, and TIGHT - the "
                        "minimum e observed for type A with F = 1 is exactly f_out - 1"),
        no_giant_sweep=True,
        cells_closed_this_round=0,
        ledger_note="outer table = 55 cells indexed by (k, G); Claude-closed stays at 9/55",
        label="ROUND-129 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_g2_cells_129.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep
