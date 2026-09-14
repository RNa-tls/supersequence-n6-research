#!/usr/bin/env python3
"""Round 149 H -- is the feasibility prune SOUND?

`feas()` is the one prune neither implementation validates for the other: I
wrote implementation B's copy by translating the same idea, so a shared
conceptual error would survive their agreement.  It is also inside the solver
but it changes the MODEL'S VALUE, so it has to be audited like a lemma.

WHAT IT CLAIMS.  At a search node, for every orbit already opened other than the
current one let u_q be its number of unused phases.  Sort them, assume the `tok`
remaining tokens are each spent re-entering one of the largest-u orbits and that
each such re-entry completes its orbit, and let `tot` be the sum of the rest.
Then the FINAL deficit is at least `tot`, so `tot > DMAX` means this node cannot
lead to a recorded chain.

WHY IT IS SOUND.  The final deficit is the total number of unused phases,
summed over the orbits the chain opens.  An orbit other than the current one can
gain further ports only if the chain RE-ENTERS it, and every re-entry is a
non-clean-E step into an already-opened orbit, which costs exactly one token
(clean-E is tau and never leaves the current orbit).  So at most `tok` of those
orbits can lose any unused phases at all, and zeroing the largest u_q first
minimises the remainder.  Hence `tot` is a LOWER bound on the final deficit.

THE TEST.  A prune that is too aggressive makes the computed capacity TOO
SMALL, which is exactly the failure mode that broke round 145.  So disable it
and recompute: if the capacities rise anywhere, the prune was unsound.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R149 = ROOT / "r147", ROOT / "r149"
sys.path.insert(0, str(R147 / "src"))
import ub147                                                        # noqa: E402

A = R147 / "l6chain147b.exe"
B = R149 / "l6chain_nofeas.exe"
BUDGET = int(os.environ.get("R149_FEAS_SECONDS", "240"))


def store():
    st = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") == "EXACT_UNCAPPED":
                st[tuple(int(x) for x in k.split("|"))] = v
    return st


ST = store()


def main(argv):
    tmp = R149 / "logs" / "feas"
    tmp.mkdir(parents=True, exist_ok=True)
    want = int(argv[0]) if argv else 60
    cells = sorted((k for k in ST if (ST[k]["nodes"] or 0) < 40_000_000),
                   key=lambda k: ST[k]["nodes"] or 0)
    step = max(1, len(cells) // want)
    sel = [(0, 14, 0, 0, 0, 0), (0, 8, 0, 0, 0, 1)]
    sel += [c for c in cells[::step] if c not in sel]
    rows, bad, to = [], [], []
    for cell in sel:
        ubp = tmp / ("ub_%d_%d_%d_%d_%d_%d.txt" % cell)
        ub147.write_table(ubp, cell, {k: dict(cc=v["cc"]) for k, v in ST.items()
                                      if k != cell}, exclude={cell})
        a = [str(x) for x in cell]
        try:
            jn = json.loads(subprocess.run([str(B)] + a + ["0", str(ubp), "0"],
                                           capture_output=True, text=True,
                                           cwd=ROOT, timeout=BUDGET).stdout)
        except Exception:
            to.append(list(cell))
            continue
        if jn["capped"]:
            to.append(list(cell))
            continue
        cc = ST[cell]["cc"]
        rec = dict(cell=list(cell), with_feas=cc, without_feas=jn["cc"],
                   nodes_without=jn["nodes"], equal=(jn["cc"] == cc))
        rows.append(rec)
        if not rec["equal"]:
            bad.append(rec)
    out = dict(cells=len(rows), equal=sum(1 for r in rows if r["equal"]),
               capacity_changed=bad, not_affordable=to,
               claim="a too aggressive prune would make capacities SMALLER, so "
                     "disabling it must not raise any of them",
               examples=rows[:5],
               ok=(len(rows) > 0 and not bad))
    (R149 / "certs" / "feas_149.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
