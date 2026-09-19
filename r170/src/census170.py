#!/usr/bin/env python3
"""Round 170 -- an independent census run over the exact 35-cell basis.

`checkbasis170.py` audited the COMBINATORICS of the minimum (monotonicity,
necessity, sufficiency, minimality).  It did not audit the VALUES, and that is
the part where a table can leak in.

The census reads capacities from round 152's tables.  Those tables are the
historical record of a search, not a certificate, so a basis that closes all
180 rows "at exact values" is only as sound as those values.  What a
production plan can actually certify for cell K is its census-safe bound S(K),
which is weaker than the exact capacity -- 115 against 106 for
`0|15|0|0|0|1`.  So the census is re-run here with every basis cell held at
its JOINT-safe bound and nothing at an exact historical value, which is the
assignment a plan would really deliver.

Three things are required, and the third is the one usually skipped:

  1. all 180 exposed rows close;
  2. the two EQUALITY rows of the 1,609-row baseline stay EQUALITY -- neither
     promoted to strictly closed nor lost, since either would mean the
     capacity model moved;
  3. the leak is accounted for cell by cell: which basis cells have a genuine
     dual-verified certificate behind the value used, and which are still
     standing on the historical table.

The lower bound is re-checked too, from the coordinates up, so that "34 is
impossible" does not rest on the same run that proposed 35.
"""
from __future__ import annotations
import hashlib, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    cost = json.loads((ROOT / "r170" / "certs" / "cost_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = sorted(set([parse(c) for c in src["minimum"]["cells"]]
                       + [parse(c) for c in
                          bas["minimum"]["witness_completion"]]))
    joint = {parse(r["cell"]): r["joint_S"] for r in cost["plan"]
             if r["joint_S"] is not None}

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    tally_full = Counter(base.values())
    eq_rows = sorted(k for k, v in base.items() if v == "EQUALITY")
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)
    print(f"baseline {len(base)} rows: {dict(tally_full)}", flush=True)
    print(f"exposed rows {len(EX)}; equality rows {len(eq_rows)}", flush=True)

    t0 = time.time()

    # ---- 1 and 2: the census at JOINT-SAFE values only
    S.apply(set(BASIS), values={K: joint[K] for K in BASIS if K in joint})
    v_safe = S.verdicts()
    open_rows = [k for k in EX if v_safe[k] != "STRICTLY_CLOSED"]
    eq_after = {k: v_safe[k] for k in eq_rows}
    eq_held = all(v == "EQUALITY" for v in eq_after.values())
    print(f"at joint-safe bounds: {len(EX) - len(open_rows)}/{len(EX)} "
          f"exposed rows closed; equality rows held: {eq_held}", flush=True)

    # ---- 3: leak accounting
    genuine = {}
    for rel in ("r170/certs/genuine_target_h_170.json",
                "r170/certs/genuine_target_a2_170.json"):
        p = ROOT / rel
        if p.exists():
            r = json.loads(p.read_text())
            if r.get("ok"):
                genuine[parse(r["cell"])] = dict(
                    bound=r["census_safe_bound_S"], certificate=r["stored"])
    vb = json.loads((ROOT / "r170" / "certs"
                     / "verification_b_h_170.json").read_text())
    dag_cells = {parse(c) for c in vb["certified_cells"]}

    leak = []
    for K in BASIS:
        g = genuine.get(K)
        if g and g["bound"] >= joint.get(K, 10 ** 9):
            backing = "GENUINE_CERTIFICATE"
        elif K in dag_cells:
            backing = "GENUINE_CERTIFICATE_IN_DAG"
        else:
            backing = "HISTORICAL_TABLE_ONLY"
        leak.append(dict(cell=cellstr(K), value_used=joint.get(K),
                         backing=backing,
                         certificate=g["certificate"] if g else None))
    tally_leak = Counter(r["backing"] for r in leak)
    print(f"value backing: {dict(tally_leak)}", flush=True)

    # ---- the lower bound, re-derived
    E = {parse(c) for c in src["minimum"]["cells"]}
    single = {K for K in S.chain_tab if K not in S.dual_chain}
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    univ = sorted({parse(c) for c in st["universe_cells"]} | single)

    def closed(sel, rows):
        S.apply(sel)
        v = S.verdicts(rows)
        return {k for k in rows if v[k] == "STRICTLY_CLOSED"}

    R = EXS - closed(E, EXS)
    best1, one_ok = 0, None
    for K in sorted(set(univ) - E, key=cellstr):
        n = len(closed(E | {K}, R))
        if n > best1:
            best1, one_ok = n, cellstr(K)
    thirty_four = best1 == len(R)
    print(f"lower bound recheck: residual {len(R)}, best single covers "
          f"{best1} ({one_ok}) -> 34 {'POSSIBLE' if thirty_four else 'IMPOSSIBLE'}",
          flush=True)

    out = dict(
        inputs={p: sha(p) for p in ("r170/certs/basis_170.json",
                                    "r170/certs/cost_170.json",
                                    "r169/certs/p1_closure_169.json")},
        baseline=dict(rows=len(base), tally=dict(tally_full),
                      reproduces_round_152=(tally_full["STRICTLY_CLOSED"] == 1607
                                            and tally_full["EQUALITY"] == 2)),
        basis_size=len(BASIS),
        census_at_joint_safe_bounds=dict(
            exposed_rows=len(EX),
            closed=len(EX) - len(open_rows),
            still_open=[list(k[1]) for k in open_rows],
            all_closed=not open_rows,
            note="run with every basis cell at its joint-safe bound and no "
                 "cell at an exact historical capacity; this is the "
                 "assignment a production plan can actually certify"),
        equality_rows=dict(
            count=len(eq_rows),
            verdicts_after={str(k[1]): v for k, v in eq_after.items()},
            both_held=eq_held,
            why="a promotion to strictly closed or a loss would both mean the "
                "capacity model moved, not that the basis improved"),
        value_backing=dict(tally=dict(tally_leak), per_cell=leak,
                           genuinely_backed=tally_leak.get(
                               "GENUINE_CERTIFICATE", 0)
                           + tally_leak.get("GENUINE_CERTIFICATE_IN_DAG", 0),
                           historical_table_only=tally_leak.get(
                               "HISTORICAL_TABLE_ONLY", 0)),
        lower_bound_recheck=dict(
            residual_rows=len(R),
            best_single_covers=best1,
            best_single_cell=one_ok,
            thirty_four_possible=thirty_four,
            independent="re-derived from the coordinates in this process, not "
                        "read from basis_170.json"),
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["verdict"] = ("CENSUS_INDEPENDENTLY_CONFIRMED"
                      if (not open_rows and eq_held and not thirty_four
                          and out["baseline"]["reproduces_round_152"])
                      else "CENSUS_CHECK_FAILED")
    out["ok"] = out["verdict"] == "CENSUS_INDEPENDENTLY_CONFIRMED"
    (ROOT / "r170" / "certs" / "census_audit_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "value_backing")},
                     ensure_ascii=False, indent=1))
    print("value_backing tally:", json.dumps(dict(tally_leak)))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
