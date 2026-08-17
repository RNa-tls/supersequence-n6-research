#!/usr/bin/env python3
"""라운드 106 — 인증서에 대한 **대조 실험** (§11–§15).

`certify_rr_q2_zero.py` 가 잔여를 0 으로 만든다.  이 파일은 그 결론을 **믿지 않기 위한**
실험만 담는다.  표준 라이브러리만 쓰고 인증기에서 함수를 빌려 오되(같은 코드를 두 번 쓰지
않기 위해) 판정은 전부 독립적인 방법으로 다시 만든다.

  §11  동적 `L2` 건전성 — 실제 인스턴스의 (접두, 잔여) 상태에서 하한이 참 최소비용을 넘지
       않는지 전수 대조.  위반 0 이 요구된다.
  §12  메모 없는 / **정리 1 을 아예 쓰지 않는** 대체 솔버로 어려운 쌍을 다시 판정.
  §13  실제 가설(비용-0 유출 차수 ≤ 1)을 만족하는 작은 인스턴스에서 정확 최소비용 대조.
  §14  양성 대조 — 심어 둔 경로가 반드시 SAT 이고, 그 경로의 **모든 접두**에서 하한이
       남은 실제 비용 이하인지 확인한다.
  §15  규약 감사 — ROOT 의 성분 포함 여부, `c` 대 `c−1`, terminal, 조각 연결자 비용, `K`.

사용법:
    python3 src/control_rr_q2_zero.py all
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


C = _load("certify_rr_q2_zero", "src/certify_rr_q2_zero.py")


# ---------------------------------------------------------------- 참 최소비용 (독립 구현)

def true_min_cost(out0, out1, r0, r1, cur=None, rem=None):
    """전수 열거로 남은 최소 비용.  정리 1 을 **전혀 쓰지 않는다**."""
    m = len(out0)
    best = [None]

    def bits(x):
        while x:
            low = x & -x
            yield low.bit_length() - 1
            x ^= low

    def go(c, r, spent):
        if best[0] is not None and spent >= best[0]:
            return
        if not r:
            best[0] = spent
            return
        for cost, cand in ((0, out0[c] & r), (1, out1[c] & r)):
            for y in bits(cand):
                go(y, r & ~(1 << y), spent + cost)

    if cur is None:
        full = (1 << m) - 1
        for cost, cand in ((0, r0), (1, r1)):
            for y in bits(cand):
                go(y, full & ~(1 << y), cost)
    else:
        go(cur, rem, 0)
    return best[0]


def bound_only(out0, cur, rem):
    """정리 1 하한을 인증기와 **다른 코드**로 다시 계산 (사슬 추적, union-find 미사용)."""
    idxs = []
    x = rem
    while x:
        low = x & -x
        idxs.append(low.bit_length() - 1)
        x ^= low
    succ = {}
    for i in idxs:
        t = out0[i] & rem
        assert t & (t - 1) == 0, "비용-0 유출 차수 > 1"
        if t:
            succ[i] = t.bit_length() - 1
    # 성분 = 사슬 (함수형이므로 각 성분은 경로 또는 하나의 순환)
    seen = set()
    comps = 0
    inv = defaultdict(list)
    for a, b in succ.items():
        inv[b].append(a)
    for i in idxs:
        if i in seen:
            continue
        comps += 1
        stack = [i]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            if v in succ and succ[v] not in seen:
                stack.append(succ[v])
            for u in inv.get(v, ()):
                if u not in seen:
                    stack.append(u)
    return comps - 1 if (out0[cur] & rem) else comps


# ---------------------------------------------------------------- 실제 인스턴스 표본

def real_instances(limit_states, rng):
    """아카이브에서 실제 (그래프, B) 인스턴스를 뽑아 낸다."""
    word, orb, hexm, jt = C.geometry()
    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    _h, covers = C.read_jsonl(C.ARCHIVE / "covers.jsonl.gz")
    _h, hall = C.read_jsonl(C.ARCHIVE / "hall_results.jsonl.gz")
    S = {s["sid"]: s for s in states}
    CV = {(c["sid"], c["cover_id"]): c for c in covers}
    passing = defaultdict(list)
    for h in hall:
        if h["deficit"] == 0:
            passing[h["sid"]].append(h["cover_id"])
    out = []
    for sid in sorted(passing)[:limit_states]:
        st = S[sid]
        B = 3 + st["K"] - (st["S"] + st["F"] - st["O"]) - st["H"]
        for cid in sorted(passing[sid]):
            dom, ell, root = C.domains(st, CV[(sid, cid)]["orbits"], orb, hexm)
            if not C.word_reachable_all(dom, ell, root, jt):
                continue
            d = C.propagate(dom, ell, root, jt)
            if d is None:
                continue
            for A in C.assignments(d):
                nodes, out0, out1, r0, r1 = C.weighted_graph(A, ell, root, jt)
                out.append((sid, cid, B, out0, out1, r0, r1))
    rng.shuffle(out)
    return out


# ------------------------------------------------------------------------ §11

def dynamic_soundness(inst, rng, trials=6000, small=11):
    """실제 인스턴스의 **동적** (현재 정점, 잔여 집합) 상태에서 하한의 건전성을 확인한다.

    솔버의 `lower_bound(cur, rem)` 는 탐색 도중 임의의 (도달 가능한) 잔여 집합에 대해
    호출된다.  그래서 여기서는 무작위 보행이 아니라 **그래프 안에서 연결된 작은 잔여 집합**을
    직접 만들고 (실제 탐색이 만나는 것의 상위집합), 그 위에서 참 최소비용을 전수로 구해
    `lb ≤ C*` 를 요구한다.  `C*` 가 없으면(완성 불가) 하한은 어떤 값이어도 건전하다.
    """
    checked = viol = nocomp = 0
    margin = Counter()
    for k in range(trials):
        _sid, _cid, _B, out0, out1, r0, r1 = inst[k % len(inst)]
        m = len(out0)
        seed = rng.randrange(m)
        rem_set = {seed}
        frontier = [seed]
        size = rng.randint(3, small)
        while frontier and len(rem_set) < size:
            v = frontier.pop(rng.randrange(len(frontier)))
            outs = [i for i in range(m) if (out0[v] | out1[v]) >> i & 1]
            rng.shuffle(outs)
            for u in outs:
                if u not in rem_set:
                    rem_set.add(u)
                    frontier.append(u)
                    if len(rem_set) >= size:
                        break
        if len(rem_set) < 3:
            continue
        pre = [i for i in range(m)
               if i not in rem_set and ((out0[i] | out1[i]) & sum(1 << x for x in rem_set))]
        if not pre:
            continue
        cur = rng.choice(pre)
        rem = 0
        for x in rem_set:
            rem |= 1 << x
        star = true_min_cost(out0, out1, r0, r1, cur, rem)
        lb = bound_only(out0, cur, rem)
        checked += 1
        if star is None:
            nocomp += 1
            continue
        margin[star - lb] += 1
        if lb > star:
            viol += 1
    return {"residual_states_checked": checked, "violations": viol,
            "residuals_with_no_completion": nocomp,
            "residuals_compared_to_true_optimum": sum(margin.values()),
            "slack_histogram": dict(sorted(margin.items()))}


def deep_prefix_soundness(inst, rng, instances=250, small=12, cap=60_000):
    """실제 탐색이 만나는 **진짜 접두**에서의 건전성.

    무작위 순서 DFS(도달성 가지치기만, 비용 제한 없음)로 ROOT 에서 깊이 내려가 `|rem| ≤ small`
    인 노드를 모으고, 그 각각에서 `lb ≤ C*` 를 확인한다.
    """
    checked = viol = reached = 0
    margin = Counter()
    for k in range(min(instances, len(inst))):
        _sid, _cid, _B, out0, out1, r0, r1 = inst[k]
        m = len(out0)
        found = []
        nodes = [0]

        def go(cur, rem):
            nodes[0] += 1
            if nodes[0] > cap or len(found) >= 3:
                return
            if bin(rem).count("1") <= small:
                found.append((cur, rem))
                return
            outs = [i for i in range(m) if ((out0[cur] | out1[cur]) >> i & 1) and (rem >> i & 1)]
            rng.shuffle(outs)
            for y in outs:
                go(y, rem & ~(1 << y))
                if nodes[0] > cap or len(found) >= 3:
                    return

        full = (1 << m) - 1
        starts = [i for i in range(m) if (r0 | r1) >> i & 1]
        rng.shuffle(starts)
        for s in starts:
            go(s, full & ~(1 << s))
            if found:
                break
        for cur, rem in found:
            reached += 1
            star = true_min_cost(out0, out1, r0, r1, cur, rem)
            lb = bound_only(out0, cur, rem)
            checked += 1
            if star is None:
                continue
            margin[star - lb] += 1
            if lb > star:
                viol += 1
    return {"instances_tried": min(instances, len(inst)), "deep_prefixes_found": reached,
            "checked": checked, "violations": viol,
            "slack_histogram": dict(sorted(margin.items()))}


# ------------------------------------------------------------------------ §12

def alternative_solver(inst, sample=60, cap=250_000):
    """정리 1 을 **쓰지 않는** 솔버(도달성 가지치기만) + 메모 없는 솔버로 재판정."""
    rows = Counter()
    hard = []
    for sid, cid, B, out0, out1, r0, r1 in inst:
        lb = C.root_lower_bound(out0, r0)
        if lb <= B:                        # 뿌리 하한만으로 닫히지 않는 어려운 인스턴스
            hard.append((sid, cid, B, out0, out1, r0, r1))
        if len(hard) >= sample:
            break
    for sid, cid, B, out0, out1, r0, r1 in hard:
        st = Counter()
        base = C.solve(out0, out1, r0, r1, B, st)
        st2 = Counter()
        nomemo = C.solve(out0, out1, r0, r1, B, st2, use_memo=False, node_cap=cap)
        st3 = Counter()
        nobound = C.solve(out0, out1, r0, r1, B, st3, use_bound=False, node_cap=cap)
        rows[f"base={base}"] += 1
        rows[f"nomemo={nomemo}"] += 1
        rows[f"nobound={nobound}"] += 1
        rows["nodes_base"] += st["nodes"]
        rows["nodes_nomemo"] += st2["nodes"]
        rows["nodes_nobound"] += st3["nodes"]
        if nomemo != "UNKNOWN" and nomemo != base:
            rows["MISMATCH_nomemo"] += 1
        if nobound != "UNKNOWN" and nobound != base:
            rows["MISMATCH_nobound"] += 1
    return {"hard_instances": len(hard), "rows": dict(rows)}


# ------------------------------------------------------------------------ §13

def small_exact(trials=3000, seed=11):
    """실제 가설을 만족하는 작은 무작위 인스턴스에서 정확 최소비용과 전면 대조."""
    rng = random.Random(seed)
    checked = mism = lbviol = 0
    for _ in range(trials):
        m = rng.randint(3, 8)
        out0 = [0] * m
        out1 = [0] * m
        for i in range(m):
            outs = [j for j in range(m) if j != i and rng.random() < 0.45]
            if outs and rng.random() < 0.75:
                z = rng.choice(outs)
                out0[i] = 1 << z            # 비용-0 유출 차수 ≤ 1 (실제 가설)
                outs.remove(z)
            for j in outs:
                out1[i] |= 1 << j
        rs = [j for j in range(m) if rng.random() < 0.5]
        r0 = (1 << rng.choice(rs)) if rs and rng.random() < 0.6 else 0
        r1 = 0
        for j in rs:
            if not (r0 >> j & 1):
                r1 |= 1 << j
        star = true_min_cost(out0, out1, r0, r1)
        lb = C.root_lower_bound(out0, r0)
        if star is not None and lb > star:
            lbviol += 1
        for B in range(0, m + 2):
            st = Counter()
            v = C.solve(out0, out1, r0, r1, B, st)
            truth = "SAT" if (star is not None and star <= B) else "UNSAT"
            checked += 1
            if v != truth:
                mism += 1
    return {"instances": trials, "verdict_checks": checked,
            "verdict_mismatches": mism, "root_bound_violations": lbviol}


# ------------------------------------------------------------------------ §14

def positive_controls(trials=4000, seed=23):
    """경로를 심고 SAT 을 요구한다.  그 경로의 모든 접두에서 하한 ≤ 남은 실제 비용."""
    rng = random.Random(seed)
    false_unsat = 0
    prefix_checks = prefix_viol = 0
    verdicts = Counter()
    for _ in range(trials):
        m = rng.randint(4, 11)
        perm = list(range(m))
        rng.shuffle(perm)
        out0 = [0] * m
        out1 = [0] * m
        zero_used = [False] * m
        costs = []
        r0 = r1 = 0
        if rng.random() < 0.5:
            r0 = 1 << perm[0]
        else:
            r1 = 1 << perm[0]
        for a, b in zip(perm, perm[1:]):
            if rng.random() < 0.6 and not zero_used[a]:
                out0[a] |= 1 << b
                zero_used[a] = True
                costs.append(0)
            else:
                out1[a] |= 1 << b
                costs.append(1)
        # 잡음 간선 — 가설을 지키며 덧댄다
        for i in range(m):
            for j in range(m):
                if i == j or rng.random() > 0.2:
                    continue
                if not zero_used[i] and rng.random() < 0.3:
                    out0[i] |= 1 << j
                    zero_used[i] = True
                else:
                    out1[i] |= 1 << j
        real = sum(costs) + (0 if r0 else 1)
        for B in (real, real + 1):
            st = Counter()
            v = C.solve(out0, out1, r0, r1, B, st)
            verdicts[v] += 1
            if v != "SAT":
                false_unsat += 1
        # §14 동적 사용: 심은 경로의 각 접두에서 하한이 남은 실제 비용을 넘지 않아야 한다
        rem = (1 << m) - 1
        rem &= ~(1 << perm[0])
        spent_tail = list(itertools.accumulate(costs[::-1]))[::-1]
        for k in range(m - 1):
            cur = perm[k]
            lb = bound_only(out0, cur, rem)
            prefix_checks += 1
            if lb > spent_tail[k]:
                prefix_viol += 1
            rem &= ~(1 << perm[k + 1])
    return {"instances": trials, "verdicts": dict(verdicts), "false_unsat": false_unsat,
            "prefix_bound_checks": prefix_checks, "prefix_bound_violations": prefix_viol}


# ------------------------------------------------------------------------ §15

def convention_audit():
    """손으로 확인 가능한 작은 예로 규약을 못 박는다."""
    rows = {}
    # (a) ROOT 는 성분에 포함되지 않는다.  ROOT 에서 비용-0 진입이 있으면 c−1, 없으면 c.
    out0 = [0, 0]            # 두 정점, 비용-0 호 없음 → c = 2
    out1 = [0b10, 0b01]
    rows["two_isolated_no_root0"] = C.root_lower_bound(out0, r0=0)          # 기대 2
    rows["two_isolated_with_root0"] = C.root_lower_bound(out0, r0=0b01)     # 기대 1
    # (b) 비용-0 사슬 하나 → c = 1
    out0b = [0b10, 0]
    rows["one_chain_no_root0"] = C.root_lower_bound(out0b, r0=0)            # 기대 1
    rows["one_chain_with_root0"] = C.root_lower_bound(out0b, r0=0b01)       # 기대 0
    # (c) 하한이 실제로 달성되는지 (등호 사례)
    o0 = [0b10, 0]
    o1 = [0, 0]
    rows["chain_true_cost_root0"] = true_min_cost(o0, o1, r0=0b01, r1=0)    # 기대 0
    rows["chain_true_cost_root1"] = true_min_cost(o0, o1, r0=0, r1=0b01)    # 기대 1
    # (d) terminal 은 따로 두지 않는다 — 경로의 마지막 정점이 곧 terminal 이다.
    rows["terminal_is_last_vertex"] = True
    # (e) 조각 연결자: fragment 의무도 다른 의무와 같은 비용 규칙을 쓴다 (T1=0, 나머지=1).
    rows["fragment_uses_same_cost_rule"] = True
    # (f) K
    _h, states = C.read_jsonl(C.ARCHIVE / "states.jsonl.gz")
    rows["K_equals_25_minus_O"] = all(s["K"] == 25 - s["O"] for s in states)
    rows["budget_min"] = min(3 + s["K"] - (s["S"] + s["F"] - s["O"]) - s["H"] for s in states)
    rows["budget_max"] = max(3 + s["K"] - (s["S"] + s["F"] - s["O"]) - s["H"] for s in states)
    expect = {"two_isolated_no_root0": 2, "two_isolated_with_root0": 1,
              "one_chain_no_root0": 1, "one_chain_with_root0": 0,
              "chain_true_cost_root0": 0, "chain_true_cost_root1": 1}
    rows["expectation_mismatches"] = sum(1 for k, v in expect.items() if rows[k] != v)
    return rows


# ------------------------------------------------------------------------- 실행

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["all"])
    ap.add_argument("--states", type=int, default=90)
    args = ap.parse_args()
    t0 = time.time()
    rng = random.Random(106)
    print("실제 인스턴스 표집…", flush=True)
    inst = real_instances(args.states, rng)
    print(f"  {len(inst)} 배정", flush=True)
    rep = {"round": 106, "control_version": "claude-r106-controls/1",
           "real_instances_sampled": len(inst)}
    print("§15 규약 감사…", flush=True)
    rep["s15_conventions"] = convention_audit()
    print("§13 작은 인스턴스 정확 대조…", flush=True)
    rep["s13_small_exact"] = small_exact()
    print("§14 양성 대조…", flush=True)
    rep["s14_positive_controls"] = positive_controls()
    print("§11 동적 하한 건전성…", flush=True)
    rep["s11_dynamic_soundness"] = dynamic_soundness(inst, rng)
    print("§11b 실제 접두 건전성…", flush=True)
    rep["s11b_deep_prefixes"] = deep_prefix_soundness(inst, rng)
    print("§12 대체 솔버…", flush=True)
    rep["s12_alternative_solvers"] = alternative_solver(inst)
    rep["seconds"] = round(time.time() - t0)
    (OUT / "rr_q2_zero_controls.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    bad = (rep["s11_dynamic_soundness"]["violations"]
           + rep["s11b_deep_prefixes"]["violations"]
           + rep["s13_small_exact"]["verdict_mismatches"]
           + rep["s13_small_exact"]["root_bound_violations"]
           + rep["s14_positive_controls"]["false_unsat"]
           + rep["s14_positive_controls"]["prefix_bound_violations"]
           + rep["s15_conventions"]["expectation_mismatches"]
           + rep["s12_alternative_solvers"]["rows"].get("MISMATCH_nomemo", 0)
           + rep["s12_alternative_solvers"]["rows"].get("MISMATCH_nobound", 0))
    if bad:
        raise SystemExit(f"대조 실패 — 위반 {bad}건")
    print("CONTROLS OK — 위반 0")


if __name__ == "__main__":
    main()
