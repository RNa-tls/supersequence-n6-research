#!/usr/bin/env python3
"""Round 167 phases 6-14 -- the ROW-level bridge-aware optimum.

Round 165 proved that 288 capacity FACTS are individually load bearing.  That
is a statement about facts, not about certificates.  Round 166 added a
certified cross-model implication and this round completes it:

    (BRIDGE-LE)  cap_piece(b, d, fp, lp) <= cap_chain(b, d, 0, 0, 0, 0)
    (BRIDGE-EQ)  cap_piece(b, d, 0,  0 )  = cap_chain(b, d, 0, 0, 0, 0)

Both come from the walk-set argument of round 166: at a = bb = e = h = 0 the
chain catalogue admits exactly the piece moves (checked for all 720 sources),
tokens and deficits are charged identically, and a mask is a restriction.  So
the two walk sets are EQUAL at fp = lp = 0 and nested otherwise.  Nothing here
uses the observed numerical agreement of the two tables as evidence; the
agreement is reported as a corroboration only.

Consequences for the certificate universe:

  * The only machine-independent second route that exists in this repository
    is the chain-model exhaustion tree (L6-EXTREE-*).  There is no piece-model
    exhaustion generator.  So the certificate universe IS the set of chain
    cells, and a masked piece value can only be supported through (BRIDGE-LE).
  * By (BRIDGE-EQ) a certificate at (b, d, 0, 0, 0, 0) also establishes the
    piece value at (b, d, 0, 0), and conversely an already dual-route piece
    value at (b, d, 0, 0) establishes the chain value at (b, d, 0, 0, 0, 0)
    for free.  Those "free" imports are counted, not certified.

The objective solved here is the row-level one: choose the cheapest set of
chain certificates that restores STRICT CLOSURE of all 181 exposed census
rows.  Optimality is proved the same way round 165 proved the basis: the
universe is shown feasible, every member is tested for individual necessity,
and the necessary set alone is shown feasible.  Necessity is a lower bound
because closure is monotone in the granted set, so a set that omits a
necessary cell is a subset of U minus that cell, which already fails.
"""
from __future__ import annotations
import hashlib, json, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
import hidden163 as H                                             # noqa: E402
import closure165 as CL                                           # noqa: E402

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
HEX = 120


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def fallback(K):
    return HEX + K[2] + K[3] + K[4]


class System:
    """The enlarged rule system, parameterised by the granted chain certs."""

    def __init__(self):
        H.load()
        self.chain_tab = dict(H.CERT)
        self.piece_tab = dict(H.PCERT)
        self.chain_nodes = {tuple(int(x) for x in r["cell"].split("|")):
                            r.get("nodes", 0)
                            for r in json.loads(
                                (CERTS / "verify_all_c152.json").read_text())
                            ["rows"] if r["status"] in GOOD}
        self.piece_nodes = {(r["b"], r["d"], r["fp"], r["lp"]):
                            r.get("nodes", 0)
                            for r in json.loads(
                                (CERTS / "verify_piece_c152.json").read_text())
                            ["rows"] if r["status"] in GOOD}
        tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
        vg = json.loads((ROOT / "r164" / "certs"
                         / "verifygen_164.json").read_text())
        done = {tuple(int(x) for x in s.split("|"))
                for s in vg["targets_upper_certified_by_two_validators"]}
        self.wchain = {tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]
                       if tuple(c) not in done}
        self.wpiece = {tuple(c) for c in tg["PIECE_SINGLE_IMPL"]
                       if tuple(c) not in done}
        self.keep_chain = {k: v for k, v in self.chain_tab.items()
                           if k not in self.wchain}
        self.keep_piece = {k: v for k, v in self.piece_tab.items()
                           if k not in self.wpiece}
        self.groups = CL.grouped()

    # ---- the value a certificate for chain cell K would establish.  For a
    # cell present in the round-152 chain table this is that table's value.
    # For a cell absent from it but whose piece counterpart is tabulated,
    # (BRIDGE-EQ) predicts the value exactly; the prediction is checked when
    # the certificate is actually generated.
    def value_of(self, K):
        if K in self.chain_tab:
            return self.chain_tab[K], "chain table"
        if K[2:] == (0, 0, 0, 0) and (K[0], K[1], 0, 0) in self.piece_tab:
            return self.piece_tab[(K[0], K[1], 0, 0)], "predicted by BRIDGE-EQ"
        return None, "unknown"

    def materialize(self, granted):
        chain = dict(self.keep_chain)
        for K in granted:
            v, _ = self.value_of(K)
            if v is not None and v < chain.get(K, 10 ** 9):
                chain[K] = v
        piece = dict(self.keep_piece)
        # (BRIDGE-EQ): the level-zero value is shared by the two models
        Z = {}
        for K, v in chain.items():
            if K[2:] == (0, 0, 0, 0):
                Z[(K[0], K[1])] = min(v, Z.get((K[0], K[1]), 10 ** 9))
        for (b, d, fp, lp), v in piece.items():
            if (fp, lp) == (0, 0):
                Z[(b, d)] = min(v, Z.get((b, d), 10 ** 9))
        cert = {K: v for K, v in chain.items() if v < fallback(K)}
        for (b, d), v in Z.items():
            K = (b, d, 0, 0, 0, 0)
            if v < HEX and v < cert.get(K, 10 ** 9):
                cert[K] = v
        pcert = dict(piece)
        for (b, d), v in Z.items():                      # (BRIDGE-LE)
            if v >= HEX:
                continue
            for fp in (0, 1):
                for lp in (0, 1):
                    p = (b, d, fp, lp)
                    if v < pcert.get(p, HEX):
                        pcert[p] = v
        pcert = {p: v for p, v in pcert.items() if v < HEX}
        H.CERT.clear(); H.CERT.update(cert)
        H.PCERT.clear(); H.PCERT.update(pcert)
        H.best.cache_clear()

    def full(self):
        """The audited round-152 system: both tables, nothing withdrawn."""
        H.CERT.clear(); H.CERT.update(self.chain_tab)
        H.PCERT.clear(); H.PCERT.update(self.piece_tab)
        H.best.cache_clear()

    def open_rows(self, granted, keys, detail=False):
        self.materialize(granted)
        r = CL.evaluate(self.groups, keys)
        o = sorted(k for k in keys if r[k]["verdict"] != "STRICTLY_CLOSED")
        return (o, r) if detail else o


