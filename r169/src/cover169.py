#!/usr/bin/env python3
"""Round 169 phases 5-8 and 11 -- a feasible certificate set under (P1).

The matching-bound method that closed rounds 165 and 167 does NOT close here:
33 cells are individually necessary, but those 33 leave four exposed rows
open.  So 33 is a proved LOWER bound and nothing more, and this module builds
an explicit feasible set to bracket the answer from above.

Construction: start from the 33 necessary cells, add candidates greedily by
rows newly closed per unit of projected generation cost, then run redundancy
elimination so the result is minimAL (no member can be dropped) even though it
is not proved minimUM.  The gap between the lower bound and the constructed
set is reported, not papered over.

Cost note.  Under (P1) a cell whose required bound already follows from a
selected dominator needs no certificate at all, which is exactly why 221 of
the 254 candidates came out redundant.  What has to be paid for is the
(P1)-maximal cells of the selection -- the ones with no selected dominator.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem, chain_dom                    # noqa: E402
from recheck168 import parse, cellstr                             # noqa: E402
from state169 import certified_from_proof_objects, sha            # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def main():
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    assert src["p1"]["holds"]
    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD}
    N = {parse(r["cell"]): r["nodes"] for r in rows if r["status"] in GOOD}
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    U167 = {parse(c) for c in st["universe_cells"]}
    CERT, _p = certified_from_proof_objects()

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)
    single = {K for K in S.chain_tab if K not in S.dual_chain}
    univ = sorted(U167 | single)
    E = {parse(c) for c in src["minimum"]["cells"]}

    def closed(sel):
        S.apply(sel)
        v = S.verdicts(EXS)
        return [k for k in EX if v[k] == "STRICTLY_CLOSED"]

    def cost(K):
        return N.get(K) or max(N.values())

    t0 = time.time()
    sel = set(E)
    have = len(closed(sel))
    trace = [dict(step=0, added=None, selected=len(sel), rows_closed=have)]
    while have < len(EX):
        best = None
        for K in univ:
            if K in sel:
                continue
            g = len(closed(sel | {K})) - have
            if g <= 0:
                continue
            score = g / max(cost(K), 1)
            if best is None or score > best[0]:
                best = (score, g, K)
        if best is None:
            break
        _s, g, K = best
        sel.add(K)
        have += g
        trace.append(dict(step=len(trace), added=cellstr(K), gain=g,
                          projected_nodes=cost(K), selected=len(sel),
                          rows_closed=have))
        print(f"  + {cellstr(K):>16} gain={g:<4} rows={have}/{len(EX)} "
              f"selected={len(sel)}", flush=True)

    feasible = have == len(EX)
    # redundancy elimination, most expensive first
    if feasible:
        for K in sorted(sel, key=lambda K: -cost(K)):
            if len(closed(sel - {K})) == len(EX):
                sel.discard(K)
    final_rows = len(closed(sel))

    maximal = [K for K in sel
               if not any(J != K and chain_dom(J, K) for J in sel)]
    out = dict(
        inputs={p: sha(p) for p in ("r169/certs/p1_closure_169.json",
                                    "r168/certs/state_168.json",
                                    "r152/certs/verify_all_c152.json")},
        exposed_rows=len(EX),
        lower_bound=dict(cells=len(E), proved_by="every feasible subset of "
                                                 "the candidate universe "
                                                 "contains each individually "
                                                 "necessary cell",
                         is_feasible_alone=False),
        constructed=dict(
            cells=len(sel), feasible=feasible and final_rows == len(EX),
            rows_closed=final_rows,
            minimal="no member can be dropped without reopening a row",
            p1_maximal_members=len(maximal),
            already_certified=len(set(CERT) & sel),
            still_to_generate=len(sel - set(CERT)),
            projected_nodes=sum(cost(K) for K in sel - set(CERT)),
            members=sorted(cellstr(K) for K in sel),
            p1_maximal_cells=sorted(cellstr(K) for K in maximal)),
        gap=dict(lower=len(E), upper=len(sel),
                 note="the exact minimum is not proved; it lies in this "
                      "interval"),
        round_167_minimum=190,
        round_167_remaining_nodes=82812460012,
        greedy_trace=trace,
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = out["constructed"]["feasible"]
    (ROOT / "r169" / "certs" / "cover_169.json").write_text(
        json.dumps({k: v for k, v in out.items()
                    if k != "seconds_noncanonical"},
                   ensure_ascii=False, indent=1) + "\n")
    show = json.loads(json.dumps(out))
    show.pop("inputs"); show.pop("greedy_trace")
    show["constructed"].pop("members")
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
