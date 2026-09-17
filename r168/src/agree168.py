#!/usr/bin/env python3
"""Round 168 phases 4 and 19 -- capacity agreement, after independent replay.

The generator discovered every value itself.  Only now, and only for cells a
verifier has actually replayed, is the discovered value compared with the
historical Route-A number.

Three outcomes:

  AGREES                 the discovered value equals the historical one.
  PLAN_VALUE_REFUTED     the discovered value is LARGER than the value round
                         167 planned with.  The plan for that cell is dead:
                         the row optimisation has to be redone with the true
                         value.  This is never runtime noise.
  HISTORICAL_DISAGREES   the discovered value differs from the round-152
                         table for a cell the table does carry.  The batch
                         stops and both artefacts are preserved.

For the eight cells whose value round 167 could only PREDICT through
(BRIDGE-EQ), the planned value comes from the piece table; those are flagged
separately because a prediction is not a certificate.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verification", action="append", required=True)
    ap.add_argument("--generation", action="append", required=True)
    ap.add_argument("--report", default="r168/certs/agreement_168.json")
    a = ap.parse_args()

    chain = {parse(r["cell"]): r["cap"] for r in json.loads(
        (ROOT / "r152" / "certs" / "verify_all_c152.json").read_text())["rows"]
        if r["status"] in GOOD}
    piece = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in json.loads(
        (ROOT / "r152" / "certs" / "verify_piece_c152.json").read_text())["rows"]
        if r["status"] in GOOD}
    plan = json.loads((ROOT / "r167" / "certs"
                       / "round168_plan_167.json").read_text())
    margins = plan["margins"]["detail"]

    replayed = set()
    for rel in a.verification:
        rep = json.loads((ROOT / rel).read_text())
        if not rep["all_ok"]:
            raise SystemExit(f"{rel} is not all_ok")
        replayed |= {parse(c) for c in rep["certified_cells"]}

    rows, refuted, disagree = [], [], []
    for rel in a.generation:
        rep = json.loads((ROOT / rel).read_text())
        for r in rep["rows"]:
            if r["status"] != "TREE_BUILT":
                continue
            K = parse(r["cell"])
            if K not in replayed:
                rows.append(dict(cell=r["cell"], verdict="NOT_REPLAYED"))
                continue
            found = r["cap"]
            hist = chain.get(K)
            pred = margins.get(r["cell"], {}).get("planned_value")
            src = ("round-152 chain table" if hist is not None else
                   "round-167 (BRIDGE-EQ) prediction from the piece table")
            planned = hist if hist is not None else pred
            row = dict(cell=r["cell"], discovered=found, planned=planned,
                       planned_source=src,
                       value_is_only_predicted=hist is None,
                       safe_upper_limit=margins.get(r["cell"], {})
                       .get("largest_still_safe"))
            if planned is None:
                row["verdict"] = "NO_REFERENCE_VALUE"
            elif found == planned:
                row["verdict"] = "AGREES"
            elif found > planned:
                row["verdict"] = "PLAN_VALUE_REFUTED"
                refuted.append(row)
            else:
                row["verdict"] = "HISTORICAL_DISAGREES_STRONGER"
                disagree.append(row)
            if (row.get("safe_upper_limit") is not None
                    and found > row["safe_upper_limit"]):
                row["breaks_row_closure"] = True
                refuted.append(row)
            rows.append(row)

    out = dict(
        inputs={p: sha(p) for p in
                ["r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json",
                 "r167/certs/round168_plan_167.json"]
                + list(a.verification) + list(a.generation)},
        compared=len([r for r in rows if r.get("verdict") not in
                      (None, "NOT_REPLAYED")]),
        agrees=sum(1 for r in rows if r.get("verdict") == "AGREES"),
        plan_value_refuted=[r["cell"] for r in refuted],
        historical_disagreements=[r["cell"] for r in disagree],
        predicted_cells_compared=[r for r in rows
                                  if r.get("value_is_only_predicted")],
        rows=rows)
    out["ok"] = not refuted and not disagree
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rows", "inputs")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
