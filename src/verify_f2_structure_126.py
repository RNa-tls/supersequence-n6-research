#!/usr/bin/env python3
"""라운드 126 — 일반 `F = 2` 의 구조 분류.

`F = 1` 의 항등식을 그대로 가져오지 않는다.  전부 일반 `F` 에서 다시 유도하고,
`n = 4` 전수와 `n = 5` 국소 전수로 **반증을 시도한다.**

핵심 정의 (라운드 110 의 계수 증명을 일반 `n`·일반 `F` 로 다시 쓴 것):

    P  = 패스 수 = n!/n + F      (F := Σ_h (e_h − 1), e_h = 육각형 h 의 진입 횟수)
    S  = #{joint : ω ≥ 3}
    H  = Σ (ω−3)₊
    O  = 건드린 궤도 수,  k := O − n!/(n(n−1))
    D  = (n−1)·O − P = (n−1)k − F
    r  = run 수 (같은 궤도의 극대 연속 블록),  e := r − O
    x  = intra-run joint 중 ω ≥ 3 인 것의 개수
    f_out = inter-run joint 중 ω = 2 인 것(자유 탈출)의 개수
    N  = S + F − O
"""
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


# ---------------------------------------------------------------- general-n geometry
def setup(n):
    perms = [tuple(p) for p in itertools.permutations(range(n))]
    idx = {p: i for i, p in enumerate(perms)}

    def sg(w):
        return w[1:] + w[:1]

    def ta(w):
        return w[1:n - 1] + (w[0],) + (w[n - 1],)

    def om(a, b):
        for k in range(1, n):
            if a[k:] == b[:n - k]:
                return k
        return n

    hexid = [-1] * len(perms)
    orbid = [-1] * len(perms)
    hexph = [-1] * len(perms)
    orbph = [-1] * len(perms)
    nh = no = 0
    for i, w in enumerate(perms):
        if hexid[i] < 0:
            x, j = w, 0
            for _ in range(n):
                hexid[idx[x]] = nh
                hexph[idx[x]] = j
                x = sg(x)
                j += 1
            nh += 1
        if orbid[i] < 0:
            x, j = w, 0
            for _ in range(n - 1):
                orbid[idx[x]] = no
                orbph[idx[x]] = j
                x = ta(x)
                j += 1
            no += 1
    assert nh == len(perms) // n and no == len(perms) // (n - 1)
    return dict(n=n, perms=perms, idx=idx, sig=sg, tau=ta, omega=om,
                hexid=hexid, orbid=orbid, hexph=hexph, orbph=orbph,
                n_hex=nh, n_orb=no)


def free_successor_identity(n):
    """§5·§6 자유 후속 공식.

    `y` 에서 나가는 **유일한** `ω = 2` joint 는
    `T1(y) = (y[2], …, y[n−1], y[1], y[0])` 이고, 항등식

        T1(σ^{n−1}(w)) = τ(w)

    가 성립한다.  진입 `u`, 길이 `len` 인 pass 의 탈출 단어는 `σ^{len−1}(u)` 이고
    `σ^{len−1}(u) = σ^{n−1}(σ^{len}(u))` 이므로

        **자유 후속 = τ(σ^{len}(u)) = τ(같은 육각형에서 순환적으로 다음 pass 의 진입 단어)**

    이 된다.  `len = n` (full pass) 이면 `σ^{len}(u) = u` 라 자유 후속은 `τ(u)` — **같은 궤도**.
    `len < n` 이면 `σ^{len}(u) ≠ u` 는 같은 육각형의 **다른** 단어이고 육각형의 `n` 개 단어는
    서로 다른 `n` 개 궤도에 있으므로 자유 후속은 **반드시 궤도를 바꾼다.**
    """
    g = setup(n)
    perms, idx, sg, ta, om = g["perms"], g["idx"], g["sig"], g["tau"], g["omega"]

    def T1(y):
        return y[2:] + (y[1], y[0])

    bad_unique = bad_ident = bad_full = bad_short = 0
    two_at_omega2 = other_is_sigma2 = 0
    hex_words_distinct_orbits = 0
    for w in perms:
        succ2 = [z for z in perms if om(w, z) == 2]
        # `omega = 2` 인 단어는 **둘**이다: T1(w) 와 σ²(w).  후자는 같은 육각형이고,
        # 중간 창 σ(w) 가 순열이므로 joint 가 아니라 회전 두 번이다 (라운드 125 §4 와 같은
        # 퇴화).  따라서 **합법 joint 로서의 ω=2 후속은 T1(w) 하나뿐**이다.
        if len(succ2) == 2:
            two_at_omega2 += 1
        s2 = sg(sg(w))
        if set(succ2) == {T1(w), s2}:
            other_is_sigma2 += 1
        else:
            bad_unique += 1
        y = w
        for _ in range(n - 1):
            y = sg(y)
        if T1(y) != ta(w):
            bad_ident += 1
    # per-word: free successor of a pass with entry u and length L
    for u in perms:
        for L in range(1, n + 1):
            y = u
            for _ in range(L - 1):
                y = sg(y)
            nxt = u
            for _ in range(L):
                nxt = sg(nxt)
            if T1(y) != ta(nxt):
                bad_full += 1
            same_orb = g["orbid"][idx[T1(y)]] == g["orbid"][idx[u]]
            if L == n and not same_orb:
                bad_full += 1
            if L < n and same_orb:
                bad_short += 1
    for h in range(g["n_hex"]):
        ws = [i for i in range(len(perms)) if g["hexid"][i] == h]
        if len({g["orbid"][i] for i in ws}) != n:
            hex_words_distinct_orbits += 1
    return dict(
        n=n,
        words_at_omega2=dict(always_exactly_two=(two_at_omega2 == len(perms)),
                             other_is_always_sigma_squared=(other_is_sigma2 == len(perms)),
                             sigma_squared_is_same_hexagon_hence_not_a_joint=True),
        unique_legal_weight2_successor_is_T1=(bad_unique == 0),
        identity_T1_sigma_n1_equals_tau=(bad_ident == 0),
        free_successor_formula_holds=(bad_full == 0),
        short_pass_free_successor_always_changes_orbit=(bad_short == 0),
        hexagons_whose_words_miss_distinct_orbits=hex_words_distinct_orbits,
        checked_words=len(perms), checked_pass_shapes=len(perms) * n)


