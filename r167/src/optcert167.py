#!/usr/bin/env python3
"""Round 167 phases 8, 10-12, 14 -- the optimality certificate and its checker.

The solver (rowopt167.py) proves the optimum by 222 full evaluations of the
180 exposed rows.  That is too big to re-check by hand.  This module extracts
a certificate that carries the same proof in O(190) SINGLE-ROW evaluations:

    UPPER BOUND.  Granting the 190 listed cells closes all 180 exposed rows.
                  One evaluation.
    LOWER BOUND.  For each listed cell K there is ONE named row that is not
                  strictly closed when every cell of the universe EXCEPT K is
                  granted.  Because granting a certificate only lowers bounds,
                  any feasible subset of the universe that omits K is contained
                  in U - {K} and therefore also leaves that row open.  So every
                  feasible set contains all 190 cells.

Upper and lower bound meet, so 190 is the minimum and the minimiser is unique.
Uniqueness is stronger than minimum cardinality: since the optimum is contained
in EVERY feasible set, it simultaneously minimises every monotone cost -- node
count, storage, wall clock.  Phase 8's three weighted problems therefore have
the same answer and need no separate optimisation.

The checker below re-derives the census rows from round 163's independent
reimplementation and re-materialises the rule system from the certificate's
own text.  It does not import the solver.
"""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import hidden163 as H                                             # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
HEX = 120
BATCHES = ("r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def cellstr(K):
    return "|".join(map(str, K))


def parse(s):
    return tuple(int(x) for x in s.split("|"))


# ------------------------------------------------------------------ rule system
class Rules:
    """base + granted, closed under (BRIDGE-EQ) and (BRIDGE-LE)."""

    def __init__(self):
        H.load()
        self.chain_tab, self.piece_tab = dict(H.CERT), dict(H.PCERT)
        tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
        vg = json.loads((ROOT / "r164" / "certs"
                         / "verifygen_164.json").read_text())
        done = {parse(s) for s
                in vg["targets_upper_certified_by_two_validators"]}
        self.wchain = {tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]
                       if tuple(c) not in done}
        self.wpiece = {tuple(c) for c in tg["PIECE_SINGLE_IMPL"]
                       if tuple(c) not in done}
        self.keep_chain = {k: v for k, v in self.chain_tab.items()
                           if k not in self.wchain}
        self.keep_piece = {k: v for k, v in self.piece_tab.items()
                           if k not in self.wpiece}

    def value_of(self, K):
        if K in self.chain_tab:
            return self.chain_tab[K]
        if K[2:] == (0, 0, 0, 0):
            return self.piece_tab.get((K[0], K[1], 0, 0))
        return None

    def apply(self, granted, override=None):
        chain = dict(self.keep_chain)
        for K in granted:
            v = self.value_of(K)
            if override and K in override:
                v = override[K]
            if v is not None:
                chain[K] = min(v, chain.get(K, 10 ** 9))
        Z = {}
        for K, v in chain.items():
            if K[2:] == (0, 0, 0, 0):
                Z[K[:2]] = min(v, Z.get(K[:2], 10 ** 9))
        for (b, d, fp, lp), v in self.keep_piece.items():
            if (fp, lp) == (0, 0):
                Z[(b, d)] = min(v, Z.get((b, d), 10 ** 9))
        cert = {K: v for K, v in chain.items()
                if v < HEX + K[2] + K[3] + K[4]}
        for (b, d), v in Z.items():
            K = (b, d, 0, 0, 0, 0)
            if v < HEX and v < cert.get(K, 10 ** 9):
                cert[K] = v
        pcert = dict(self.keep_piece)
        for (b, d), v in Z.items():
            if v >= HEX:
                continue
            for fp in (0, 1):
                for lp in (0, 1):
                    if v < pcert.get((b, d, fp, lp), HEX):
                        pcert[(b, d, fp, lp)] = v
        H.CERT.clear(); H.CERT.update(cert)
        H.PCERT.clear(); H.PCERT.update({p: v for p, v in pcert.items()
                                         if v < HEX})
        H.best.cache_clear()

    def full(self):
        H.CERT.clear(); H.CERT.update(self.chain_tab)
        H.PCERT.clear(); H.PCERT.update(self.piece_tab)
        H.best.cache_clear()


