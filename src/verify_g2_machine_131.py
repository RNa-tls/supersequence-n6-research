#!/usr/bin/env python3
"""라운드 131 §11 — **새 가지치기의 양성 대조**.

라운드 130 의 짧은-pass 상태 기계 위에 라운드 131 이 추가한 세 규칙

* **규칙 R** (정리 131.1(b)) — 반복 run 은 지정된 자유 `ν`-하강의 `ω = 2` 탈출만 연다;
* **조건부 lock** (정리 131.1(c)) — 상승 lock 은 목표 궤도가 *알려진* 반복 궤도와 다를 때만
  걸고, 판정 불가한 자리는 `LOCK0MODE` 의 α/β 두 갈래가 덮는다;
* **잎 검사** — `#반복 run = e` 이고 `r = O + e`

를 파이썬으로 **엔진과 같은 순서로** 다시 구현해 합법 `n = 4` walk 에 적용한다.
거짓 기각이 하나라도 있으면 그 규칙은 `n = 6` 탐색에 쓸 수 없다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup, legal_joint          # noqa: E402
from verify_fg_repair_128 import walk_measure                   # noqa: E402
from verify_g2_machine_130 import replay_machine                # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def _sids(passes, hexes, n):
    """엔진의 slot id 를 walk 에 붙인다.  유형 A: walk 순서 = ν 순서(= AORDER 1) 의 호 번호.
    유형 B: `2·slot + (0 = opener, 1 = closer)`, slot 은 육각형이 처음 나온 순서."""
    cnt = Counter(hexes)
    multi = [h for h in dict.fromkeys(hexes) if cnt[h] >= 2]
    sid = [-1] * len(passes)
    if len(multi) == 1 and cnt[multi[0]] == 3:
        arcs = [i for i in range(len(passes)) if hexes[i] == multi[0]]
        for j, i in enumerate(arcs):
            sid[i] = j
        return sid, "A"
    if len(multi) == 2 and all(cnt[h] == 2 for h in multi):
        for s, h in enumerate(multi):
            ps = [i for i in range(len(passes)) if hexes[i] == h]
            sid[ps[0]] = 2 * s
            sid[ps[1]] = 2 * s + 1
        return sid, "B"
    return sid, "?"


def replay_rules_131(g, m, lock0mode):
    """엔진의 라운드-131 규칙을 그대로 재생한다.  walk 을 받아들이면 (True, None)."""
    n = g["n"]
    orbid, hexid = g["orbid"], g["hexid"]
    passes, hexes, nu = m["passes"], m["hexes"], m["nu"]
    P = len(passes)
    sid, typ = _sids(passes, hexes, n)
    if typ == "?":
        return False, "not a G=2 multiplicity type"
    mtype = 0 if typ == "A" else 1

    # 이 walk 이 실제로 갖는 자유 탈출 패턴에서 FREESPEC/REVSPEC/LOCKSPEC 을 읽는다.
    orbs = [orbid[u] for (u, _) in passes]
    runs, cur = [], [0]
    for i in range(1, P):
        if orbs[i] == orbs[i - 1]:
            cur.append(i)
        else:
            runs.append(cur)
            cur = [i]
    runs.append(cur)
    runof = [0] * P
    for ri, r in enumerate(runs):
        for p in r:
            runof[p] = ri
    oms = []
    for i in range(P - 1):
        oms.append(n - passes[i][1] if orbs[i + 1] != orbs[i] or True else 0)
    # joint weight between pass i and i+1 = omega; recover it from the pass lengths:
    # a pass of length L consumes L letters, so omega(i) = L_i - (overlap) ; instead use
    # the recorded structure: a free (omega = 2) joint is exactly the one whose successor
    # entry equals tau(entry(nu(p))).
    ta, idx, perms = g["tau"], g["idx"], g["perms"]
    free = [False] * P
    for i in range(P - 1):
        free[i] = (idx[ta(perms[passes[nu[i]][0]])] == passes[i + 1][0])

    revspec = sum(1 << sid[i] for i in range(P - 1)
                  if free[i] and sid[i] >= 0 and nu[i] < i and orbs[i + 1] != orbs[i])
    lockspec = sum(1 << sid[i] for i in range(P) if sid[i] >= 0 and nu[i] > i)

    # ---- 엔진 순서 그대로 재생 -------------------------------------------------
    amask, av, bo, bc, bov = 0, -1, 0, 0, [-1, -1]
    seen = set()
    nrev = 0
    lockorb, lockwait, pend, q0orb = -1, -1, -1, -1

    def revorb_of(d):
        if mtype == 0:
            return (orbid[av], True) if (amask & 1) else (-1, False)
        s = d >> 1
        return (orbid[bov[s]], True) if s < bo else (-1, False)

    u0 = passes[0][0]
    seen.add(orbs[0])
    if sid[0] == 0:
        if mtype == 0:
            av, amask = u0, 1
        else:
            bov[0], bo = u0, 1
    pend = 0 if (sid[0] >= 0 and (lockspec >> sid[0]) & 1) else -1
    cursid = sid[0]

    for i in range(P - 1):
        w = passes[i + 1][0]
        nq = orbid[w]
        c = 0 if free[i] else 1
        same = (nq == orbs[i])
        fresh = nq not in seen
        rv = 1 if (not same and not fresh) else 0
        # --- 규칙 R --------------------------------------------------------
        if rv:
            if c != 0:
                return False, "R: repeat run opened by a costly joint"
            if cursid < 0 or not ((revspec >> cursid) & 1):
                return False, "R: repeat run not opened by a designated free descent"
            nrev += 1
        # --- lockorb 강제 ---------------------------------------------------
        if lockorb >= 0 and nq != lockorb:
            return False, "lock: walk left the locked orbit before nu(p)"
        # --- 새 pass 등록 (엔진과 같은 순서: lock 판정 전에) -----------------
        s2 = sid[i + 1]
        if s2 >= 0:
            if mtype == 0:
                if amask == 0:
                    av = w
                amask |= 1 << s2
            elif s2 % 2 == 0:
                bov[s2 // 2] = w
                bo += 1
            else:
                bc += 1
        # --- beta 갈래의 필요조건 ------------------------------------------
        if lock0mode == 0 and mtype != 0 and s2 == 2:
            if q0orb < 0 or nq != q0orb:
                return False, "beta: orb(entry(opener1)) != Q(opener0)"
        # --- 조건부 lock ----------------------------------------------------
        nlo, nlw = lockorb, lockwait
        if pend >= 0 and c == 0:
            unknown = risky = False
            for d in range(4):
                if not ((revspec >> d) & 1):
                    continue
                ro, kn = revorb_of(d)
                if not kn:
                    unknown = True
                elif ro == nq:
                    risky = True
            apply_ = (not risky) and (True if not unknown else (lock0mode == 1))
            if apply_:
                nlo, nlw = nq, (sid[nu[i]] if sid[i] >= 0 else -1)
            if lock0mode == 0 and mtype != 0 and pend == 0:
                q0orb = nq
        if s2 >= 0 and nlw == s2:
            nlo, nlw = -1, -1
        lockorb, lockwait = nlo, nlw
        pend = s2 if (s2 >= 0 and (lockspec >> s2) & 1) else -1
        cursid = s2
        seen.add(nq)

    # --- 잎 검사 ------------------------------------------------------------
    if nrev != m["e"]:
        return False, "leaf: #repeat runs != e"
    if len(runs) != len(seen) + m["e"]:
        return False, "leaf: r != O + e"
    return True, None


def n4_control(maxlen=39):
    """§11 — 세 대조군 전부에서 거짓 기각이 0 이어야 한다."""
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
    rejects = []
    boundary = []
    for L, seq in ws:
        m = walk_measure(g, W, seq, L)
        if m["G"] != 2:
            continue
        stat["G2"] += 1
        typ = "A" if m["partition"] == (2,) else ("B" if m["partition"] == (1, 1) else "?")
        # 대조군 2 — 모든 유형 A / G = 2 예제 (라운드 130 기계가 그대로 받아야 한다)
        if typ == "A":
            stat["typeA"] += 1
            ok130, _ = replay_machine(n, g, m["passes"], m["hexes"], m["F"])
            if not ok130:
                stat["REJECT_130_typeA"] += 1
        # 대조군 3 — e = 1 경계 현상 (유형 A, f_out = 3, e = 1)
        if typ == "A" and m["f_out"] == 3 and m["e"] == 1:
            boundary.append((L, seq))
            stat["boundary_e1"] += 1
        # 대조군 1 — 새 규칙의 건전성 가설은 **등호 `f_out = F + e` 하나뿐**이다.
        # (`x = 0` 과 `F = 2` 는 엔진의 별개 제약이지 이 규칙들의 전제가 아니므로
        #  대조군을 그것으로 좁히지 않는다 — 좁히면 e >= 1 예제가 전부 빠진다.)
        if m["f_out"] != m["F"] + m["e"]:
            continue
        stat["in_scope"] += 1
        stat[f"scope_{typ}_F{m['F']}_e{m['e']}"] += 1
        acc = [lm for lm in (2, 1, 0) if replay_rules_131(g, m, lm)[0]]
        if acc:
            stat["accept"] += 1
            stat["accept_lock0mode_" + "".join(str(a) for a in sorted(acc))] += 1
        else:
            stat["REJECT"] += 1
            if len(rejects) < 5:
                _, why = replay_rules_131(g, m, 2)
                rejects.append(dict(L=L, type=typ, e=m["e"], f_out=m["f_out"], why=why))
    # 대조군 3 을 규칙으로 다시 돌린다 (범위 안에 드는 것만)
    bstat = Counter()
    for L, seq in boundary:
        m = walk_measure(g, W, seq, L)
        bstat["total"] += 1
        if m["f_out"] == m["F"] + m["e"]:
            bstat["in_scope"] += 1
            if any(replay_rules_131(g, m, lm)[0] for lm in (2, 1, 0)):
                bstat["accept"] += 1
            else:
                bstat["REJECT"] += 1
    return dict(
        n=4, maxlen=maxlen, walks=len(ws), G2_walks=stat["G2"],
        typeA_walks=stat["typeA"], typeA_rejected_by_round130_machine=stat["REJECT_130_typeA"],
        boundary_e1_examples=stat["boundary_e1"],
        boundary_replay={k: v for k, v in sorted(bstat.items())},
        in_scope=stat["in_scope"], accepted=stat["accept"], rejected=stat["REJECT"],
        false_rejection=stat["REJECT"],
        lock0mode_breakdown={k: v for k, v in sorted(stat.items())
                             if k.startswith("accept_lock0mode")},
        in_scope_breakdown={k: v for k, v in sorted(stat.items())
                            if k.startswith("scope_")},
        reject_examples=rejects,
        clean=(stat["REJECT"] == 0 and stat["REJECT_130_typeA"] == 0
               and bstat["REJECT"] == 0))


def synthetic_ae1_block(n=6):
    """§11 대조군 4 — `A/e=1` 이 강제하는 국소 배치를 **합성**해 규칙이 안 거부하는지 본다.

    `arc0 → (4 full) → arc1 → (4 full) → arc2 → R₂ 첫 pass` 를 실제 `n = 6` 기하로 만든다.
    """
    g = setup(n)
    perms, idx, sg, ta = g["perms"], g["idx"], g["sig"], g["tau"]
    orbid, hexid, orbph = g["orbid"], g["hexid"], g["orbph"]
    out = []
    for l0 in range(1, 5):
        for l1 in range(1, 6 - l0):
            l2 = n - l0 - l1
            v0 = 0                                   # S6 대칭으로 한 단어를 고정
            v1 = idx[_sigk(sg, perms[v0], l0)]
            v2 = idx[_sigk(sg, perms[v1], l1)]
            back = idx[_sigk(sg, perms[v2], l2)]
            ok = (back == v0)
            q0, q1, q2 = orbid[v1], orbid[v2], orbid[v0]
            distinct = len({q0, q1, q2}) == 3
            # S1 = [tau(v1) .. arc1]:  tau(v1) 의 궤도는 orb(v1) 이고 arc1 은 그 τ-사슬의 5번째
            s1_start = idx[ta(perms[v1])]
            s1_ok = (orbid[s1_start] == q0
                     and (orbph[v1] - orbph[s1_start]) % (n - 1) == n - 2)
            s2_start = idx[ta(perms[v2])]
            s2_ok = (orbid[s2_start] == q1
                     and (orbph[v2] - orbph[s2_start]) % (n - 1) == n - 2)
            r2_start = idx[ta(perms[v0])]
            r2_ok = (orbid[r2_start] == q2
                     and (orbph[v0] - orbph[r2_start]) % (n - 1) == n - 2)
            same_hex = (hexid[v0] == hexid[v1] == hexid[v2])
            out.append(dict(split=f"{l0}{l1}{l2}", sigma_cycle_closes=ok,
                            same_hexagon=same_hex, three_orbits_distinct=distinct,
                            S1_is_5_passes=s1_ok, S2_is_5_passes=s2_ok,
                            R2_starts_at_tau_v0=r2_ok))
    return dict(n=n, n_splits=len(out), rows=out,
                clean=all(r["sigma_cycle_closes"] and r["same_hexagon"]
                          and r["three_orbits_distinct"] and r["S1_is_5_passes"]
                          and r["S2_is_5_passes"] and r["R2_starts_at_tau_v0"] for r in out))


def _sigk(sg, w, k):
    for _ in range(k):
        w = sg(w)
    return w


if __name__ == "__main__":
    d = dict(n4=n4_control(), synthetic=synthetic_ae1_block())
    print(json.dumps(d, ensure_ascii=False, indent=1))