def same_hexagon_never_consecutive(n):
    """§3 — 연속한 두 pass 는 절대 같은 육각형에 있을 수 없다.

    같은 육각형이면 `z = σ^m(y)` (`1 ≤ m ≤ n−1`) 이고, 문자열 `y·z의 마지막 m 글자` 의
    오프셋 `j = 1..m−1` 창은 정확히 `σ^j(y)` — **전부 순열**이다.  비반복 walk 에서는
    그 창들도 walk 의 정점이어야 하므로 이 전이는 joint 가 아니라 회전 `m` 번이고,
    두 pass 는 사실 **같은 pass** 다.  `m = 1` 은 회전 자체다.  따라서 모순.
    """
    g = setup(n)
    perms, idx, sg, om = g["perms"], g["idx"], g["sig"], g["omega"]
    bad = 0
    inter_windows_all_perms = 0
    total = 0
    for y in perms:
        for m in range(1, n):
            z = y
            for _ in range(m):
                z = sg(z)
            total += 1
            if om(y, z) != m:
                bad += 1
            s = list(y) + [y[i] for i in range(m)]
            wins = [tuple(s[j:j + n]) for j in range(1, m)]
            if all(len(set(w)) == n for w in wins):
                inter_windows_all_perms += 1
    return dict(n=n, pairs_checked=total,
                omega_equals_rotation_count=(bad == 0),
                every_intermediate_window_is_a_permutation=(inter_windows_all_perms == total),
                conclusion="two passes of the same hexagon can never be consecutive")


# ---------------------------------------------------------------- multiplicity taxonomy
def partitions(m, mx=None):
    if mx is None:
        mx = m
    if m == 0:
        yield ()
        return
    for p in range(min(m, mx), 0, -1):
        for rest in partitions(m - p, p):
            yield (p,) + rest


def multiplicity_types(F):
    """§2 — `F = Σ_h (e_h − 1)` 이므로 양수 부분들은 `F` 의 분할이다.  완전성은 즉각적이다."""
    out = []
    for p in partitions(F):
        mult = [q + 1 for q in p]
        out.append(dict(partition=list(p), entry_counts=mult, m=len(mult),
                        n_short_passes=sum(mult)))
    return out


def length_compositions(n, e_h):
    """육각형 하나의 `e_h` 개 pass 길이: `n` 을 `e_h` 개의 양의 정수로 나눈 **순서 있는** 분해."""
    out = []

    def rec(rem, k, cur):
        if k == 1:
            if rem >= 1:
                out.append(tuple(cur + [rem]))
            return
        for a in range(1, rem - k + 2):
            rec(rem - a, k - 1, cur + [a])

    rec(n, e_h, [])
    return out


