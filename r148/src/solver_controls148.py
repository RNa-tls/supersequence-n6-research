#!/usr/bin/env python3
"""Round 148 Phase 11 -- POSITIVE CONTROLS for the two round-144 coexistence
solvers, on a real instance.

A negative verdict is only informative from a solver that can say YES.  The
third procedure (r147 uses src/l6_cover_bfs_146.py) carries its own control: it
reports the minimum number of tau-orbits that DOES cover F, and says NO at c
only because that minimum is larger.  The two round-144 solvers cannot be
controlled that way -- src/l6_circuit_coexist_144.py structurally requires
|F| = 4c and refuses any other c -- so they are controlled on a real length-872
cover instead: such a cover's own chain and its own c pure circuits ARE a
solution of exactly the instance the solver is asked about, so both solvers must
answer YES.

Existence only (`first_only=True`): these instances have astronomically many
solutions and enumerating them all is what made the round-146 attempt time out.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R148 = ROOT / "r148"
sys.path.insert(0, str(ROOT / "src"))
import l6_coexist_control_146 as CTL                                # noqa: E402


def main(argv):
    paths = argv or [str(ROOT / "data" / "verified_872_witness.txt")]
    rows = []
    for p in paths:
        W = Path(p).read_text().split()[0]
        t0 = time.time()
        # the decomposition is round 146's; the solver calls are made here so
        # the node cap can be raised -- round 146 used 60M and timed out
        ent, chain_ports, pure, P = CTL.decompose(W)
        c = len(pure)
        chain_idx = [CTL.lexrank(ent[x]) for x in chain_ports]
        chain_hex = {CTL.hexkey(ent[x]) for x in chain_ports}
        F = set(CTL.hexkey(q) for q in CTL.PERMS) - chain_hex
        r1 = (CTL.CO.coexist(chain_idx, c, node_cap=20_000_000_000,
                             first_only=True)
              if len(F) == 4 * c else dict(ok=None, reason="|F| != 4c"))
        r3 = (CTL.CO3.solve(chain_idx, c, first_only=True)
              if len(F) == 4 * c else dict(ok=None))
        r = dict(L=len(W), P=P, c=c, chain_ports=len(chain_ports),
                 predicted_chain_ports=120 - 4 * c, F=len(F),
                 dfs_ok=r1.get("ok"), dfs_nodes=r1.get("nodes"),
                 dfs_solutions=r1.get("solutions"),
                 subset_ok=r3.get("ok"), subset_nodes=r3.get("nodes"),
                 subset_solutions=r3.get("solutions"),
                 control_passes=(r1.get("ok") is True and r3.get("ok") is True
                                 and len(chain_ports) == 120 - 4 * c))
        r["source"] = str(Path(p).relative_to(ROOT))
        r["seconds"] = round(time.time() - t0, 1)
        rows.append(r)
        print(json.dumps(r), flush=True)
    out = dict(instances=rows,
               dfs_control_passes=all(x.get("dfs_ok") is True for x in rows),
               subset_control_passes=all(x.get("subset_ok") is True for x in rows),
               ok=all(x.get("control_passes") for x in rows))
    (R148 / "certs" / "solver_controls_148.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print("SOLVER POSITIVE CONTROLS OK:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
