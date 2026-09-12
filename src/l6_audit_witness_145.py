#!/usr/bin/env python3
"""Audit ANY n=6 covering word against the whole round-145 framework.

Usage:  python3 src/l6_audit_witness_145.py FILE [FILE ...]
        (one word per line, alphabet 123456 or 012345)

Exists because the round-145 checks on n = 6 were run on ONE structural family
of length-872 covers (the stored witness and its 48 symmetry images).  The
public archive holds 44,120 length-872 covers in four families (treelike,
nonstandard, slack1, slack2) that differ in fragment and orbit counts, and those
other families are UNTESTED here.  Drop them in and this script will report,
per word: whether it is a cover, whether Phi already fixes it, the full splicing
audit, (FO), MASTER-142 against the actual length, and the chain extraction.
Any word whose MASTER-142 value disagrees with its length would REFUTE the
round-145 lower-bound chain, so this is the cheapest available falsification
test.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_splicing_145 as SP                                        # noqa: E402
import l6_extraction_145 as EX                                      # noqa: E402
from l6_fixed_representative_145 import (is_cover, fixed_representative,  # noqa
                                         audit_fixed_point)


def audit(word):
    w = word.strip()
    alpha = "".join(sorted(set(w)))
    if len(alpha) != 6:
        return dict(ok=False, why=f"alphabet size {len(alpha)}")
    if not is_cover(w, 6, alpha):
        return dict(ok=False, why="not a cover")
    wf, lens = fixed_representative(w, 6)
    fp = audit_fixed_point(wf, 6)
    sp = SP.analyse(wf, 6)
    ex = EX.extract(wf, 6)
    exh = EX.extract(wf, 6, keep_heavy=True)
    return dict(length=len(w), fixed_length=len(wf), already_fixed=(wf == w),
                phi_iterations=len(lens) - 1, fixed_point_audit=fp["ok"],
                splicing_ok=sp["ok"], FO_holds=sp["FO_holds"],
                MASTER=sp["MASTER"], MASTER_holds=sp["MASTER_holds"],
                invariants={k: sp[k] for k in
                            ("P", "G", "O", "k", "S", "H", "D2", "Qs", "K",
                             "R_int", "c", "d", "g", "Z", "Bstar")},
                types=sp["types"],
                extraction_ok=ex["ok"] and exh["ok"],
                chains=ex["chains"], sum_P=ex["sum_P"], sum_D=ex["sum_D"],
                sum_tok=ex["sum_tok"], sigma=ex["sigma"],
                ok=(fp["ok"] and sp["ok"] and sp["FO_holds"]
                    and sp["MASTER_holds"] and ex["ok"] and exh["ok"]))


if __name__ == "__main__":
    rows, profiles = [], {}
    for path in sys.argv[1:]:
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            r = audit(line)
            rows.append(r)
            if r.get("ok") is not None and "invariants" in r:
                key = json.dumps(r["invariants"], sort_keys=True)
                profiles[key] = profiles.get(key, 0) + 1
            print(json.dumps({k: r[k] for k in
                              ("length", "already_fixed", "MASTER",
                               "MASTER_holds", "ok") if k in r},
                             ensure_ascii=False))
    bad = [r for r in rows if not r.get("ok")]
    print(f"\nwords={len(rows)}  failures={len(bad)}  "
          f"distinct invariant profiles={len(profiles)}")
    for k, v in profiles.items():
        print(f"  x{v}  {k}")
    if bad:
        print("\nFAILURES (these would refute the round-145 chain):")
        for r in bad[:5]:
            print(" ", json.dumps(r, ensure_ascii=False)[:400])
    sys.exit(1 if bad else 0)