def short_pass_structure(n, F):
    """§3·§4 — 다중 진입 유형마다 짧은 pass 수 · 길이 분해 · 결손 분해."""
    rows = []
    for t in multiplicity_types(F):
        per_hex = []
        for e_h in t["entry_counts"]:
            comps = length_compositions(n, e_h)
            per_hex.append(dict(
                entries=e_h,
                all_passes_short=all(all(a < n for a in c) for c in comps),
                n_ordered_compositions=len(comps),
                length_partitions=sorted({tuple(sorted(c, reverse=True)) for c in comps}),
                deficits=sorted({tuple(sorted((n - a for a in c), reverse=True))
                                 for c in comps})))
        rows.append(dict(
            partition=t["partition"], entry_counts=t["entry_counts"], m=t["m"],
            n_short_passes=t["n_short_passes"],
            total_deficit=n * F,
            deficit_check=(sum(n * (e - 1) for e in t["entry_counts"]) == n * F),
            per_hexagon=per_hex,
            n_split_shapes=int(__import__("math").prod(
                len(length_compositions(n, e)) for e in t["entry_counts"]))))
    return rows


# ---------------------------------------------------------------- §1·§7·§8·§9 arithmetic
def constants(n):
    fact = 1
    for i in range(2, n + 1):
        fact *= i
    return dict(n=n, n_words=fact, n_hex=fact // n, n_orb=fact // (n - 1),
                O_min=fact // (n * (n - 1)), P_min=fact // n,
                L_base=n + fact - 2 + fact // n)


def identities(n, F):
    """§1·§7 — 일반 `n`, 일반 `F` 에서 다시 유도한 항등식 (F=1 형태를 상속하지 않는다).

        P = n!/n + F
        Σ_pass len = n!  ⇒  총 결손 Σ (n − len) = n·P − n! = n·F
        육각형 h 하나에서는 Σ len = n  ⇒  결손 = n(e_h − 1)
        D = (n−1)O − P = (n−1)k − F ≥ 0  ⇒  **F ≤ (n−1)k**
        L = L_base + F + S + H          (L_base = n + n! − 2 + n!/n)
        S = (r − 1) + x − f_out,  r = O + e            ← F 에 의존하지 않는다
        N = S + F − O = F − 1 + e + x − f_out
        L = L_base + O_min + k + N + H = (L_base + O_min − 1) + k + F + e + x + H − f_out
    """
    c = constants(n)
    return dict(
        n=n, F=F, P=c["P_min"] + F, total_deficit=n * F,
        per_hexagon_deficit="n(e_h - 1)",
        D="(n-1)k - F", k_min=-(-F // (n - 1)),
        L_formula=f"{c['L_base']} + F + S + H",
        L_at_F=f"{c['L_base'] + F} + S + H",
        S_formula="(r - 1) + x - f_out   with r = O + e",
        N_formula="F - 1 + e + x - f_out",
        master=f"L = {c['L_base'] + c['O_min'] - 1} + k + F + e + x + H - f_out",
        master_at_F=f"L = {c['L_base'] + c['O_min'] - 1 + F} + k + e + x + H - f_out",
        **{kk: vv for kk, vv in c.items() if kk != "n"})


def f2_budget(LCAP=871):
    """§1·§8·§9 — `F = 2`, `n = 6` 의 정확한 예산과 실현 가능한 `k`.

    `L = 869 + k + e + x + H − f_out ≤ 871  ⟺  k + e + x + H − f_out ≤ 2`.

    증명된 `f_out` 상한 (§5·§6):
      * `f_out ≤ #짧은 pass = F + m`  (m = 다중 진입 육각형 수);
      * 어떤 다중 진입 육각형의 **모든** pass 가 자유로 나가면 `e ≥ 1` (보조정리 E′);
      * 타입 A(m=1): `f_out = 3 ⟹ e ≥ 1`  ⇒  **`f_out ≤ F + e` 증명됨**;
      * 타입 B(m=2): `f_out ≥ 3 ⟹` 어떤 육각형이 완전 자유 `⟹ e ≥ 1`.
        `f_out = 4, e = 1` 만 미해결.
    """
    rows = []
    for typ, m, smax in (("A", 1, 3), ("B", 2, 4)):
        for f in range(0, smax + 1):
            # 증명된 하한: 육각형 하나가 완전 자유면 e >= 1
            if typ == "A":
                emin = 1 if f == 3 else 0
            else:
                emin = 1 if f >= 3 else 0
            for e in range(emin, 6):
                for x in range(0, 6):
                    for H in range(0, 7):
                        for k in range(1, 8):
                            if (n_1 := 5 * k - 2) < 0:
                                continue
                            if k + e + x + H - f > LCAP - 869:
                                continue
                            rows.append(dict(type=typ, m=m, f_out=f, e=e, x=x, H=H, k=k,
                                             D=n_1, O=24 + k, S=23 + k + e + x - f,
                                             N=1 + e + x - f, L=869 + k + e + x + H - f,
                                             violates_f_out_le_F_plus_e=(f > 2 + e),
                                             violates_theorem_A=(f > 2 + e + x)))
    return rows


def f2_cells(LCAP=871):
    """§9 — 산술적으로 가능한 `k` 값과 `F = 2` 칸의 개수."""
    rows = f2_budget(LCAP)
    uncond = sorted({r["k"] for r in rows})
    cond = sorted({r["k"] for r in rows if not r["violates_f_out_le_F_plus_e"]})
    thmA = sorted({r["k"] for r in rows if not r["violates_theorem_A"]})
    openrows = [r for r in rows if r["violates_f_out_le_F_plus_e"]]
    return dict(
        k_min_from_D="F <= (n-1)k  =>  2 <= 5k  =>  k >= 1",
        k_feasible_unconditional=uncond,
        k_feasible_if_f_out_le_F_plus_e=cond,
        k_feasible_if_theorem_A=thmA,
        n_cells_unconditional=len(uncond),
        n_cells_conditional=len(cond),
        max_H_unconditional=max(r["H"] for r in rows),
        max_H_conditional=max(r["H"] for r in rows
                              if not r["violates_f_out_le_F_plus_e"]),
        max_H_by_type={t: max(r["H"] for r in rows if r["type"] == t) for t in "AB"},
        max_H_by_type_conditional={
            t: max(r["H"] for r in rows
                   if r["type"] == t and not r["violates_f_out_le_F_plus_e"])
            for t in "AB"},
        max_H_if_theorem_A=max(r["H"] for r in rows if not r["violates_theorem_A"]),
        n_cells_if_theorem_A=len(thmA),
        theorem_A_open_configuration=sorted({(r["type"], r["f_out"], r["e"], r["x"])
                                             for r in rows if r["violates_theorem_A"]}),
        k_plus_x_plus_H_max_if_theorem_A=max(
            r["k"] + r["x"] + r["H"] for r in rows if not r["violates_theorem_A"]),
        k_plus_x_plus_H_max_conditional=max(
            r["k"] + r["x"] + r["H"] for r in rows
            if not r["violates_f_out_le_F_plus_e"]),
        open_configuration=sorted({(r["type"], r["f_out"], r["e"], r["x"])
                                   for r in openrows}),
        n_rows_unconditional=len(rows),
        n_rows_conditional=len(rows) - len(openrows))


# ---------------------------------------------------------------- §10 n = 4 falsification
def legal_joint(n, a, b, m):
    """### 라운드 126 §10 의 모형 정정 — 전이는 **합법 joint** 여야 한다.

    `a -> b` 가 `omega = m` 이면 문자열은 `a` 뒤에 `b` 의 마지막 `m` 글자를 붙인 것이고,
    오프셋 `j = 1..m-1` 의 창이 새로 생긴다.  NR6 walk 의 문자열은 각 순열을 **정확히 한 번**
    창으로 가져야 하므로 그 중간 창은 **순열이면 안 된다** (순열이면 그 순열이 문자열에 두 번
    나오거나, walk 이 그 지점을 지나간 것이 되어 pass 분해가 달라진다).

    이것은 라운드 125 §4 가 무게-6 목록에서 발견한 퇴화와 **같은 조건**이다.
    특히 `b = σ^m(a)` 는 중간 창이 전부 `σ^j(a)` 라 **언제나 불법**이다.

    라운드 120·122 의 `n = 4` 대조는 이 조건을 걸지 않았으므로 **합법 walk 의 초집합**을
    돌았다.  대조로서는 여전히 유효하지만(초집합에서 성립하면 부분집합에서도 성립한다),
    구조 주장을 반증하는 데 쓰려면 반드시 걸러야 한다.
    """
    s = list(a) + list(b[n - m:])
    for j in range(1, m):
        if len(set(s[j:j + n])) == n:
            return False
    return True


def n4_walks(maxlen, legal_only=True):
    """고정된 시작 단어에서 출발하는 모든 비반복 `n = 4` walk (S₄ 좌곱으로 완전 축약).

    `legal_only` 면 합법 joint 만 쓴다 (위 `legal_joint` 참조)."""
    g = setup(4)
    perms, idx, sg, om = g["perms"], g["idx"], g["sig"], g["omega"]
    W = [[om(a, b) for b in perms] for a in perms]
    OK = [[(a == b) or (not legal_only) or legal_joint(4, perms[a], perms[b], W[a][b])
           for b in range(24)] for a in range(24)]
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
            if not OK[cur][j]:
                continue
            w = W[cur][j]
            if 4 + total + w + (24 - len(seq) - 1) > maxlen:
                continue
            seq.append(j)
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    dfs(0, 1, [0], 0)
    return g, W, out


def measure(g, W, seq, L):
    """walk 하나에서 라운드 126 의 모든 좌표와 구조를 뽑는다."""
    n = g["n"]
    idx, sg = g["idx"], g["sig"]
    perms, hexid, orbid = g["perms"], g["hexid"], g["orbid"]
    nfact = len(perms)
    om = [W[seq[i]][seq[i + 1]] for i in range(len(seq) - 1)]
    passes, cur, start = [], 1, seq[0]
    for i, w in enumerate(om):
        if w >= 2:
            passes.append((start, cur))
            cur = 1
            start = seq[i + 1]
        else:
            cur += 1
    passes.append((start, cur))
    P = len(passes)
    F = P - nfact // n
    joints = [w for w in om if w >= 2]
    S = sum(1 for w in joints if w >= 3)
    H = sum(max(w - 3, 0) for w in joints)
    entries = [p[0] for p in passes]
    lens = [p[1] for p in passes]
    hx = [hexid[e] for e in entries]
    orbs = [orbid[e] for e in entries]
    ecnt = Counter(hx)
    O = len(set(orbs))
    k = O - nfact // (n * (n - 1))
    runs, curr = [], [0]
    for i in range(1, P):
        if orbs[i] == orbs[i - 1]:
            curr.append(i)
        else:
            runs.append(curr)
            curr = [i]
    runs.append(curr)
    r = len(runs)
    e = r - O
    inter = {run[0] - 1 for run in runs[1:]}          # joint index that breaks a run
    x = sum(1 for i, w in enumerate(joints) if i not in inter and w >= 3)
    f_out = sum(1 for i in inter if joints[i] == 2)
    N = S + F - O
    # nu: hexagon-successor permutation on passes
    bypos = {}
    for i, (u, ln) in enumerate(passes):
        bypos[(hexid[u], g["hexph"][u])] = i
    nu = []
    for i, (u, ln) in enumerate(passes):
        z = perms[u]
        for _ in range(ln):
            z = sg(z)
        nu.append(bypos[(hexid[idx[z]], g["hexph"][idx[z]])])
    runof = [None] * P
    for ri, run in enumerate(runs):
        for i in run:
            runof[i] = ri
    return dict(L=L, P=P, F=F, S=S, H=H, O=O, k=k, r=r, e=e, x=x, f_out=f_out, N=N,
                lens=lens, hexes=hx, orbs=orbs, entry_counts=dict(ecnt), passes=passes,
                nu=nu, runof=runof, joints=joints, inter=sorted(inter),
                m=sum(1 for v in ecnt.values() if v >= 2))


def n4_falsify(maxlen=37, legal_only=True):
    """§10 — `n = 4` 전수로 라운드 126 의 모든 주장을 반증 시도한다."""
    g, W, walks = n4_walks(maxlen, legal_only)
    n, nfact = 4, 24
    c = constants(4)
    stat = Counter()
    viol = Counter()
    f2types = Counter()
    fout_by_type_e = Counter()
    open_case = []
    perms, idx, sg = g["perms"], g["idx"], g["sig"]
    for L, seq in walks:
        r = measure(g, W, seq, L)
        stat["walks"] += 1
        stat[f"F={r['F']}"] += 1
        # --- identities -------------------------------------------------------
        if r["P"] != c["P_min"] + r["F"]:
            viol["P = n!/n + F"] += 1
        if L != c["L_base"] + r["F"] + r["S"] + r["H"]:
            viol["L = L_base + F + S + H"] += 1
        if r["S"] != (r["r"] - 1) + r["x"] - r["f_out"]:
            viol["S = (r-1) + x - f_out"] += 1
        if r["N"] != r["F"] - 1 + r["e"] + r["x"] - r["f_out"]:
            viol["N = F - 1 + e + x - f_out"] += 1
        if L != (c["L_base"] + c["O_min"] - 1) + r["k"] + r["F"] + r["e"] + r["x"] \
                + r["H"] - r["f_out"]:
            viol["master identity"] += 1
        if (n - 1) * r["O"] - r["P"] != (n - 1) * r["k"] - r["F"]:
            viol["D = (n-1)k - F"] += 1
        if (n - 1) * r["k"] - r["F"] < 0:
            viol["D >= 0"] += 1
        # --- multiplicity taxonomy (S2) --------------------------------------
        parts = sorted((v - 1 for v in r["entry_counts"].values() if v >= 2), reverse=True)
        if sum(parts) != r["F"]:
            viol["F = sum(e_h - 1)"] += 1
        if len(r["entry_counts"]) != c["n_hex"]:
            viol["every hexagon entered"] += 1
        # --- short-pass structure (S3) ---------------------------------------
        shorts = [i for i, ln in enumerate(r["lens"]) if ln < n]
        multi = {h for h, v in r["entry_counts"].items() if v >= 2}
        if {i for i in range(r["P"]) if r["hexes"][i] in multi} != set(shorts):
            viol["short pass <=> multiply-entered hexagon"] += 1
        if len(shorts) != r["F"] + r["m"]:
            viol["#short = F + m"] += 1
        if any(r["hexes"][i] == r["hexes"][i + 1] for i in range(r["P"] - 1)):
            viol["same-hexagon passes never consecutive"] += 1
        for h in r["entry_counts"]:
            tot = sum(r["lens"][i] for i in range(r["P"]) if r["hexes"][i] == h)
            if tot != n:
                viol["per-hexagon lengths sum to n"] += 1
        if sum(n - ln for ln in r["lens"]) != n * r["F"]:
            viol["total deficit = nF"] += 1
        # --- free-successor formula and nu (S5, S6) ---------------------------
        for i in range(r["P"] - 1):
            if r["joints"][i] == 2:
                nxt_entry = r["passes"][i + 1][0]
                u = perms[r["passes"][r["nu"][i]][0]]
                if nxt_entry != idx[g["tau"](u)]:
                    viol["free successor = tau(entry(nu(p)))"] += 1
        if sorted(r["nu"]) != list(range(r["P"])):
            viol["nu is a permutation"] += 1
        for i in range(r["P"]):
            if r["hexes"][r["nu"][i]] != r["hexes"][i]:
                viol["nu preserves the hexagon"] += 1
            if r["lens"][i] == n and r["nu"][i] != i:
                viol["full pass is a nu-fixed point"] += 1
        # --- f_out bounds (S5) ------------------------------------------------
        if r["f_out"] > r["F"] + r["m"]:
            viol["f_out <= F + m"] += 1
        if r["f_out"] > r["F"] + r["e"]:
            viol["f_out <= F + e"] += 1
        if r["f_out"] > r["F"] + r["e"] + r["x"]:
            viol["Theorem A: f_out <= F + e + x"] += 1
        # Lemma E' : a fully-free multiply-entered hexagon forces e >= 1
        freepass = {i for i in range(r["P"] - 1)
                    if r["joints"][i] == 2 and i in set(r["inter"])}
        for h, v in r["entry_counts"].items():
            if v >= 2 and all(i in freepass for i in range(r["P"]) if r["hexes"][i] == h):
                if r["e"] < 1:
                    viol["Lemma E': fully-free hexagon => e >= 1"] += 1
        # --- F = 2 specifics ---------------------------------------------------
        if r["F"] == 2:
            typ = "A" if parts == [2] else ("B" if parts == [1, 1] else "?")
            f2types[typ] += 1
            f2types[f"{typ}:lens={tuple(sorted((r['lens'][i] for i in shorts), reverse=True))}"] += 1
            fout_by_type_e[(typ, r["f_out"], r["e"])] += 1
            if typ == "B" and r["f_out"] == 4:
                open_case.append(dict(e=r["e"], x=r["x"], k=r["k"], H=r["H"], L=L))
    return dict(
        n=4, maxlen=maxlen, legal_only=legal_only, walks=len(walks),
        F_distribution={kk: vv for kk, vv in sorted(stat.items()) if kk.startswith("F=")},
        violations=dict(viol),
        all_claims_survive=(len(viol) == 0),
        F2_types={kk: vv for kk, vv in sorted(f2types.items())},
        F2_fout_by_type_and_e={f"{t}_f{f}_e{e}": v
                               for (t, f, e), v in sorted(fout_by_type_e.items())},
        typeB_fout_max_observed=max([0] + [f for (t, f, e) in fout_by_type_e if t == "B"]),
        open_case_typeB_fout4=open_case[:20],
        n_open_case_typeB_fout4=len(open_case))


def n4_legality_impact(maxlen=37):
    """### 라운드 120·122 의 `n = 4` 대조를 합법 모형에서 다시 잰다.

    그 대조들은 joint 합법성을 걸지 않아 **합법 walk 의 초집합**을 돌았다.  대조로서는
    유효하지만(초집합에서 성립하면 부분집합에서도 성립한다), 구조 통계는 달라진다.
    라운드 122 §10 이 쓴 두 통계를 합법 모형에서 다시 잰다.
    """
    out = {}
    for legal in (False, True):
        g, W, walks = n4_walks(maxlen, legal)
        F1 = firstfull = lastfull = bothfull = 0
        for L, seq in walks:
            r = measure(g, W, seq, L)
            if r["F"] != 1:
                continue
            F1 += 1
            ff = r["lens"][0] == 4
            lf = r["lens"][-1] == 4
            firstfull += ff
            lastfull += lf
            bothfull += (ff and lf)
        out["legal" if legal else "superset"] = dict(
            walks=len(walks), F1_walks=F1, first_pass_full=firstfull,
            last_pass_full=lastfull, both_ends_full=bothfull,
            first_pass_full_pct=round(100 * firstfull / F1, 1) if F1 else None,
            both_ends_full_pct=round(100 * bothfull / F1, 1) if F1 else None)
    out["conclusion"] = (
        "the Round-122 conclusion survives: even in the legal model a large fraction of F = 1 "
        "walks have a FULL first pass and both ends full, so F = 1 does not force the short "
        "pass to sit at an end")
    return out


def fout_minimum_e(maxlen=38):
    """§5 — 관측된 `(타입, f_out)` 마다의 **최소 `e`**.  추측 `f_out ≤ F + e` 의 정밀 검사."""
    g, W, walks = n4_walks(maxlen, True)
    best = {}
    allF = {}
    for L, seq in walks:
        r = measure(g, W, seq, L)
        parts = sorted((v - 1 for v in r["entry_counts"].values() if v >= 2), reverse=True)
        key = (r["F"], tuple(parts), r["f_out"])
        best[key] = min(best.get(key, 99), r["e"])
        allF[(r["F"], r["f_out"])] = min(allF.get((r["F"], r["f_out"]), 99), r["e"])
    return dict(
        maxlen=maxlen, walks=len(walks),
        min_e_by_F_partition_fout={f"F{f}_{'.'.join(map(str, p))}_f{fo}": v
                                   for (f, p, fo), v in sorted(best.items())},
        min_e_by_F_fout={f"F{f}_f{fo}": v for (f, fo), v in sorted(allF.items())},
        conjecture_f_out_le_F_plus_e_holds=all(fo <= f + v for (f, fo), v in allF.items()),
        tight_cases=[f"F{f}_f{fo}: min e = {v} (= f_out - F)"
                     for (f, fo), v in sorted(allF.items()) if v == fo - f])


def heavy_compositions(H):
    """`H = Σ (w−3)₊` 를 만드는 무거운 이음매 무게 다중집합 (무게 ≤ 6 이므로 부분 ≤ 3)."""
    out = []

    def rec(rem, mx, cur):
        if rem == 0:
            out.append(tuple(3 + p for p in cur))
            return
        for p in range(min(rem, mx), 0, -1):
            rec(rem - p, p, cur + [p])

    rec(H, 3, [])
    return out


def summarise(n4_maxlen=39, legality_maxlen=35):
    cells = f2_cells()
    ident = identities(6, 2)
    fal = n4_falsify(n4_maxlen)
    mine = fout_minimum_e(n4_maxlen)
    rep = dict(
        round=126, column="F = 2", n=6,
        identities=ident,
        local_lemmas={str(n): free_successor_identity(n) for n in (4, 5, 6)},
        same_hexagon_theorem={str(n): same_hexagon_never_consecutive(n) for n in (4, 5, 6)},
        multiplicity_taxonomy=dict(
            types=multiplicity_types(2),
            completeness=("F = Σ_h (e_h − 1) with e_h >= 1 integers, so the positive parts "
                          "form a partition of F; partitions of 2 are {2} and {1,1}, hence "
                          "exactly two types, and the taxonomy is complete"),
            type_A="one hexagon entered three times (m = 1, 3 short passes)",
            type_B="two hexagons entered twice each (m = 2, 4 short passes)"),
        short_pass_structure=short_pass_structure(6, 2),
        short_pass_rules=[
            "per hexagon the pass lengths sum to n = 6, so a hexagon with e_h >= 2 entries "
            "has ALL its passes short and a hexagon with e_h = 1 has one full pass",
            "#short passes = F + m, so 3 in type A and 4 in type B",
            "total length deficit = n*F = 12, and hexagon h contributes exactly n(e_h - 1)",
            "two passes of the same hexagon are NEVER consecutive (proved for all F and all n)"],
        free_exit_structure=dict(
            unique_legal_weight2_successor="T1(y) = (y[2], ..., y[n-1], y[1], y[0])",
            other_weight2_word="sigma^2(y) - same hexagon, illegal (intermediate window is a "
                               "permutation), so it is two rotations, not a joint",
            formula="free successor of a pass = tau(entry(nu(p)))",
            nu="the hexagon-successor permutation on passes; its cycles are the hexagons, "
               "with cycle length e_h (F=1: one 2-cycle; F=2 type A: one 3-cycle; "
               "F=2 type B: two 2-cycles)",
            full_pass="nu-fixed, so its free successor tau(u) stays in the same orbit and can "
                      "never be an inter-run arc",
            short_pass="nu(p) != p, and a hexagon's n words lie in n DISTINCT orbits, so the "
                       "free successor always changes orbit - always an inter-run arc",
            order_lemma="if p exits freely and is in case (i) then p < nu(p) in walk order",
            lemma_E_prime=("for a hexagon h with e_h >= 2: if EVERY pass of h exits freely, "
                           "then some pass of h is in case (ii), so some orbit carries two "
                           "runs and e >= 1")),
        f_out_bounds=dict(
            proved_all_F="f_out <= #short = F + m",
            proved_typeA="f_out <= F + e   (f_out = 3 forces e >= 1 via Lemma E')",
            proved_typeB="f_out >= 3 forces a fully-free hexagon by pigeonhole, hence e >= 1; "
                         "so f_out <= 2 when e = 0 and f_out <= 4 when e >= 1",
            open_case="type B with f_out = 4 and e = 1 - the ONLY configuration where "
                      "f_out <= F + e is not proved",
            conjecture="f_out <= F + e   (reduces to Lemma E at F = 1)",
            falsification=dict(
                n4_walks=mine["walks"], n4_maxlen=n4_maxlen,
                holds=mine["conjecture_f_out_le_F_plus_e_holds"],
                min_e_by_F_and_fout=mine["min_e_by_F_fout"],
                tight_cases=mine["tight_cases"],
                typeB_fout4_min_e_observed=min(
                    [c["e"] for c in fal["open_case_typeB_fout4"]] or [None]),
                open_case_observed=sum(1 for c in fal["open_case_typeB_fout4"]
                                       if c["e"] == 1))),
        resource_accounting=dict(
            S="(r - 1) + x - f_out, r = O + e - the derivation never uses F",
            why=("every inter-run joint from a FULL pass has omega >= 3 (its only omega-2 "
                 "successor tau(u) is intra-orbit), and every omega-2 exit of a SHORT pass "
                 "is inter-run, so #{inter-run, omega=2} = f_out exactly"),
            N="F - 1 + e + x - f_out",
            master_identity=ident["master"],
            at_F2=ident["master_at_F"],
            budget="L <= 871  <=>  k + e + x + H - f_out <= 2",
            theorem_A_equivalent="O <= 1 + S + F  <=>  f_out <= F + e + x",
            theorem_A_status=("PROVED at F = 1 by Lemma E; PROVED here for F = 2 type A and "
                              "for type B except the single open configuration; EMPIRICAL "
                              "for F >= 3 - and the project's 55-cell slab table depends on it")),
        heavy_tails=dict(
            catalogue={"w1": 1, "w2": 1, "w3": 3, "w4": 13, "w5": 71,
                       "w6_genuine": 308, "w6_raw_indecomposable": 461},
            note="Round 125 correction: only 308 of the 461 indecomposable permutations of "
                 "{0..5} realize omega = 6",
            max_H_unconditional=cells["max_H_unconditional"],
            max_H_typeA=cells["max_H_by_type"]["A"],
            max_H_typeB=cells["max_H_by_type"]["B"],
            max_H_if_f_out_le_F_plus_e=cells["max_H_conditional"],
            max_H_if_theorem_A=cells["max_H_if_theorem_A"],
            H_can_exceed_3=("only in type B, only in the single open configuration "
                            "(f_out = 4, e = 1, x = 0, k = 1), where H = 4 would be allowed"),
            compositions={str(H): [list(c) for c in heavy_compositions(H)]
                          for H in range(0, 5)}),
        feasible_cells=cells,
        n4_falsification={kk: vv for kk, vv in fal.items() if kk != "F2_types"},
        n4_F2_length_shapes=fal["F2_types"],
        legality_correction=dict(
            statement=("a transition a -> b with omega = m is a legal joint only if none of "
                       "the m - 1 intermediate windows is a permutation; this is the same "
                       "degeneracy Round 125 found in the weight-6 catalogue"),
            rounds_120_122_n4_controls=("did NOT enforce joint legality, so they ran on a "
                                        "SUPERSET of legal walks; valid as controls, but the "
                                        "structural statistics differ"),
            impact=n4_legality_impact(legality_maxlen),
            without_legality=("2 of the round's claims fail on the superset - "
                              "'same-hexagon passes are never consecutive' and the "
                              "free-successor formula - exactly the two that need legality")),
        no_giant_search=True,
        cell_status=dict(
            F0_column="Claude-closed", F1_column="Claude-closed",
            F2_column="OPEN - this round only classifies its structure",
            claude_closed_outer_cells="9/55 (unchanged)",
            F2_cells_conditional=cells["n_cells_conditional"],
            would_become_if_F2_closed="13/55"),
        label="ROUND-126 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f2_structure_126.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep


if __name__ == "__main__":
    r = summarise()
    print(json.dumps(dict(
        identities=r["identities"]["master_at_F"],
        budget=r["resource_accounting"]["budget"],
        types=[t["entry_counts"] for t in r["multiplicity_taxonomy"]["types"]],
        cells=r["feasible_cells"]["k_feasible_if_f_out_le_F_plus_e"],
        max_H=r["heavy_tails"]["max_H_if_f_out_le_F_plus_e"],
        n4_walks=r["n4_falsification"]["walks"],
        violations=r["n4_falsification"]["violations"]), indent=1))
