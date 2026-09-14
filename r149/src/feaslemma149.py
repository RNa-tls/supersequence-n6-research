#!/usr/bin/env python3
"""Round 149 H -- auditing the feasibility prune AS A LEMMA.

`feas()` is the one prune the two implementations do not validate for each
other: implementation B's copy was written by translating the same idea, so a
shared conceptual error would survive their agreement.  It is inside the solver
but it changes the model's value, so it has to be audited.

FIRST ATTEMPT (failed, reported honestly).  Disable the prune and recompute.
This turns out to be impossible: `feas` is what makes even the d = 0 cells
tractable -- with it off, the smallest cell does not finish in 120 s.  So the
"turn it off" audit is UNAVAILABLE, not passed.

WHAT IS DONE INSTEAD.  Audit the lemma directly.

  LEMMA (feas).  At a search state let u_q be the number of unused phases of
  each opened orbit q other than the current one, let `tok` be the tokens left,
  and let `tot` be the sum of the u_q after zeroing the `tok` largest.  Then
  every completion of this walk ends with deficit >= tot.

  PROOF.  The final deficit is the total number of unused phases over the
  orbits the chain opens.  An orbit other than the current one can gain ports
  only if the chain RE-ENTERS it, and every re-entry is a non-clean-E step into
  an already-opened orbit, which costs exactly one token -- clean-E is tau and
  never leaves the current orbit (theorem 2.3 (C1)).  So at most `tok` of those
  orbits can lose any unused phases at all, and zeroing the largest u_q first
  minimises what remains.  Orbits opened LATER only add to the final deficit.  ∎

  CONSEQUENCE.  `tot > DMAX` means no completion can be recorded, so pruning is
  sound.  A violation would be a state on a walk that IS recorded whose prefix
  had tot > that walk's final deficit.

  THE TEST.  Take the walks that actually attain the capacities -- the witness
  certificates -- and evaluate `tot` at EVERY prefix, comparing it with the
  walk's own final deficit.  If the lemma is false the solver would have pruned
  one of these very walks, so this tests it exactly where it is load-bearing.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R149 = ROOT / "r147", ROOT / "r149"
sys.path.insert(0, str(R147 / "src"))
import catalogue147 as C                                            # noqa: E402

PERMS, ORB, PH, HEX = C.PERMS, C.ORB, C.PHASE, C.HEX
FREE, DA, DB, PAID, KIND, HEAVY = C.catalogue()
MOVE = {}
for i in range(720):
    MOVE[(i, FREE[i])] = "freeE"
    MOVE.setdefault((i, DA[i]), "dirtyA")
    MOVE.setdefault((i, DB[i]), "dirtyB")
    for j in range(5):
        MOVE.setdefault((i, PAID[i][j]), "paid")
    for t, _c in HEAVY[i]:
        MOVE.setdefault((i, t), "heavy")


def feas_tot(phm, corb, tok):
    """The solver's own quantity, recomputed here from the state."""
    us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                reverse=True)
    return sum(us[tok:])


def audit_walk(ports, b):
    """Evaluate the lemma at every prefix of a walk that attains a capacity."""
    phm = {ORB[ports[0]]: {PH[ports[0]]}}
    corb, tok = ORB[ports[0]], b
    worst = None
    final_orbits = len({ORB[v] for v in ports})
    final_deficit = 5 * final_orbits - len(ports)
    for i in range(len(ports) - 1):
        tot = feas_tot(phm, corb, tok)
        if worst is None or tot > worst:
            worst = tot
        if tot > final_deficit:
            return dict(ok=False, at=i, tot=tot, final_deficit=final_deficit)
        u, t = ports[i], ports[i + 1]
        name = MOVE.get((u, t))
        q = ORB[t]
        fresh = q not in phm
        if not (name == "freeE" or fresh):
            tok -= 1
        phm.setdefault(q, set()).add(PH[t])
        corb = q
    return dict(ok=True, max_tot_over_prefixes=worst,
                final_deficit=final_deficit, ports=len(ports))


def main():
    cert = json.loads((R149 / "certs" / "certcheck_149.json").read_text())
    rows, bad = [], []
    cdir = R149 / "logs" / "cert"
    for rec in cert["detail"]:
        if rec.get("status") != "ATTAINABILITY_VERIFIED":
            continue
        cell = tuple(rec["cell"])
        wp = cdir / ("wit_%d_%d_%d_%d_%d_%d.jsonl" % cell)
        if not wp.exists():
            continue
        for ln in wp.read_text().splitlines()[:40]:
            if not ln.strip():
                continue
            ports = json.loads(ln)["ports"]
            r = audit_walk(ports, cell[0])
            r["cell"] = list(cell)
            rows.append(r)
            if not r["ok"]:
                bad.append(r)
    out = dict(
        turn_it_off_audit="UNAVAILABLE -- with the prune disabled even the "
                          "smallest cell does not finish in 120 s, so the "
                          "comparison could not be run and is NOT claimed",
        walks_audited=len(rows), violations=len(bad), examples=bad[:4],
        sample=rows[:4],
        lemma="at every prefix of a walk that attains its cell's capacity, the "
              "prune's quantity tot never exceeds that walk's final deficit, so "
              "the prune never discarded it",
        ok=(len(rows) > 0 and not bad))
    (R149 / "certs" / "feaslemma_149.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("examples", "sample")}, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