def main():
    S = System()
    t0 = time.time()

    # ---------- baseline and the exposed rows, recomputed here
    S.full()
    base_full = CL.evaluate(S.groups)
    tally_full = Counter(v["verdict"] for v in base_full.values())
    nothing = S.open_rows(set(), set(base_full))
    exposed = sorted(k for k in nothing
                     if base_full[k]["verdict"] == "STRICTLY_CLOSED")
    EX = set(exposed)
    # round 165 withdrew the same cells but had no bridge, so its exposed set
    # is a superset: a row that the free bridge imports already close is not
    # exposed here.  The difference is identified rather than glossed over.
    CL.withdraw([], [])                       # no-op, keeps the API honest
    H.CERT.clear(); H.CERT.update({k: v for k, v in S.chain_tab.items()
                                   if k not in S.wchain})
    H.PCERT.clear(); H.PCERT.update({k: v for k, v in S.piece_tab.items()
                                     if k not in S.wpiece})
    H.best.cache_clear()
    r165_open = CL.evaluate(S.groups, set(base_full))
    exposed_165 = sorted(k for k in base_full
                         if base_full[k]["verdict"] == "STRICTLY_CLOSED"
                         and r165_open[k]["verdict"] != "STRICTLY_CLOSED")
    free_rows = sorted(set(exposed_165) - EX)

    # ---------- phase 6: which cells does the census actually consult?
    QC, QP = set(), set()
    _CC, _PC = H.CC, H.PC

    def CC(b, d, a, bb, e, h=0):
        QC.add((b, d, a, bb, e, h)); return _CC(b, d, a, bb, e, h)

    def PC(b, d, fp, lp):
        QP.add((b, d, fp, lp)); return _PC(b, d, fp, lp)

    H.CC, H.PC = CC, PC
    S.materialize(set())                     # weakest system -> widest search
    CL.evaluate(S.groups, EX)
    S.materialize(U0 := set(S.chain_tab))    # every certificate granted
    CL.evaluate(S.groups, EX)
    S.full()                                 # the audited system
    CL.evaluate(S.groups, EX)
    H.CC, H.PC = _CC, _PC

    # ---------- the certificate universe
    avail0 = set()
    S.materialize(set())
    for K in QC:
        if K in H.CERT:
            avail0.add(K)
    univ = []
    for K in sorted(QC):
        v, how = S.value_of(K)
        if v is None or v >= fallback(K) or K in avail0:
            continue
        univ.append(K)
    U = set(univ)

    # ---------- phase 7: feasibility of the universe
    open_U = S.open_rows(U, EX)
    open_none = S.open_rows(set(), EX)

    # ---------- necessity of each member (the matching lower bound)
    nec, red = [], []
    per_cell, witness, guard = {}, {}, {}
    for K in univ:
        o, det = S.open_rows(U - {K}, EX, detail=True)
        per_cell["|".join(map(str, K))] = len(o)
        if o:
            w = o[0]
            guard["|".join(map(str, K))] = [[k[0], list(k[1])] for k in o]
            witness["|".join(map(str, K))] = dict(
                layer=867 + w[0], row=dict(zip(H.COORD, w[1])),
                required=det[w]["required"],
                bounds_without_this_cell={m: v for m, v
                                          in det[w]["bounds"].items()},
                verdict=det[w]["verdict"])
        (nec if o else red).append(K)
    E = set(nec)
    open_E = S.open_rows(E, EX)

    # ---------- phase 13-A: does the FACT-level plan of phases 0-5 close the
    # rows?  It supports every essential fact, but through weaker bridged
    # values, so this has to be checked and not assumed.
    g = json.loads((ROOT / "r165" / "certs"
                    / "row_closure_graph_165.json").read_text())
    ess = set(g["essential_cells"])
    chain_facts = sorted(c for c in ess if g["ablation"][c]["model"] == "chain")
    piece_facts = sorted(c for c in ess if g["ablation"][c]["model"] == "piece")
    factset = {tuple(int(x) for x in c.split("|")) for c in chain_facts}
    for c in piece_facts:
        b, d = (int(x) for x in c.split("|")[:2])
        factset.add((b, d, 0, 0, 0, 0))
    factset_raw = set(factset)
    factset = {K for K in factset
               if S.value_of(K)[0] is not None and K not in avail0}
    open_A = S.open_rows(factset, EX)

    # ---------- cost
    def nodes(K):
        if K in S.chain_nodes and S.chain_nodes[K]:
            return S.chain_nodes[K], "measured chain search"
        p = (K[0], K[1], 0, 0)
        if K[2:] == (0, 0, 0, 0) and S.piece_nodes.get(p):
            return S.piece_nodes[p], "measured piece search (same cell)"
        best = None
        for k, v in S.chain_nodes.items():
            if v and all(a <= b for a, b in zip(K, k)):
                best = v if best is None else min(best, v)
        return best, "estimated from the cheapest measured dominating cell"

    def cost(cells):
        tot, unknown = 0, 0
        for K in cells:
            n, _ = nodes(K)
            if n is None:
                unknown += 1
            else:
                tot += n
        return tot, unknown

    cU, _ = cost(U); cE, _ = cost(E); cA, _ = cost(factset)
    rep = json.loads((ROOT / "r166" / "certs"
                      / "verification_166.json").read_text())
    assert rep["all_ok"]
    DONE = set()
    import gzip
    sys.path.insert(0, str(ROOT / "r166" / "src"))
    import extree_basis_verify as V
    for rel in ("r164/certs/extree_prefix_164.txt.gz",
                "r166/certs/extree_batch2_166.txt.gz",
                "r166/certs/extree_batch3_166.txt.gz"):
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for cell, capv, _ in V.parse_batch(text)[1]:
            DONE.add(tuple(cell))
    old = sum(S.chain_nodes.get(tuple(int(x) for x in c.split("|")), 0)
              for c in chain_facts)
    for c in piece_facts:
        b, d, fp, lp = (int(x) for x in c.split("|"))
        old += S.piece_nodes.get((b, d, fp, lp), 0)

    out = dict(
        inputs={p: sha(p) for p in
                ("r165/certs/row_closure_graph_165.json",
                 "r164/certs/targets_164.json",
                 "r164/certs/verifygen_164.json",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json",
                 "r163/src/hidden163.py", "r165/src/closure165.py")},
        baseline=dict(rows=len(base_full), tally=dict(tally_full),
                      reproduces_round_152=(tally_full["STRICTLY_CLOSED"] == 1607
                                            and tally_full["EQUALITY"] == 2)),
        exposed_rows=len(exposed),
        round_165_exposed_rows=len(exposed_165),
        round_165_count_reproduced=len(exposed_165) == 181,
        rows_closed_for_free_by_the_bridge=[
            dict(layer=f"L{867 + k[0]}", row=dict(zip(H.COORD, k[1])))
            for k in free_rows],
        consulted=dict(chain_cells=len(QC), piece_cells=len(QP),
                       chain_cells_in_the_152_table=sum(1 for K in QC
                                                        if K in S.chain_tab),
                       chain_cells_only_predicted=sorted(
                           "|".join(map(str, K)) for K in QC
                           if K not in S.chain_tab
                           and S.value_of(K)[0] is not None),
                       chain_cells_with_no_value=sorted(
                           "|".join(map(str, K)) for K in QC
                           if S.value_of(K)[0] is None),
                       argument="a certificate for a cell the census never "
                                "consults cannot change any bound, so the "
                                "universe below is complete"),
        universe=dict(size=len(U),
                      cells=sorted("|".join(map(str, K)) for K in U),
                      feasible=not open_U, rows_left_open=len(open_U)),
        with_nothing_granted=dict(rows_left_open=len(open_none)),
        optimum=dict(
            necessary=len(nec),
            redundant=len(red),
            cells=sorted("|".join(map(str, K)) for K in nec),
            necessary_set_is_feasible=not open_E,
            rows_left_open_for_the_necessary_set=len(open_E),
            proof=("every granted certificate only lowers bounds, so closure "
                   "is monotone; a cell K with open_rows(U - {K}) nonempty is "
                   "in every feasible subset of U, because any such subset is "
                   "contained in U - {K}.  The necessary cells therefore give "
                   "a lower bound, and the necessary set is itself feasible, "
                   "so it is THE minimum and it is unique."),
            minimum_is_proved=(not open_U) and (not open_E),
            per_cell_rows_opened_when_dropped=per_cell,
            witness_rows=witness,
            guarded_rows=guard),
        fact_level_plan=dict(
            certificates=len(factset),
            before_dropping_free_and_valueless_cells=len(factset_raw),
            dropped_because_already_free=sorted(
                "|".join(map(str, K)) for K in factset_raw if K in avail0),
            equals_the_row_level_optimum=(factset == E),
            extra_over_the_optimum=sorted("|".join(map(str, K))
                                          for K in factset - E),
            missing_from_the_optimum=sorted("|".join(map(str, K))
                                            for K in E - factset),
            closes_every_exposed_row=not open_A,
            rows_left_open=len(open_A),
            note="objective A of phase 13: support all 288 round-165 facts. "
                 "It is NOT automatically sufficient for row closure because "
                 "a masked piece fact is supported only by the weaker bridged "
                 "value, so this is checked."),
        already_certified=dict(
            cells=sorted("|".join(map(str, K)) for K in DONE),
            in_the_optimum=sorted("|".join(map(str, K)) for K in DONE & E),
            count_in_the_optimum=len(DONE & E),
            remaining=len(E - DONE),
            remaining_nodes=cost(E - DONE)[0]),
        predicted_value_cells=dict(
            cells=sorted("|".join(map(str, K)) for K in U
                         if K not in S.chain_tab),
            in_the_optimum=sorted("|".join(map(str, K)) for K in E
                                  if K not in S.chain_tab),
            note="these chain cells are absent from the round-152 table; "
                 "(BRIDGE-EQ) predicts their capacity from the tabulated "
                 "piece value at (b,d,0,0).  The prediction is a planning "
                 "input, not a proof step: the generated certificate reports "
                 "the true value and must be re-checked against it."),
        cost=dict(old_plan_all_288_facts=old,
                  old_plan_note="the piece half of this figure is hypothetical: "
                                "no piece-model exhaustion generator exists, "
                                "and the round-152 piece search reuses one tree "
                                "for several masks, so the piece contribution "
                                "is an upper estimate",
                  universe=cU, fact_level_plan=cA, row_level_optimum=cE,
                  savings_vs_old=old - cE,
                  per_cell_of_the_optimum={
                      "|".join(map(str, K)): nodes(K)[0] for K in
                      sorted(E, key=lambda K: (-(nodes(K)[0] or 0), K))}),
        seconds=round(time.time() - t0, 1),
    )
    out["ok"] = (out["baseline"]["reproduces_round_152"]
                 and out["round_165_count_reproduced"]
                 and out["optimum"]["minimum_is_proved"])
    (ROOT / "r167" / "certs" / "row_optimum_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = {k: v for k, v in out.items() if k != "inputs"}
    show["universe"] = {k: v for k, v in show["universe"].items()
                        if k != "cells"}
    show["optimum"] = {k: v for k, v in show["optimum"].items()
                       if k not in ("cells", "per_cell_rows_opened_when_dropped")}
    show["cost"] = {k: v for k, v in show["cost"].items()
                    if k != "per_cell_of_the_optimum"}
    show["already_certified"] = {k: v for k, v in show["already_certified"].items()
                                 if k != "cells"}
    show["predicted_value_cells"] = {
        k: v for k, v in show["predicted_value_cells"].items() if k != "note"}
    show["fact_level_plan"] = {k: v for k, v in show["fact_level_plan"].items()
                               if k != "note"}
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
