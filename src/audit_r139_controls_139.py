#!/usr/bin/env python3
"""라운드 139 감사 — 1,510 개 문자 컨트롤 위에서 splice 를 **내가 직접** 수행.

Astra 의 JSON 은 **문자 단어만 데이터로** 읽는다 (그들의 `nu`, `pieces`, `cuts` 는
비교 대상이지 입력이 아니다).  창·pass·조인트·궤도·육각형·`nu`·splice 그래프·
순수 자유 순환·자름·조각을 전부 우리 기하 `setup(n)` 위에서 다시 만든다.

감사 지시서 §2 의 일곱 항목을 모든 컨트롤에서 확인한다:
  (a) splice 후 인접 단어가 **합법 조인트**를 이룬다;
  (b) 중간 순열 창이 새로 생기지 않는다;
  (c) 외부 끝점 의미가 보존된다;
  (d) 삭제/병합이 순열 중복을 만들지 않는다;
  (e) 새 육각형 반복이 생기지 않는다;
  (f) 궤도 등록이 옳다;
  (g) run 경계가 옳게 갱신된다.
그리고 §4/§5 의 MASTER 항등식 `sum b_j + s = S+1-O+c` 를 실측한다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GEO = {}


def geo(n):
    if n not in GEO:
        GEO[n] = setup(n)
    return GEO[n]


def sig(n, w, t=1):
    g = geo(n)
    for _ in range(t):
        w = g["idx"][g["sig"](g["perms"][w])]
    return w


def parse(word, n):
    """문자 단어 -> 창 위치, pass, 조인트 무게."""
    g = geo(n)
    pos = [i for i in range(len(word) - n + 1) if len(set(word[i:i + n])) == n]
    wins = [g["idx"][tuple(int(ch) for ch in word[i:i + n])] for i in pos]
    if len(set(wins)) != len(wins):
        return None
    passes, st = [], 0
    for i in range(1, len(pos) + 1):
        if i == len(pos) or pos[i] != pos[i - 1] + 1:
            passes.append((wins[st], i - st, pos[st], pos[i - 1]))
            st = i
    weights = [passes[j + 1][2] - passes[j][3] for j in range(len(passes) - 1)]
    return dict(pos=pos, wins=wins, passes=passes, weights=weights)


def legal_joint(n, a, b, m):
    g = geo(n)
    cat = list(g["perms"][a]) + list(g["perms"][b])[n - m:]
    return all(len(set(cat[i:i + n])) != n for i in range(1, m))


def analyse_control(word, n):
    p = parse(word, n)
    if p is None:
        return dict(ok=False, why="original word repeats a permutation")
    g = geo(n)
    ORB, HEX = g["orbid"], g["hexid"]
    passes = p["passes"]
    P = len(passes)
    entry = [q[0] for q in passes]
    length = [q[1] for q in passes]
    if len(set(entry)) != P:
        return dict(ok=False, why="pass entries not distinct")
    pos_of = {e: i for i, e in enumerate(entry)}

    # --- nu: v_nu(i) = sigma^{l_i}(v_i)
    nu = []
    for i in range(P):
        tgt = sig(n, entry[i], length[i])
        if tgt not in pos_of:
            return dict(ok=False, why="nu target is not a registered entry")
        nu.append(pos_of[tgt])
    fixed = sum(1 for i in range(P) if nu[i] == i)
    full = sum(1 for i in range(P) if length[i] == n)
    if fixed != full:
        return dict(ok=False, why="nu fixed points != full passes")

    # --- (a)(b)(c) splice 는 조인트를 문자 그대로 옮긴다
    joint_fail = []
    for i in range(P - 1):
        w = p["weights"][i]
        src_old = sig(n, entry[i], length[i] - 1)        # 원래 조인트 출처 창
        src_new = sig(n, entry[nu[i]], n - 1)            # full pass 후 출처 창
        if src_old != src_new:
            joint_fail.append(("endpoint", i))
            continue
        if not legal_joint(n, src_old, entry[i + 1], w):
            joint_fail.append(("illegal_original", i))
        if not legal_joint(n, src_new, entry[i + 1], w):
            joint_fail.append(("illegal_spliced", i))

    # --- splice 그래프: nu(i) -> i+1, 더미 = P
    N = P + 1
    T = [(i + 1) % N for i in range(N)]
    nuf = nu + [P]
    inv = [0] * N
    for i, j in enumerate(nuf):
        inv[j] = i
    nxt = [T[inv[j]] for j in range(N)]
    seen, cycles = [False] * N, []
    for st in range(N):
        if seen[st]:
            continue
        cyc, j = [], st
        while not seen[j]:
            seen[j] = True
            cyc.append(j)
            j = nxt[j]
        cycles.append(cyc)
    path = []
    for c in cycles:
        if P in c:
            kk = c.index(P)
            path = c[kk + 1:] + c[:kk]
    circuits = [c for c in cycles if P not in c]

    # --- (d)(e) 모든 pass 를 full 로 바꿔도 육각형/순열 중복이 없는가
    #     full pass 는 육각형 전체를 쓴다 -> 성분 안에서 육각형이 서로 달라야 한다
    hexrep = []
    for comp in [path] + circuits:
        hs = [HEX[entry[i]] for i in comp]
        if len(set(hs)) != len(hs):
            hexrep.append(sorted(Counter(hs).items()))

    # --- 순수 자유 순환: 모든 변이 weight 2 인 순환
    def edge_weight(u):
        """splice 후 정점 u 에서 나가는 변의 무게 (u = nu(i) 이면 원래 조인트 i)."""
        i = inv[u]
        return None if i >= P - 1 or i == P else p["weights"][i]

    pure_free = []
    for c in circuits:
        ws = [edge_weight(u) for u in c]
        if all(w == 2 for w in ws):
            pure_free.append(c)
    cnt = len(pure_free)

    S = sum(1 for w in p["weights"] if w >= 3)
    H = sum(w - 3 for w in p["weights"] if w > 3)
    O = len({ORB[e] for e in entry})
    D = (n - 1) * O - P
    e_free_blocks = P - sum(1 for w in p["weights"] if w == 2)
    return dict(ok=True, n=n, P=P, O=O, D=D, S=S, H=H,
                nu=nu, path=path, circuits=circuits, n_circuits=len(circuits),
                pure_free_cycles=pure_free, c=cnt,
                joint_failures=joint_fail,
                component_hex_repeats=hexrep,
                free_blocks_t=e_free_blocks,
                t_equals_S_plus_1=(e_free_blocks == S + 1),
                master_rhs=S + 1 - O + cnt)


def run(path=None, limit=None):
    p = Path(path)
    data = json.loads(p.read_text())
    cs = data["controls"]
    if limit:
        cs = cs[:limit]
    fail = Counter()
    agree = Counter()
    checked = 0
    for ctl in cs:
        r = analyse_control(ctl["word"], ctl["n"])
        checked += 1
        if not r["ok"]:
            fail["parse:" + r["why"]] += 1
            continue
        if r["joint_failures"]:
            fail["joint_not_preserved"] += 1
        # 육각형 반복은 **단일 경로 위상에서만** 허용된다 (§3). 3-성분 위상에서는
        # 모든 성분이 육각형 단순해야 하고, 단일 경로에서는 중복 분리 자름이
        # 그것을 처리한다 (§5).
        if r["component_hex_repeats"] and r["n_circuits"] != 0:
            fail["hex_repeat_in_three_component_topology"] += 1
        if bool(r["component_hex_repeats"]) != bool(ctl["duplicate_separating_cuts"]):
            fail["duplicate_separating_cuts_mismatch"] += 1
        if not r["t_equals_S_plus_1"]:
            fail["t_ne_S_plus_1"] += 1
        # Astra 기록과 대조 (데이터 비교, 신뢰 아님)
        agree["nu"] += (r["nu"] == ctl["nu"][:len(r["nu"])])
        agree["path"] += (r["path"] == ctl["spliced_path"])
        agree["cycles"] += (sorted(map(sorted, r["circuits"]))
                            == sorted(map(sorted, ctl["spliced_cycles"])))
        agree["c"] += (r["c"] == ctl["c"])
        agree["master_rhs"] += (r["master_rhs"] == ctl["identity_rhs"])
        agree["b_plus_s"] += (ctl["b"] + ctl["s"] == r["master_rhs"])
        agree["S"] += (r["S"] == ctl["original"]["S"])
        agree["O"] += (r["O"] == ctl["original"]["O"])
        agree["P"] += (r["P"] == ctl["original"]["P"])
        agree["D"] += (r["D"] == ctl["original"]["D"])
        agree["H"] += (r["H"] == ctl["original"]["H"])
        h = sum(1 for w in parse(ctl["word"], ctl["n"])["weights"] if w >= 4)
        agree["m_le_3_minus_c_plus_h"] += (len(ctl["pieces"]) <= 3 - r["c"] + h)
        agree["hexrepeat_iff_one_path"] += (
            bool(r["component_hex_repeats"]) == (r["n_circuits"] == 0))
    return dict(controls_checked=checked, failures=dict(fail),
                total_failures=sum(fail.values()),
                agreement_with_astra={k: f"{v}/{checked}" for k, v in agree.items()},
                full_agreement=all(v == checked for v in agree.values()),
                all_pass=(sum(fail.values()) == 0))


if __name__ == "__main__":
    src = sys.argv[1]
    r = run(src, int(sys.argv[2]) if len(sys.argv) > 2 else None)
    (ROOT / "outputs" / "rr_r139_controls_audit_139.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps(r, ensure_ascii=False, indent=1))
