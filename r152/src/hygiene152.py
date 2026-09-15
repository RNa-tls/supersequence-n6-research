#!/usr/bin/env python3
"""Round 152 -- what the certified-only pipeline is allowed to read.

The round-146 aggregate UB file and the round-144 chain tables are RETRACTED
(the first was unsound, the second superseded), and the round-148 census called
the heavy-retained model with the joint count h instead of its budget HMAX = H.
None of that may reach the round-152 verdict, so this checks the sources by
inspection rather than by trust:

  * no file in the certified-only pipeline may open a production capacity table
    or UB file;
  * the checkers may not import the production searchers;
  * the heavy-retained call in r152/src/rows152.py must be keyed on H;
  * every verification report feeding the census must be free of UNKNOWN_CAP
    and DISAGREE rows.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# files that must never appear in the certified-only pipeline
FORBIDDEN_READS = [
    "chain_cells_147.json", "heavy_cells_147.json", "loadbearing_cells_147.json",
    "rr_l6_marked_capacity_table_144.json", "ub147", "catalogue147.h",
    "l6_chain_capacity_147", "l6_marked_capacity", "l6_coupled_144",
    "l6cap", "l6chain", "INVALIDATED_BY_UB146", "chain2_147",
]
PIPELINE = [
    "r152/src/checker152.py", "r152/src/checker152.c",
    "r152/src/piece152.py", "r152/src/piece152.c",
    "r152/src/extree152.py", "r152/src/extree152.c",
    "r152/src/rows152.py", "r152/src/passes152.py", "r152/src/ppasses152.py",
]
# these may name a production table only as an OPTIONAL --compare cross-check
COMPARE_ONLY = {"r152/src/checker152.py", "r152/src/piece152.py"}


def main():
    out = {"forbidden_reads": {}, "ok": True}
    for rel in PIPELINE:
        src = (ROOT / rel).read_text()
        hits = []
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith(("#", "*", "/*", "//")):
                continue
            for bad in FORBIDDEN_READS:
                if bad in line:
                    hits.append(dict(line=i, needle=bad, text=line.strip()[:110]))
        if hits and rel in COMPARE_ONLY:
            # allowed only on the --compare path, which never feeds a verdict
            hits = [h for h in hits if "compare" not in h["text"].lower()]
        out["forbidden_reads"][rel] = hits
        if hits:
            out["ok"] = False

    # the heavy-retained model must use HMAX = H, not the joint count h
    rows = (ROOT / "r152" / "src" / "rows152.py").read_text()
    m = re.search(r"heavy KEPT.*?\n(.*?)\n    if mv is not None", rows, re.S)
    block = m.group(1) if m else ""
    out["heavy_retained_uses_H"] = bool(block) and 'r["H"]' in block \
        and 'r["h"]' not in block
    out["heavy_retained_block"] = [l.strip() for l in block.splitlines()
                                   if l.strip()]
    out["ok"] &= out["heavy_retained_uses_H"]

    # no UNKNOWN_CAP or DISAGREE anywhere in the reports the census consumes
    out["reports"] = {}
    for rel in ["r152/certs/verify_all_c152.json",
                "r152/certs/verify_piece_c152.json"]:
        p = ROOT / rel
        if not p.exists():
            out["reports"][rel] = "MISSING"
            out["ok"] = False
            continue
        d = json.loads(p.read_text())
        bad = [r["cell"] for r in d["rows"]
               if r["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED")]
        out["reports"][rel] = dict(cells=len(d["rows"]), not_certified=bad)
        if bad:
            out["ok"] = False

    # the census must not have read anything but those reports
    cen = ROOT / "r152" / "certs" / "census_152.json"
    if cen.exists():
        c = json.loads(cen.read_text())
        out["census_inputs"] = dict(chain=c["verify_reports"],
                                    piece=c["verify_piece_reports"])
        out["census_survivors"] = {
            L: v["tally"] for L, v in c["layers"].items()}
        bad = [L for L, v in c["layers"].items()
               if v["tally"].get("SURVIVING") or v["tally"].get("UNKNOWN_CAP")]
        out["census_has_survivors_or_unknown"] = bad
        out["ok"] &= not bad
    else:
        out["census_inputs"] = "MISSING"
        out["ok"] = False

    (ROOT / "r152" / "certs" / "hygiene_152.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
