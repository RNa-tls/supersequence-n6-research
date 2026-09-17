#!/usr/bin/env python3
"""Round 165 phase 12b -- verify a SAT UNSAT proof with an INDEPENDENT checker.

Cadical saying UNSAT is one more implementation's opinion.  A DRAT proof
checked by drat-trim is a machine-checkable certificate: the checker never
searches, it replays the resolution steps.  That is the same Route-B shape as
an exhaustion tree, in a different format.

drat-trim is not in the repository; it is fetched and built at run time from
its upstream source, and its sha256 is recorded so the run is reproducible.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")
sys.path.insert(0, str(ROOT / "r165" / "src"))
sys.path.insert(0, str(ROOT / "r164" / "src"))
import sat165 as S                                                # noqa: E402
import routeb164 as R                                             # noqa: E402
from pysat.solvers import Cadical153, Lingeling                    # noqa: E402

# pysat's CaDiCaL binding returns an EMPTY proof whenever the solver settles
# the instance in preprocessing -- it does so even for a four-clause
# contradiction -- and an empty proof cannot derive the empty clause, so
# drat-trim rightly rejects it.  Lingeling's binding emits the lemmas.  This
# was found by running both on a toy UNSAT formula, not guessed.
SOLVER = Lingeling

DRAT = SCRATCH / "drat-trim"


def dimacs(cls, nvars, path):
    with open(path, "w") as fh:
        fh.write(f"p cnf {nvars} {len(cls)}\n")
        for c in cls:
            fh.write(" ".join(map(str, c)) + " 0\n")


def check_cell(cell, cap, budget_s=1800):
    """Every orbit sub-instance must be UNSAT and its proof must check."""
    b, d, fp, lp = cell
    T = cap + 1
    subs = []
    ok = True
    for m in range(1, (d + T) // 5 + 1):
        cls, pool, st = S.build(cell, T, m)
        cnf = SCRATCH / f"c_{b}_{d}_{fp}_{lp}_{m}.cnf"
        prf = SCRATCH / f"c_{b}_{d}_{fp}_{lp}_{m}.drat"
        dimacs(cls, pool.top, cnf)
        t0 = time.time()
        with SOLVER(bootstrap_with=cls, with_proof=True) as s:
            res = s.solve()
            proof = s.get_proof() if not res else None
        tsolve = time.time() - t0
        if res:
            subs.append(dict(orbits=m, result="SAT"))
            ok = False
            cnf.unlink(missing_ok=True)
            continue
        with open(prf, "w") as fh:
            fh.write("\n".join(proof) + "\n")
        t0 = time.time()
        r = subprocess.run([str(DRAT), str(cnf), str(prf), "-f"],
                           capture_output=True, text=True, timeout=budget_s)
        tcheck = time.time() - t0
        verified = "s VERIFIED" in r.stdout
        subs.append(dict(orbits=m, result="UNSAT",
                         clauses=st["clauses"], variables=st["variables"],
                         cnf_bytes=cnf.stat().st_size,
                         proof_lines=len(proof),
                         proof_bytes=prf.stat().st_size,
                         solve_seconds=round(tsolve, 1),
                         check_seconds=round(tcheck, 1),
                         drat_trim_verified=verified))
        ok = ok and verified
        cnf.unlink(missing_ok=True)
        prf.unlink(missing_ok=True)
    return dict(cell="|".join(map(str, cell)), cap=cap, ports_tested=T,
                sub_instances=len(subs), all_unsat_and_verified=ok,
                subs=subs)


def main():
    if not DRAT.exists():
        print("drat-trim not built", file=sys.stderr)
        return 1
    drat_sha = hashlib.sha256(DRAT.read_bytes()).hexdigest()
    src = SCRATCH / "drat-trim.c"
    import os
    only = os.environ.get("R165_CELLS", "0,0,0,0;20")
    rows = []
    for spec in only.split("|"):
        args, cap = spec.split(";")
        rows.append(check_cell(tuple(int(x) for x in args.split(",")),
                               int(cap)))
    for r in rows:
        print(json.dumps({k: v for k, v in r.items() if k != "subs"}),
              flush=True)
    out = dict(
        solver=SOLVER.__name__,
        solver_note="pysat's CaDiCaL proof binding returns an empty proof on "
                    "instances it settles in preprocessing (verified on a "
                    "four-clause contradiction), so Lingeling is used for "
                    "proof logging",
        checker="drat-trim (upstream marijnheule/drat-trim, built here)",
        checker_source_sha256=hashlib.sha256(src.read_bytes()).hexdigest()
        if src.exists() else None,
        checker_binary_sha256=drat_sha,
        note="the binary is built at run time and lives outside the "
             "repository; only its hashes are pinned",
        cells=rows,
        all_verified=all(r["all_unsat_and_verified"] for r in rows),
        totals=dict(
            proof_bytes=sum(s.get("proof_bytes", 0) for r in rows
                            for s in r["subs"]),
            solve_seconds=round(sum(s.get("solve_seconds", 0) for r in rows
                                    for s in r["subs"]), 1),
            check_seconds=round(sum(s.get("check_seconds", 0) for r in rows
                                    for s in r["subs"]), 1)))
    out["ok"] = out["all_verified"]
    (ROOT / "r165" / "certs" / "drat_check_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "cells"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
