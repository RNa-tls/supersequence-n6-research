#!/usr/bin/env python3
"""Round 165 phase 12 -- SAT / UNSAT pilot on the PIECE model.

Why the piece model.  In the chain model a move's resource effect depends on
the (source, target) pair across all 518,400 pairs, so a propositional
encoding needs ~32M clauses per instance.  The piece model is far tighter:
only clean E and the five paid targets are legal, every port must sit in a
FRESH hexagon, and -- the key observation -- both budgets collapse to
CARDINALITY constraints:

    blocks   = 1 + (number of paid moves)
    tokens   = blocks - (number of distinct orbits used)
    deficit  = 5*(orbits) - (ports)

so for a fixed number of ports T,

    deficit <= d      <=>   orbits <= (d + T) // 5
    tokens  <= b      <=>   paid   <= b - 1 + orbits

Both are sums over indicator variables.  That is what makes this encodable.

The encoding is derived from the mathematical model above, NOT from the
production DFS: no search state, no pruning, no move ordering appears in it.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
import routeb164 as R                                             # noqa: E402

from pysat.card import CardEnc, EncType, ITotalizer                # noqa: E402
from pysat.formula import IDPool                                   # noqa: E402
from pysat.solvers import Cadical153                               # noqa: E402

N = R.N


def build(cell, T, norb):
    """Clauses for 'a legal piece with T ports and EXACTLY norb orbits exists'.

    The orbit count is pinned rather than coupled, because the token bound
    tok = 1 + paid - orbits <= b is a relation between two sums.  Pinning
    orbits turns it into the plain cardinality bound paid <= b - 1 + norb, and
    the whole question is the disjunction over the finitely many legal norb.
    """
    b, d, fp, lp = cell
    pool = IDPool()
    cls = []

    def x(i, p):
        return pool.id(("x", i, p))

    def o(q):
        return pool.id(("o", q))

    def e(i):
        return pool.id(("e", i))

    # 1. start at port 0, exactly one port per step
    cls.append([x(0, 0)])
    for i in range(T):
        cls.append([x(i, p) for p in range(N)])
        cls.extend(CardEnc.atmost([x(i, p) for p in range(N)], bound=1,
                                  vpool=pool, encoding=EncType.seqcounter))
    # 2. every port lies in a FRESH hexagon -> at most one step per hexagon
    byhex = {}
    for p in range(N):
        byhex.setdefault(R.HEX[p], []).append(p)
    for h, ps in byhex.items():
        lits = [x(i, p) for i in range(T) for p in ps]
        cls.extend(CardEnc.atmost(lits, bound=1, vpool=pool,
                                  encoding=EncType.seqcounter))
    # 3. transitions: from u only clean E or one of the five paid targets,
    #    and e[i] holds exactly when the move is paid
    for i in range(T - 1):
        for u in range(N):
            allowed = [R.FREE[u]] + list(R.PAID[u])
            cls.append([-x(i, u)] + [x(i + 1, t) for t in allowed])
            cls.append([-x(i, u), -x(i + 1, R.FREE[u]), -e(i)])
            for t in R.PAID[u]:
                cls.append([-x(i, u), -x(i + 1, t), e(i)])
    # 4. orbit indicators, both directions
    byorb = {}
    for p in range(N):
        byorb.setdefault(R.ORB[p], []).append(p)
    for q, ps in byorb.items():
        lits = [x(i, p) for i in range(T) for p in ps]
        for l in lits:
            cls.append([-l, o(q)])
        cls.append([-o(q)] + lits)
    # 5. pin the orbit count
    ovars = [o(q) for q in sorted(byorb)]
    cls.extend(CardEnc.atmost(ovars, bound=norb, vpool=pool,
                              encoding=EncType.seqcounter))
    cls.extend(CardEnc.atleast(ovars, bound=norb, vpool=pool,
                               encoding=EncType.seqcounter))
    # 6. tokens: with the orbit count pinned, paid <= b - 1 + norb
    evars = [e(i) for i in range(T - 1)]
    pbound = b - 1 + norb
    if pbound < 0:
        cls.append([])
    elif pbound < len(evars):
        cls.extend(CardEnc.atmost(evars, bound=pbound, vpool=pool,
                                  encoding=EncType.seqcounter))
    # 7. the mask: a partial FIRST / LAST block
    if fp:
        lits = [e(i) for i in range(min(4, T - 1))]
        cls.append(lits if lits else [])
    if lp:
        lits = [e(i) for i in range(max(0, T - 5), T - 1)]
        cls.append(lits if lits else [])
    stats = dict(ports=T, orbits=norb, variables=pool.top, clauses=len(cls))
    return cls, pool, stats


def run_cell(cell, cap, want, proof=False):
    """Decide 'is there a legal piece with T ports?' as a disjunction over the
    orbit count.  UNSAT for every admissible norb proves UNSAT overall."""
    b, d, fp, lp = cell
    T = cap + (1 if want == "UNSAT" else 0)
    subs, sat = [], False
    tvars = tcls = tbuild = tsolve = 0
    proof_lines = proof_bytes = 0
    # deficit = 5*norb - T <= d, and a piece has at least one orbit
    lo, hi = 1, (d + T) // 5
    for m in range(lo, hi + 1):
        t0 = time.time()
        cls, pool, stats = build(cell, T, m)
        tbuild += time.time() - t0
        tvars = max(tvars, stats["variables"])
        tcls += stats["clauses"]
        t0 = time.time()
        with Cadical153(bootstrap_with=cls, with_proof=proof) as s:
            r = s.solve()
            pr = s.get_proof() if (proof and not r) else None
        tsolve += time.time() - t0
        if pr is not None:
            proof_lines += len(pr)
            proof_bytes += sum(len(y) + 1 for y in pr)
        subs.append(dict(orbits=m, result="SAT" if r else "UNSAT",
                         clauses=stats["clauses"]))
        if r:
            sat = True
            break
    out = dict(cell="|".join(map(str, cell)), cap=cap, ports_tested=T,
               expected=want, result="SAT" if sat else "UNSAT",
               agrees=(("SAT" if sat else "UNSAT") == want),
               orbit_cases=len(subs), orbit_range=[lo, hi],
               max_variables=tvars, total_clauses=tcls,
               build_seconds=round(tbuild, 1),
               solve_seconds=round(tsolve, 1), subproblems=subs)
    if proof:
        out["proof_lines"] = proof_lines
        out["proof_bytes"] = proof_bytes
    return out


def main():
    pc, order = R.parse_pcert(ROOT / "r152" / "certs" / "pcert_all_152.txt")
    graph = json.loads((ROOT / "r165" / "certs"
                        / "row_closure_graph_165.json").read_text())
    ess_piece = [c for c in graph["essential_cells"]
                 if graph["ablation"][c]["model"] == "piece"]
    caps = {c: pc[tuple(int(x) for x in c.split("|"))]["cap"]
            for c in ess_piece}

    rows = []
    # (a) CORRECTNESS: a small, already dual-certified cell, both directions
    for cell, want in (((0, 0, 0, 0), "SAT"), ((0, 0, 0, 0), "UNSAT"),
                       ((0, 2, 0, 0), "SAT"), ((0, 2, 0, 0), "UNSAT")):
        cap = pc[cell]["cap"]
        rows.append(run_cell(cell, cap, want, proof=(want == "UNSAT")))
        print(json.dumps(rows[-1]), flush=True)
    # (b) SCALING: the cheapest basis piece cell by capacity
    cheap = min(caps, key=lambda c: caps[c])
    k = tuple(int(x) for x in cheap.split("|"))
    rows.append(run_cell(k, caps[cheap], "UNSAT", proof=True))
    print(json.dumps({y: rows[-1][y] for y in
                      ("cell", "cap", "max_variables", "total_clauses",
                       "result", "orbit_cases", "build_seconds",
                       "solve_seconds")}), flush=True)

    out = dict(
        model="piece",
        encoding="derived from the block/orbit arithmetic, not from the "
                 "production DFS: tokens = 1 + paid - orbits and "
                 "deficit = 5*orbits - ports, so both budgets are cardinality "
                 "constraints",
        solver="Cadical153 via python-sat 1.9.dev15",
        correctness_checks=[r for r in rows[:4]],
        all_correctness_checks_agree=all(r["agrees"] for r in rows[:4]),
        scaling_probe=rows[4],
        cheapest_basis_piece_cell=cheap,
        rows=rows)
    out["ok"] = out["all_correctness_checks_agree"]
    (ROOT / "r165" / "certs" / "sat_pilot_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1)[:2000])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
