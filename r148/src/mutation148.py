#!/usr/bin/env python3
"""Round 148 Phase 5 -- MUTATION TESTING of the fail-closed master verifier.

Each mutation corrupts one load-bearing artifact and the verifier must FAIL.
Files are backed up BY CONTENT and restored afterwards (round 146 learned the
hard way that `git checkout` silently does nothing for untracked files, which
left injected faults in place and produced a spurious finding).

A mutation that the verifier does NOT catch is reported as an ESCAPE, not
quietly dropped.
"""
from __future__ import annotations
import copy, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
VER = R148 / "src" / "verifier148.py"

CHAIN = R147 / "tables" / "chain_cells_147.json"
HEAVY = R147 / "tables" / "heavy_cells_147.json"
LB = R147 / "tables" / "loadbearing_cells_147.json"
MONO = R147 / "certs" / "monotonicity_147.json"
IMPLB = R147 / "certs" / "second_impl_147.json"
FAILC = R147 / "certs" / "failclosed_147.json"
BINS = R147 / "certs" / "binaries_147.json"
CENSUS = R148 / "rows" / "census_148.json"
WITC = R148 / "certs" / "witnesses_148.json"
W96T = R148 / "witnesses" / "row96_table.jsonl"
W872 = ROOT / "data" / "verified_872_witness.txt"


def run_verifier():
    r = subprocess.run([sys.executable, str(VER)], capture_output=True,
                       text=True, cwd=ROOT)
    failed = [ln.split()[1] for ln in r.stdout.splitlines()
              if ln.startswith("FAIL")]
    return r.returncode, failed


def mutate_json(path, fn):
    d = json.loads(Path(path).read_text())
    fn(d)
    Path(path).write_text(json.dumps(d, indent=1))


def main():
    files = [CHAIN, HEAVY, LB, MONO, IMPLB, FAILC, BINS, CENSUS, WITC, W96T, W872]
    backup = {p: p.read_bytes() for p in files if p.exists()}

    def restore():
        for p, b in backup.items():
            p.write_bytes(b)

    rc0, f0 = run_verifier()
    baseline = dict(mutation="none (baseline)", returncode=rc0, failed=f0,
                    detected=(rc0 == 0), note="the clean tree must PASS")
    results = [baseline]

    muts = []

    def M(name, path, fn, why):
        muts.append((name, path, fn, why))

    M("1_capacity_decreased_by_1", CHAIN,
      lambda d: d.__setitem__("0|14|0|0|0|0",
                              {**d["0|14|0|0|0|0"], "cc": d["0|14|0|0|0|0"]["cc"] - 1}),
      "an equality cell's capacity no longer equals the required port count")
    M("2_capacity_increased_by_1", CHAIN,
      lambda d: d.__setitem__("0|0|0|0|0|0",
                              {**d["0|0|0|0|0|0"], "cc": d["0|0|0|0|0|0"]["cc"] + 1}),
      "breaks monotonicity against its neighbours")
    M("3_cell_removed", CHAIN,
      lambda d: d.pop("0|14|0|0|0|0"), "a load-bearing cell goes missing")
    M("4_cell_marked_capped", CHAIN,
      lambda d: d.__setitem__("0|8|2|0|0|0",
                              {**d["0|8|2|0|0|0"], "capped": True,
                               "status": "UNKNOWN_CAP"}),
      "a capped cell may never be used as a bound")
    M("5_heavy_cell_removed", HEAVY,
      lambda d: d.pop("0|8|0|0|0|1"), "the 92-port equality cell goes missing")
    M("6_budget_columns_swapped", CHAIN,
      lambda d: d.__setitem__("0|8|0|2|0|0", d.pop("0|8|2|0|0|0")),
      "the a and bb budgets are transposed in a key")
    M("7_monotonicity_certificate_falsified", MONO,
      lambda d: d.update(ok=False, adjacent_violations=3),
      "a monotonicity violation is reported")
    M("8_implementation_B_incomplete", IMPLB,
      lambda d: d.update(ok=False, timeouts=["0|14|0|0|0|0"],
                         agreeing=d["agreeing"] - 1),
      "one load-bearing cell is only assumed, not cross-checked")
    M("9_failclosed_certificate_falsified", FAILC,
      lambda d: d.update(ok=False, failures=[{"case": "round144_chain_ub_verbatim"}]),
      "the loader would accept a round-144 UB file")
    M("10_source_hash_changed", BINS,
      lambda d: d["phase2_build"].__setitem__("exe_sha256", "0" * 64),
      "the recorded executable hash no longer matches")
    M("11_L870_row_left_open", CENSUS,
      lambda d: d["layers"]["L870"]["tally"].update(STRICTLY_CLOSED=352,
                                                    SURVIVING=1),
      "one L=870 row survives")
    M("12_L871_third_equality_row", CENSUS,
      lambda d: d["layers"]["L871"]["tally"].update(STRICTLY_CLOSED=1153,
                                                    EQUALITY=3),
      "a third equality row appears")
    M("13_equality_witness_deleted", W96T,
      None, "one of the two 96-port witnesses is removed")
    M("14_witness_permutation_rank_altered", W96T,
      None, "one port index inside a witness is changed")
    M("15_coexistence_result_missing", WITC,
      lambda d: [r.pop("certificates", None) for r in d["rows"]],
      "the coexistence verdicts are gone")
    M("16_notable_route_marked_capped", WITC,
      lambda d: d["rows"][0]["route_notable"].update(capped=True,
                                                     status="UNKNOWN_CAP"),
      "the table-free enumeration did not finish")
    M("17_872_witness_truncated", W872,
      None, "the upper-bound witness is no longer a cover")
    M("18_loadbearing_cell_not_in_ledger", LB,
      lambda d: d["cells"].append([5, 20, 0, 0, 0, 0]),
      "a load-bearing cell has no computed capacity")

    for name, path, fn, why in muts:
        try:
            if name == "13_equality_witness_deleted":
                lines = path.read_text().splitlines()
                path.write_text(lines[0] + "\n")
            elif name == "14_witness_permutation_rank_altered":
                lines = path.read_text().splitlines()
                o = json.loads(lines[0])
                o["ports"][5] = (o["ports"][5] + 1) % 720
                path.write_text(json.dumps(o) + "\n" + "\n".join(lines[1:]) + "\n")
            elif name == "17_872_witness_truncated":
                path.write_text(path.read_text().split()[0][:-1] + "\n")
            else:
                mutate_json(path, fn)
            rc, failed = run_verifier()
            results.append(dict(mutation=name, target=str(path.relative_to(ROOT)),
                                why=why, returncode=rc, detected=(rc != 0),
                                failed_checks=failed))
        finally:
            restore()
        print(f"{'DETECTED' if results[-1]['detected'] else 'ESCAPED  '} "
              f"{name}: {results[-1]['failed_checks']}", flush=True)

    rc1, f1 = run_verifier()
    results.append(dict(mutation="none (restored)", returncode=rc1, failed=f1,
                        detected=(rc1 == 0), note="the tree must PASS again"))
    escapes = [r["mutation"] for r in results[1:-1] if not r["detected"]]
    out = dict(mutations=len(muts), detected=len(muts) - len(escapes),
               escaped=escapes, baseline_passes=baseline["detected"],
               restored_passes=results[-1]["detected"],
               ok=(not escapes and baseline["detected"]
                   and results[-1]["detected"]),
               detail=results)
    (R148 / "certs" / "mutation_148.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
