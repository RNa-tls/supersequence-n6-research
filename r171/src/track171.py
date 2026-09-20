#!/usr/bin/env python3
"""Round 171 -- the progress ledger: how many load-bearing VALUES are genuine.

The primary number for this round is certified load-bearing bounds out of 35.
Helper certificates are counted separately and are not theorem progress: a
ladder rung closes no census row, so generating more of them moves nothing on
this ledger.

For every basis cell that now has a certificate, the census is re-run with its
ROUND-152 TABLE ENTRY DISABLED and the certified bound used in its place.  That
is the only way the historical dependency count can be believed: a cell is only
off the table when the census still closes without reading it.

Cells that have no certificate yet still read the table, and they are reported
as exactly that.  The desired sequence is 33 -> 0 and this module states where
it actually stands.
"""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402

BATCHES = [
    "r164/certs/extree_prefix_164.txt.gz",
    "r166/certs/extree_batch2_166.txt.gz",
    "r166/certs/extree_batch3_166.txt.gz",
    "r168/certs/extree_batch1_168.txt.gz",
    "r170/certs/extree_ladder_h_170.txt.gz",
    "r170/certs/extree_ladder_a2_170.txt.gz",
    "r170/certs/extree_target_h_170.txt.gz",
    "r170/certs/extree_target_a2_170.txt.gz",
    "r171/certs/extree_probe_b1a10_171.txt.gz",
    "r171/certs/extree_lb_batch1_171.txt.gz",
    "r171/certs/extree_lb_b1a10_d5_171.txt.gz",
    "r171/certs/extree_lb_b1a10_d7_171.txt.gz",
]


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def genuine():
    out = {}
    for rel in BATCHES:
        p = ROOT / rel
        if not p.exists():
            continue
        for line in gzip.decompress(p.read_bytes()).decode().splitlines():
            s = line.split("#")[0].split()
            if s and s[0] == "tree":
                out[tuple(int(x) for x in s[1:7])] = (int(s[7]), rel)
    return out


def main():
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = sorted(set([parse(c) for c in src["minimum"]["cells"]]
                       + [parse(c) for c in
                          bas["minimum"]["witness_completion"]]))
    doss = json.loads((ROOT / "r171" / "certs"
                       / "remaining_171.json").read_text())
    Smap = {d["cell"]: d["safe_upper_bound_S"] for d in doss["dossier"]}
    gen = genuine()

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

    certified = [K for K in BASIS if K in gen]
    still_table = [K for K in BASIS if K not in gen]

    # the census with every certified cell held at its CERTIFIED bound and the
    # table entry unused; uncertified cells keep the table value
    vals = {K: gen[K][0] for K in certified}
    t0 = time.time()
    S.apply(set(BASIS), values=vals)
    v = S.verdicts()
    open_rows = [k for k in EX if v[k] != "STRICTLY_CLOSED"]
    eq_after = {str(k[1]): v[k] for k in eq_rows}
    eq_held = all(x == "EQUALITY" for x in eq_after.values())
    print(f"certified {len(certified)}/35, table-dependent {len(still_table)}",
          flush=True)
    print(f"census with certified bounds substituted: "
          f"{len(EX) - len(open_rows)}/{len(EX)} closed, equality held "
          f"{eq_held}", flush=True)

    rows = []
    for K in certified:
        cap, rel = gen[K]
        rows.append(dict(cell=cellstr(K), certified_bound=cap,
                         census_safe_bound_S=Smap.get(cellstr(K)),
                         certificate=rel,
                         bound_is_at_or_below_S=(
                             Smap.get(cellstr(K)) is None
                             or cap <= Smap[cellstr(K)]),
                         historical_table_entry="DISABLED"))
    out = dict(
        primary_metric=dict(
            genuine_load_bearing_bounds=len(certified),
            basis_size=len(BASIS),
            reads_as=f"{len(certified)}/35",
            historical_load_bearing_dependencies_remaining=len(still_table)),
        helper_certificates_this_round=dict(
            count=3,
            cells=["1|2|10|0|0|0", "1|3|10|0|0|0", "1|4|10|0|0|0"],
            not_theorem_progress="a ladder rung closes no census row; helper "
                                 "count is reported separately and never as "
                                 "progress on the 35"),
        census_with_certified_bounds=dict(
            exposed_rows=len(EX),
            closed=len(EX) - len(open_rows),
            all_closed=not open_rows,
            still_open=[list(k[1]) for k in open_rows],
            baseline_tally=dict(tally_full),
            equality_rows=eq_after,
            equality_preserved=eq_held,
            method="each certified cell is held at the bound its certificate "
                   "proves and its round-152 table entry is not read; "
                   "uncertified cells still read the table"),
        certified_cells=rows,
        still_table_dependent=[cellstr(K) for K in still_table],
        sequence_target="33 -> 0",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = (not open_rows) and eq_held
    (ROOT / "r171" / "certs" / "progress_171.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out["primary_metric"], ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
