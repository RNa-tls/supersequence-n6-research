#!/usr/bin/env python3
"""Round 168 phases 20-22 -- independence-restricted census and progress.

The census is rebuilt using ONLY facts the current proof system supports
twice:

  * capacity cells that already had two independent implementations;
  * cells carried by an exhaustion certificate that verifier B replayed in
    THIS run (never a value read from the round-152 table);
  * the bridge implications those two give, (BRIDGE-LE) and (BRIDGE-EQ);
  * the analytic fallbacks 120 + a + bb + e and 120.

Everything else is unavailable.  The two genuine equality rows must survive
as equality rows -- if either turned into a strict closure the restricted
system would be claiming more than the audited one, which is a defect.

Progress is reported on BOTH axes.  Certificates completed is the cheap
number; exposed rows independently closed is the one that measures proof.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import hidden163 as H                                             # noqa: E402
from recheck168 import System, parse, cellstr                     # noqa: E402

# round 165 stored the two equality rows as their COORD vectors only, so the
# layer is recovered by locating them in the row space rather than assumed.
EQ_ROWS = [(3, 0, 1, 0, 7, 0, 7, 0, 0, 0, 1),
           (4, 0, 0, 0, 6, 0, 6, 0, 0, 0, 0)]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verification", action="append", required=True,
                    help="verifier-B report(s) whose certified cells may be "
                         "used")
    ap.add_argument("--report", default="r168/certs/census_168.json")
    a = ap.parse_args()

    S = System()
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    assert st["ok"]
    EX = [(t, tuple(k)) for t, k in st["exposed_rows"]]
    OPT = {parse(c) for c in st["optimum"]}

    granted, sources = set(), {}
    for rel in a.verification:
        rep = json.loads((ROOT / rel).read_text())
        if not rep["all_ok"]:
            raise SystemExit(f"{rel} is not all_ok; nothing may be used")
        for c in rep["certified_cells"]:
            granted.add(parse(c))
            sources.setdefault(parse(c), rel)

    S.apply(granted)
    all_v = S.verdicts()
    tally = Counter(all_v.values())
    closed = [k for k in EX if all_v[k] == "STRICTLY_CLOSED"]
    still = [k for k in EX if all_v[k] != "STRICTLY_CLOSED"]
    # The two audited equality rows are located by their COORD vector.  Under
    # the restricted system many OTHER rows also fall back to equality or to
    # surviving -- that is the expected consequence of a weaker bound set.
    # What must not happen is either audited equality row becoming STRICTLY
    # CLOSED, which would mean the restricted system claims MORE than the
    # audited one.
    want = [tuple(r) for r in EQ_ROWS]
    found = sorted(k for k in all_v if tuple(k[1]) in want)
    eq = {f"E{i + 1}": dict(layer=867 + k[0], row=dict(zip(H.COORD, k[1])),
                            verdict=all_v[k])
          for i, k in enumerate(found)}

    # the remaining tail, recosted from the round-167 order
    plan = json.loads((ROOT / "r167" / "certs"
                       / "round168_plan_167.json").read_text())
    order = [(parse(r["cell"]), r["search_nodes"], r["basis"])
             for r in plan["generation_plan"]["order"]]
    left = [(K, n, w) for K, n, w in order if K not in granted]
    rem = sum(n for _K, n, _w in left)
    top = sorted(left, key=lambda x: -x[1])[:10]

    rates = json.loads((ROOT / "r168" / "certs" / "rates_168.json").read_text())
    ratio = rates["generator"]["cost_of_independence"]

    out = dict(
        inputs={p: sha(p) for p in
                ["r168/certs/state_168.json",
                 "r167/certs/round168_plan_167.json",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json"] + list(a.verification)},
        rule_system="dual-route facts + certificates replayed by verifier B "
                    "in this run + (BRIDGE-LE)/(BRIDGE-EQ) + analytic "
                    "fallbacks; every other round-152 value is unavailable",
        certificates=dict(
            required=len(OPT),
            certified=len(granted & OPT),
            remaining=len(OPT - granted),
            certified_outside_the_target=len(granted - OPT)),
        rows=dict(
            total=len(all_v), tally=dict(tally),
            exposed=len(EX),
            independently_closed=len(closed),
            still_open=len(still),
            equality=eq,
            equality_rows_found=len(found),
            equality_rows_intact=(len(found) == 2
                                  and all(v["verdict"] == "EQUALITY"
                                          for v in eq.values())),
            equality_rows_total_under_the_restricted_system=sum(
                1 for v in all_v.values() if v == "EQUALITY"),
            note="a strictly closed row can fall back to EQUALITY or "
                 "SURVIVING when the single-route facts are withdrawn; only "
                 "the 180 exposed rows are the ones round 168 has to win "
                 "back, and the two audited equality rows must stay "
                 "equality rows"),
        tail=dict(
            remaining_cells=len(left),
            remaining_projected_search_nodes=rem,
            remaining_expected_extree_nodes=int(rem * 1.1329),
            remaining_pessimistic_extree_nodes=int(rem * 1.4018),
            remaining_generation_nodes_with_discovery=int(rem * 2.11),
            top_10=[dict(cell=cellstr(K), projected_search_nodes=n, basis=w)
                    for K, n, w in top],
            fraction_of_remaining_cost_in_top_10=(
                round(sum(n for _K, n, _w in top) / rem, 4) if rem else 0.0),
            independence_cost=ratio),
        still_open_rows=[[k[0], list(k[1])] for k in still],
    )
    # a row outside the exposed set must not have opened: the exposed set is
    # by construction everything that CAN open when the single-route facts go
    outside = [k for k, v in all_v.items()
               if k not in set(EX) and v == "SURVIVING"]
    out["rows"]["unexpected_open_rows_outside_the_exposed_set"] = len(outside)
    out["ok"] = (out["rows"]["equality_rows_intact"] and not outside)
    out["complete"] = (out["certificates"]["remaining"] == 0
                       and out["rows"]["still_open"] == 0)
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "still_open_rows")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
