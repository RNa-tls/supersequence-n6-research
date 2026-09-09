#!/usr/bin/env python3
"""라운드 140 감사 — G=3 국소 분류, 접속 사건 정리 `K+R<=G+1`, 516 자원 행.

전부 우리 자신의 규칙으로 처음부터 유도한다.
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations, combinations_with_replacement, permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------- §11/§4 다중도 패턴
def multiplicity_patterns(G=3):
    """`sum_h (m_h - 1) = G` 의 모든 분할."""
    out = []

    def rec(rem, cur, mx):
        if rem == 0:
            out.append(tuple(cur))
            return
        for v in range(min(rem, mx), 0, -1):
            rec(rem - v, cur + [v], v)
    rec(G, [], G)
    pats = []
    for p in out:
        ms = tuple(v + 1 for v in p)             # m_h = (m_h - 1) + 1
        pats.append(dict(excess=list(p), multiplicities=list(ms),
                         short_passes=sum(ms), n_split_hexagons=len(ms)))
    return pats


def cycles_of(perm):
    n = len(perm)
    seen = [False] * n
    cy = []
    for i in range(n):
        if seen[i]:
            continue
        c, j = [], i
        while not seen[j]:
            seen[j] = True
            c.append(j)
            j = perm[j]
        cy.append(c)
    return cy


def supports(pattern):
    """시간순 짧은 occurrence 위에서 가능한 모든 `nu` 지지.

    `m_h` 짝의 occurrence 를 어느 위치에 놓을지 고르고(분할), 각 육각형 안에서
    길이 `m_h` 순환 하나를 고른다.  같은 다중도끼리는 이름 구분이 없으므로
    표준화한다.
    """
    ms = pattern["multiplicities"]
    tot = sum(ms)
    seen = set()
    out = []

    def assign(rem_positions, idx, alloc):
        if idx == len(ms):
            yield tuple(alloc)
            return
        for combo in combinations(rem_positions, ms[idx]):
            rest = [p for p in rem_positions if p not in combo]
            yield from assign(rest, idx + 1, alloc + [combo])

    for alloc in assign(tuple(range(tot)), 0, []):
        for cyc_choice in _cycle_choices(alloc):
            nu = [0] * tot
            hexlab = [0] * tot
            for hi, (positions, cyc) in enumerate(zip(alloc, cyc_choice)):
                for a, b in cyc:
                    nu[a] = b
                for p in positions:
                    hexlab[p] = hi
            # 같은 다중도 육각형끼리는 라벨 교환 대칭 -> 표준화
            key = _canon(nu, hexlab, ms)
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(nu=nu, hexlab=hexlab))
    return out


def _cycle_choices(alloc):
    """각 육각형 위치 집합에 대해 그 위에서의 순환 하나 (모든 선택)."""
    def cycs(positions):
        m = len(positions)
        if m == 1:
            return [[(positions[0], positions[0])]]
        res = []
        first = positions[0]
        for rest in permutations(positions[1:]):
            order = (first,) + rest
            res.append([(order[i], order[(i + 1) % m]) for i in range(m)])
        return res
    lists = [cycs(list(p)) for p in alloc]

    def rec(i, cur):
        if i == len(lists):
            yield tuple(cur)
            return
        for c in lists[i]:
            yield from rec(i + 1, cur + [c])
    yield from rec(0, [])


def _canon(nu, hexlab, ms):
    best = None
    groups = {}
    for i, m in enumerate(ms):
        groups.setdefault(m, []).append(i)
    idxs = list(range(len(ms)))
    for perm in permutations(idxs):
        if any(ms[perm[i]] != ms[i] for i in idxs):
            continue
        relab = {perm[i]: i for i in idxs}
        hl = tuple(relab[h] for h in hexlab)
        cand = (tuple(nu), hl)
        if best is None or cand < best:
            best = cand
    return best


def beta_components(nu, P):
    """`beta = T . nu^{-1}` 의 성분 (더미 정점 `P` 포함)."""
    N = P + 1
    T = [(i + 1) % N for i in range(N)]
    nuf = list(nu) + [P]
    inv = [0] * N
    for i, j in enumerate(nuf):
        inv[j] = i
    nxt = [T[inv[j]] for j in range(N)]
    return cycles_of(nxt)


def support_table(G=3):
    rows = []
    for pat in multiplicity_patterns(G):
        sup = supports(pat)
        byF = Counter()
        KR = Counter()
        for s in sup:
            nu = s["nu"]
            F = sum(1 for i in range(len(nu)) if i < nu[i])
            byF[F] += 1
            comps = beta_components(nu, len(nu))
            K = len(comps)
            R = 0
            for c in comps:
                cnt = Counter(s["hexlab"][v] for v in c if v < len(nu))
                R += sum(max(m - 1, 0) for m in cnt.values())
            KR[(K, R)] += 1
            s["F"] = F
            s["K"] = K
            s["R"] = R
        # 길이 장식: 육각형마다 6 을 m_h 개 양의 부분으로 나누는 순서 합성
        def comps_of_6(parts):
            return len(list(combinations(range(1, 6), parts - 1)))
        dec = 1
        for m in pat["multiplicities"]:
            dec *= comps_of_6(m)
        rows.append(dict(pattern=pat, n_supports=len(sup),
                         by_F=dict(sorted(byF.items())),
                         decoration_factor=dec,
                         decorated_total=len(sup) * dec,
                         KR=dict(sorted((f"{k},{r}", v) for (k, r), v in KR.items())),
                         supports=sup))
    return rows


def incidence_theorem(G=3):
    tab = support_table(G)
    allKR = Counter()
    bad = []
    parity_ok = True
    decorated_by_F = Counter()
    for t in tab:
        for s in t["supports"]:
            allKR[(s["K"], s["R"])] += 1
            if s["K"] + s["R"] > G + 1:
                bad.append(s)
            if (s["K"] - (G + 1)) % 2 != 0:
                parity_ok = False
            decorated_by_F[s["F"]] += t["decoration_factor"]
    return dict(
        total_supports=sum(t["n_supports"] for t in tab),
        by_type={"".join(map(str, t["pattern"]["multiplicities"])): t["n_supports"]
                 for t in tab},
        by_type_F={"".join(map(str, t["pattern"]["multiplicities"])): t["by_F"]
                   for t in tab},
        decorated_by_type={"".join(map(str, t["pattern"]["multiplicities"])):
                           t["decorated_total"] for t in tab},
        decorated_total=sum(t["decorated_total"] for t in tab),
        decorated_by_F=dict(sorted(decorated_by_F.items())),
        KR_distribution={f"({k},{r})": v for (k, r), v in sorted(allKR.items())},
        K_plus_R_le_G_plus_1=(len(bad) == 0),
        K_parity_matches_G_plus_1=parity_ok,
        K_values=sorted({k for k, _ in allKR}),
        violations=len(bad))


# ------------------------------------------------------ §7 자원 행 공간
TYPES = {"A4": (4, [1, 2, 3]), "A3B2": (5, [2, 3]), "B222": (6, [3])}


def heavy_refinements(H):
    if H == 0:
        return [[]]
    out = []
    for h in (1, 2, 3):
        for ws in combinations_with_replacement((4, 5, 6), h):
            if sum(w - 3 for w in ws) == H:
                out.append(list(ws))
    return out


def resource_rows(G=3, kmin=1, kmax=4):
    """`(7.1)` 로부터 G=3 의 완전한 자원 행 공간."""
    per_k = {}
    for k in range(kmin, kmax + 1):
        rows = []
        for tname, (shortc, Fs) in TYPES.items():
            for F in Fs:
                budget = F + 1 - k
                if budget < 0:
                    continue
                for delta in range(budget + 1):
                    for x in range(budget - delta + 1):
                        for H in range(budget - delta - x + 1):
                            for f_out in range(shortc + 1):
                                e = f_out - F + delta
                                if e < 0:
                                    continue
                                rows.append(dict(type=tname, F=F, delta=delta,
                                                 x=x, H=H, f_out=f_out, e=e, k=k))
        ref = sum(len(heavy_refinements(r["H"])) for r in rows)
        per_k[k] = dict(k=k, O=24 + k, D=5 * k - G, P=120 + G,
                        arithmetic_rows=len(rows), heavy_refined_rows=ref,
                        by_type=dict(Counter(r["type"] for r in rows)),
                        by_F=dict(sorted(Counter(r["F"] for r in rows).items())),
                        by_delta=dict(sorted(Counter(r["delta"] for r in rows).items())),
                        by_x=dict(sorted(Counter(r["x"] for r in rows).items())),
                        by_H=dict(sorted(Counter(r["H"] for r in rows).items())),
                        rows=rows)
    return per_k


def resource_summary(G=3):
    per_k = resource_rows(G)
    tot = sum(v["arithmetic_rows"] for v in per_k.values())
    ref = sum(v["heavy_refined_rows"] for v in per_k.values())
    # 길이 항등식 재확인: L = 867+k+J+delta+x+H, J = G-F
    bad = []
    for k, v in per_k.items():
        for r in v["rows"]:
            J = G - r["F"]
            L = 867 + k + J + r["delta"] + r["x"] + r["H"]
            if L > 871:
                bad.append((k, r))
            # e 상한
            if r["e"] > TYPES[r["type"]][0] + 1 - k:
                bad.append(("e-bound", k, r))
    return dict(per_k={k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                       for k, v in per_k.items()},
                arithmetic_total=tot, heavy_refined_total=ref,
                astra_claims=dict(arithmetic=516, heavy_refined=580,
                                  per_k={4: 9, 3: 46, 2: 139, 1: 322},
                                  per_k_refined={4: 9, 3: 46, 2: 148, 1: 377}),
                matches_516=(tot == 516), matches_580=(ref == 580),
                per_k_matches=all(per_k[k]["arithmetic_rows"] == v
                                  for k, v in {4: 9, 3: 46, 2: 139, 1: 322}.items()),
                per_k_refined_matches=all(per_k[k]["heavy_refined_rows"] == v
                                          for k, v in {4: 9, 3: 46, 2: 148,
                                                       1: 377}.items()),
                length_violations=len(bad),
                identities=dict(P=120 + G, D_formula="5k-G",
                                D_by_k={k: 5 * k - G for k in range(1, 5)},
                                length="L = 867+k+J+delta+x+H, J=G-F",
                                condition="delta+x+H <= F+1-k"))


if __name__ == "__main__":
    res = dict(patterns=multiplicity_patterns(3),
               incidence=incidence_theorem(3),
               resources=resource_summary(3))
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_r140_g3_140.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1)[:4000])