def groups_by_layer():
    out = {}
    for t in (0, 1, 2, 3, 4):
        g = defaultdict(list)
        for r in H.rows(t):
            g[tuple(r[c] for c in H.COORD)].append(r)
        out[t] = dict(g)
    return out


def closed(variants):
    req, b = H.bounds(variants)
    return (bool(b) and min(b.values()) < req), req, b


def done_cells():
    rep = json.loads((ROOT / "r166" / "certs"
                      / "verification_166.json").read_text())
    assert rep["all_ok"], "the pinned round-166 verification is not all_ok"
    out = set()
    for rel in BATCHES:
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for cell, _capv, _toks in V.parse_batch(text)[1]:
            out.add(tuple(cell))
    return out


def main():
    t0 = time.time()
    src = json.loads((ROOT / "r167" / "certs"
                      / "row_optimum_167.json").read_text())
    assert src["ok"]
    R = Rules()
    G = groups_by_layer()
    U = {parse(c) for c in src["universe"]["cells"]}
    OPT = {parse(c) for c in src["optimum"]["cells"]}
    wit = src["optimum"]["witness_rows"]

    # ---------- the exposed rows, re-derived
    R.full()
    base = {(t, k): closed(v)[0] for t, g in G.items() for k, v in g.items()}
    R.apply(set())
    now = {(t, k): closed(v)[0] for t, g in G.items() for k, v in g.items()}
    EX = sorted(k for k in base if base[k] and not now[k])

    # ---------- upper bound: one evaluation
    R.apply(OPT)
    still = [k for k in EX if not closed(G[k[0]][k[1]])[0]]

    # ---------- lower bound: one row per cell
    bad = []
    for K in sorted(OPT):
        w = wit[cellstr(K)]
        key = (w["layer"] - 867, tuple(w["row"][c] for c in H.COORD))
        if key[1] not in G[key[0]]:
            bad.append(dict(cell=cellstr(K), error="row not in the row space"))
            continue
        R.apply(U - {K})
        ok, req, b = closed(G[key[0]][key[1]])
        if ok:
            bad.append(dict(cell=cellstr(K), error="witness row still closed",
                            required=req, bounds=b))

    # ---------- phase 11/12: what the eight existing certificates buy
    DONE = done_cells()
    R.apply(DONE)
    open_now = [k for k in EX if not closed(G[k[0]][k[1]])[0]]
    R.apply(set())
    open_zero = [k for k in EX if not closed(G[k[0]][k[1]])[0]]
    piece_facts = [c for c in json.loads(
        (ROOT / "r165" / "certs" / "row_closure_graph_165.json").read_text()
    )["essential_cells"]
        if len(c.split("|")) == 4]
    bridged = sorted(c for c in piece_facts
                     if (parse(c)[0], parse(c)[1], 0, 0, 0, 0) in DONE)
    free = sorted(c for c in piece_facts
                  if (parse(c)[0], parse(c)[1], 0, 0) in R.keep_piece
                  and parse(c) not in R.keep_piece)

    # ---------- phase 10: the economics of each bridge group
    pn = {(r["b"], r["d"], r["fp"], r["lp"]): r.get("nodes", 0)
          for r in json.loads((CERTS / "verify_piece_c152.json").read_text())
          ["rows"] if r["status"] in GOOD}
    cn = {parse(r["cell"]): r.get("nodes", 0)
          for r in json.loads((CERTS / "verify_all_c152.json").read_text())
          ["rows"] if r["status"] in GOOD}
    grp = defaultdict(list)
    for c in piece_facts:
        grp[parse(c)[:2]].append(c)
    econ = {}
    for bd, members in sorted(grp.items()):
        K = (bd[0], bd[1], 0, 0, 0, 0)
        chain_cost = cn.get(K) or pn.get((bd[0], bd[1], 0, 0))
        econ[cellstr(K)] = dict(
            piece_facts=sorted(members), covered=len(members),
            chain_certificate_nodes=chain_cost,
            piece_facts_nodes=sum(pn.get(parse(c), 0) for c in members),
            piece_facts_nodes_shared_tree=max(
                [pn.get(parse(c), 0) for c in members] or [0]),
            in_the_optimum=K in OPT,
            already_free_no_certificate_needed=(K not in OPT and K not in U))
    # the cells the census consults but that need no certificate
    tail = sorted(econ.items(),
                  key=lambda kv: -(kv[1]["chain_certificate_nodes"] or 0))[:6]

    out = dict(
        inputs={p: sha(p) for p in
                ("r167/certs/row_optimum_167.json",
                 "r166/certs/verification_166.json",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json",
                 "r165/certs/row_closure_graph_165.json",
                 "r163/src/hidden163.py") + BATCHES},
        claim=("the minimum set of direct chain EXTREE certificates that "
               "restores strict closure of every exposed census row has "
               "exactly 190 members, and it is unique"),
        rules=dict(
            BRIDGE_LE="cap_piece(b,d,fp,lp) <= cap_chain(b,d,0,0,0,0)",
            BRIDGE_EQ="cap_piece(b,d,0,0) = cap_chain(b,d,0,0,0,0)",
            source="round 166 walk-set argument, not numerical agreement",
            fallback_chain="120 + a + bb + e", fallback_piece="120"),
        exposed_rows=dict(count=len(EX), matches_the_solver=len(EX)
                          == src["exposed_rows"]),
        upper_bound=dict(granted=len(OPT), rows_left_open=len(still),
                         ok=not still),
        lower_bound=dict(checked=len(OPT), failures=bad, ok=not bad,
                         single_row_evaluations=len(OPT),
                         cheaper_than_the_solver_by=round(
                             (len(U) * len(EX)) / max(len(OPT), 1), 1)),
        weighted_variants=dict(
            minimum_cardinality=len(OPT), minimum_node_cost=len(OPT),
            minimum_storage_cost=len(OPT),
            argument="the optimum is contained in every feasible set, so it "
                     "minimises every monotone cost function at once"),
        progress=dict(
            DIRECT_SECOND_ROUTE=sorted(cellstr(K) for K in DONE & OPT),
            DIRECT_SECOND_ROUTE_count=len(DONE & OPT),
            certified_cells_outside_the_optimum=sorted(
                cellstr(K) for K in DONE - OPT),
            BRIDGE_DERIVED_piece_facts=len(bridged),
            OTHER_DERIVED_piece_facts_free_from_retained_cells=len(free),
            exposed_rows_closed_by_current_certificates=len(EX) - len(open_now),
            exposed_rows_still_open=len(open_now),
            exposed_rows_open_with_nothing_granted=len(open_zero),
            remaining_certificates=len(OPT - DONE)),
        bridge_group_economics=dict(
            groups=len(econ), detail=econ,
            caveat="the round-152 piece search reports one node count per "
                   "(b,d,fp,lp) row, but for 20 of the 55 (b,d) groups the "
                   "four masks share an identical count because the mask only "
                   "changes ACCEPTANCE, not the search tree.  So the naive sum "
                   "over masks overstates what a mask-aware implementation "
                   "would pay; both figures are given.",
            piece_side_nodes_naive_sum=sum(
                v["piece_facts_nodes"] for v in econ.values()),
            piece_side_nodes_shared_tree=sum(
                v["piece_facts_nodes_shared_tree"] for v in econ.values()),
            chain_side_nodes=sum(v["chain_certificate_nodes"] or 0
                                 for v in econ.values()),
            most_expensive=[dict(cell=k, **v) for k, v in tail]),
    )
    out["ok"] = (out["exposed_rows"]["matches_the_solver"]
                 and out["upper_bound"]["ok"] and out["lower_bound"]["ok"])
    (ROOT / "r167" / "certs" / "optimality_certificate_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = {k: v for k, v in out.items() if k != "inputs"}
    show["bridge_group_economics"] = {
        k: v for k, v in show["bridge_group_economics"].items()
        if k != "detail"}
    print(json.dumps(show, ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
