#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- OLD vs R1 side-by-side table from recorded runs."""
from __future__ import annotations
import glob, json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "r172/certs/side_by_side_R1.json"


def mean_depth(h):
    n = sum(h.values())
    return round(sum(int(k) * v for k, v in h.items()) / n, 2) if n else None


def main():
    runs = defaultdict(dict)
    for p in sorted(glob.glob(str(ROOT / "r172/certs/exp/*.json"))):
        r = json.loads(Path(p).read_text())
        runs[(r["cell"], r["bound"], r["node_cap"], r["environment_job"])][r["mode"]] = r
    rows = []
    for (cell, J, cap, env), m in sorted(runs.items()):
        row = dict(cell=cell, J=J, node_cap=cap, environment_job=env)
        for mode in ("old", "r1"):
            r = m.get(mode)
            if not r:
                continue
            c = r["counters"]
            row[mode] = dict(
                status=r["status"], visited_nodes=r["visited_nodes"],
                proof_tokens=r["proof_tokens"],
                internal_nodes=c.get("internal", 0),
                p_calls=c.get("p_calls", 0), old_p_prunes=c.get("leaf_p_old", 0),
                r1_only_prunes=c.get("leaf_r1_only", 0),
                r1_dead_leaves=c.get("leaf_r1_dead", 0),
                b_leaves=c.get("leaf_b", 0), f_leaves=c.get("leaf_f", 0),
                p_fallback_fraction=round(c.get("p_fallback", 0) / c["p_calls"], 4)
                if c.get("p_calls") else None,
                r1_branch_lookups=c.get("r1_branch_lookups", 0),
                r1_branch_fallback=c.get("r1_branch_fallback", 0),
                branch_count_hist_evals=r["branch_count_histogram_r1_evals"],
                branch_count_hist_prunes=r["branch_count_histogram_r1_prunes"],
                mean_depth_nodes=mean_depth(r["depth_histogram_nodes"]),
                mean_depth_by_leaf={k: mean_depth(v) for k, v in
                                    r["depth_histogram_leaves"].items()},
                max_depth=max(map(int, r["depth_histogram_nodes"])),
                audit_old_p_leaves=c.get("audit_old_p_leaves", 0),
                audit_conservativity_failures=c.get("audit_conservativity_failures", 0),
                seconds_noncanonical=r["seconds_noncanonical"],
                generator_sha256=r["generator_sha256"]["gen172"])
        if "old" in row and "r1" in row and \
                row["old"]["status"] == row["r1"]["status"] == "COMPLETED":
            row["node_ratio_r1_over_old"] = round(
                row["r1"]["visited_nodes"] / row["old"]["visited_nodes"], 4)
        rows.append(row)
    OUT.write_text(json.dumps(dict(title="OLD vs R1 bounded side-by-side (EXPERIMENTAL)",
                                   rows=rows), indent=1) + "\n")
    print(f"{'cell':>14} {'J':>4} {'cap':>9} {'mode':>4} {'status':>9} {'nodes':>10} "
          f"{'p_calls':>9} {'old_p':>9} {'r1_only':>9} {'dead':>5} {'pFB':>6} {'audit':>5} {'sec':>6}")
    for r in rows:
        for mode in ("old", "r1"):
            x = r.get(mode)
            if x:
                print(f"{r['cell']:>14} {r['J']:>4} {r['node_cap']:>9} {mode:>4} {x['status']:>9} "
                      f"{x['visited_nodes']:>10} {x['p_calls']:>9} {x['old_p_prunes']:>9} "
                      f"{x['r1_only_prunes']:>9} {x['r1_dead_leaves']:>5} "
                      f"{x['p_fallback_fraction']!s:>6} {x['audit_conservativity_failures']:>5} "
                      f"{x['seconds_noncanonical']:>6}")
        if "node_ratio_r1_over_old" in r:
            print(f"{'':>14} completed-tree node ratio r1/old = {r['node_ratio_r1_over_old']}")


if __name__ == "__main__":
    main()
