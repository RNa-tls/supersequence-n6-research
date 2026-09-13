#!/usr/bin/env python3
"""Round 147 Phase 16 -- the searcher's table loader must FAIL CLOSED.

Round 144's loader accepted a wrong-arity file, silently kept the minimum of
conflicting duplicate keys, and monotonised the table itself.  Each of those is
how a bad table got in.  This script feeds the round-147 searcher a series of
deliberately broken tables and requires a NON-ZERO exit every time, plus a
clean run on the good table, so "accepted" can never be the default.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147 = ROOT / "r147"
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

EXE = R147 / "l6chain147.exe"
TMP = R147 / "logs" / "failclosed"
CELL = (0, 2, 1, 0, 0, 0)          # cheap, and its table is small


def run(ubpath, cell=CELL, target=0):
    b, d, a, bb, e, h = cell
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        str(h), "20000000", str(ubpath), str(target)],
                       capture_output=True, text=True, cwd=ROOT)
    return r.returncode, (r.stderr or "").strip().splitlines()[:1]


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    store = {}
    for k, v in json.loads((R147 / "tables" / "chain_cells_147.json").read_text()).items():
        if v.get("status") == "EXACT_UNCAPPED":
            store[tuple(int(x) for x in k.split("|"))] = dict(cc=v["cc"])
    good = TMP / "good.txt"
    ub147.write_table(good, CELL, store, exclude={CELL})
    lines = good.read_text().splitlines()
    head, rows = lines[0], lines[1:]

    cases = []

    def case(name, text, expect_fail=True, path=None):
        p = path or (TMP / (name + ".txt"))
        if text is not None:
            p.write_text(text)
        rc, err = run(p)
        ok = (rc != 0) if expect_fail else (rc == 0)
        cases.append(dict(case=name, returncode=rc, stderr=err,
                          expected="reject" if expect_fail else "accept",
                          ok=ok))

    case("good_table", None, expect_fail=False, path=good)
    case("wrong_magic", "UB6 %d\n" % len(rows) + "\n".join(rows) + "\n")
    case("no_magic", "\n".join(rows) + "\n")
    case("arity_5_round144_chain_file", "UB7 3\n0 0 0 20\n1 0 0 35\n2 0 0 50\n")
    case("arity_3_round144_piece_file", "UB7 2\n0 0 20\n0 1 20\n")
    case("truncated", "UB7 %d\n" % len(rows) + "\n".join(rows[:-3]) + "\n")
    case("padded", "UB7 %d\n" % (len(rows) - 3) + "\n".join(rows) + "\n")
    dup = rows[:]
    t0 = dup[0].split()
    dup.append(" ".join(t0[:6] + [str(int(t0[6]) - 1)]))
    case("duplicate_conflicting_key", "UB7 %d\n" % len(dup) + "\n".join(dup) + "\n")
    case("index_out_of_range", "UB7 1\n0 41 0 0 0 0 20\n")
    case("value_out_of_range", "UB7 1\n0 0 0 0 0 0 999\n")
    case("negative_value", "UB7 1\n0 0 0 0 0 0 -1\n")
    case("malformed_row", "UB7 2\n0 0 0 0 0 0 20\n0 0 0 0 x 0 20\n")
    # non-monotone: drop the value at a higher d below its lower neighbour
    nm = []
    for ln in rows:
        f = ln.split()
        if f[1] == "2":
            f[6] = "1"
        nm.append(" ".join(f))
    case("non_monotone_in_d", "UB7 %d\n" % len(nm) + "\n".join(nm) + "\n")
    # the literal round-144 artefacts
    case("round144_chain_ub_verbatim", None,
         path=ROOT / "outputs" / "rr_l6_chain_ub_144.txt")
    case("round144_piece_ub_verbatim", None,
         path=ROOT / "outputs" / "rr_l6_capacity_ub_144.txt")
    case("missing_file", None, path=TMP / "does_not_exist.txt")
    _ = head

    out = dict(cases=cases, total=len(cases),
               rejected_as_required=sum(1 for c in cases if c["ok"]),
               failures=[c for c in cases if not c["ok"]],
               ok=all(c["ok"] for c in cases))
    (R147 / "certs" / "failclosed_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    for c in cases:
        print(f"{'OK ' if c['ok'] else 'BAD'} {c['case']:34s} rc={c['returncode']:3d} "
              f"{c['stderr']}")
    print(json.dumps({k: v for k, v in out.items() if k != "cases"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
