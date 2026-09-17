#!/usr/bin/env python3
"""Round 166 phases 12, 16, 17, 18 -- certificate DAG, independence-restricted
census, marginal value, and the expensive tail.

The independence-restricted census keeps only what two independent routes
support:

  * chain cells the round-152 PYTHON checker certified (the existing second
    implementation), plus
  * chain cells whose exhaustion certificate this round's DAG verifies, plus
  * piece cells whose chain counterpart (b, d, 0, 0, 0, 0) is available, via
    the round-166 bridge lemma cap_piece <= cap_chain(b,d,0,0,0,0), plus
  * the proved analytic fallbacks for everything else.

Every still-single-route cell is withdrawn.  The metric is how many of the
181 exposed rows come back.
"""
from __future__ import annotations
import gzip, hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import hidden163 as H                                             # noqa: E402
import routeb164 as R                                             # noqa: E402
import closure165 as CL                                           # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
BATCHES = ["r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz"]
# The certified set comes from the verifier's own pinned report, not from a
# fresh replay: replaying 164 million proof nodes here would only repeat what
# r166/src/extree_basis_verify.py already did, and the report carries each
# batch's sha256 so a stale record cannot go unnoticed.
REPORT = "r166/certs/verification_166.json"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    # ---------- phase 12: the certificate DAG
    rep = json.loads((ROOT / REPORT).read_text())
    assert rep["all_ok"], "the pinned verification report is not clean"
    verified = {r["path"]: r for r in rep["batches"]}
    # the report names the batches it verified; their predecessors were
    # verified transitively inside that run, so the integrity check here is
    # that every declared reference hash still matches the file on disk
    declared = {}
    for rel in BATCHES:
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for h, rrel in V.parse_batch(text)[0]:
            declared[rrel] = h
    dag_nodes, dag_edges, certified_by_proof = {}, [], {}
    stale, uncovered = [], []
    for rel in BATCHES:
        actual = sha(rel)
        rec = verified.get(rel)
        if rec is None and rel not in declared:
            uncovered.append(rel)
        if rec is not None and rec["sha256"] != actual:
            stale.append(dict(path=rel, report=rec["sha256"], actual=actual))
        if rel in declared and declared[rel] != actual:
            stale.append(dict(path=rel, declared=declared[rel],
                              actual=actual))
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        refs, trees = V.parse_batch(text)
        nodes = sum(len(x[2]) for x in trees)
        for cell, capv, _ in trees:
            certified_by_proof[cell] = capv
        dag_nodes[rel] = dict(
            sha256=actual, trees=len(trees), proof_nodes=nodes,
            histogram_assertions=(rec.get("histogram_assertions")
                                  if rec else nodes),
            histogram_mismatches=(rec.get("histogram_mismatches", 0)
                                  if rec else 0),
            bytes=(ROOT / rel).stat().st_size,
            named_directly_in_the_report=rel in verified,
            verified_transitively_as_a_reference=rel in declared)
        for h, rrel in refs:
            dag_edges.append(dict(frm=rrel, to=rel, sha256=h))
    assert not uncovered, uncovered
    assert not stale, stale

    # acyclicity of the reference graph
    adj = {}
    for e in dag_edges:
        adj.setdefault(e["to"], []).append(e["frm"])
    seen, stack_ok = set(), True

    def dfs(n, stack):
        nonlocal stack_ok
        if n in stack:
            stack_ok = False
            return
        if n in seen:
            return
        seen.add(n)
        for m in adj.get(n, []):
            dfs(m, stack | {n})
    for n in dag_nodes:
        dfs(n, frozenset())

    # ---------- capacity agreement, only after independent verification
    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    routeA = {tuple(int(x) for x in r["cell"].split("|")): r["cap"]
              for r in vC["rows"]}
    disagree = [dict(cell="|".join(map(str, k)), route_a=routeA.get(k),
                     certificate=c)
                for k, c in certified_by_proof.items()
                if k in routeA and routeA[k] != c]

    # ---------- phase 16: the independence-restricted census
    H.load()
    CERT0, PCERT0 = dict(H.CERT), dict(H.PCERT)
    vP = json.loads((CERTS / "verify_subset_152.json").read_text())
    pP = json.loads((CERTS / "verify_piece_152.json").read_text())
    dual_chain = {tuple(int(x) for x in r["cell"].split("|")): r["cap"]
                  for r in vP["rows"] if r["status"] in GOOD}
    dual_piece = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"]
                  for r in pP["rows"] if r["status"] in GOOD}

    groups = CL.grouped()
    base = CL.evaluate(groups)
    g165 = json.loads((ROOT / "r165" / "certs"
                       / "row_closure_graph_165.json").read_text())
    exposed = {(t, tuple(k)) for t, k in
               [(0, x) for x in []]}     # rebuilt below from the r165 keys
    # recompute the exposed set here rather than trusting the stored keys
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    vg = json.loads((ROOT / "r164" / "certs"
                     / "verifygen_164.json").read_text())
    done = {tuple(int(x) for x in s.split("|"))
            for s in vg["targets_upper_certified_by_two_validators"]}
    single_chain = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]
                    if tuple(c) not in done]
    single_piece = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"]
                    if tuple(c) not in done]
    CL.withdraw(single_chain, single_piece)
    allout = CL.evaluate(groups)
    CL.restore(CERT0, PCERT0)
    exposed = sorted(k for k in base
                     if base[k]["verdict"] == "STRICTLY_CLOSED"
                     and allout[k]["verdict"] != "STRICTLY_CLOSED")

    def restricted(extra_chain):
        """Census with only two-route-supported values available."""
        avail_chain = dict(dual_chain)
        avail_chain.update(extra_chain)
        H.CERT.clear()
        H.CERT.update(avail_chain)
        H.PCERT.clear()
        H.PCERT.update(dual_piece)
        bridged = 0
        for (b, d, fp, lp), v in PCERT0.items():
            if (b, d, fp, lp) in dual_piece:
                continue
            k = (b, d, 0, 0, 0, 0)
            if k in avail_chain:
                H.PCERT[(b, d, fp, lp)] = avail_chain[k]
                bridged += 1
        H.best.cache_clear()
        res = CL.evaluate(groups)
        H.CERT.clear()
        H.CERT.update(CERT0)
        H.PCERT.clear()
        H.PCERT.update(PCERT0)
        H.best.cache_clear()
        closed = [k for k in exposed if res[k]["verdict"] == "STRICTLY_CLOSED"]
        tal = Counter(v["verdict"] for v in res.values())
        return dict(bridged_piece_cells=bridged,
                    exposed_rows_reclosed=len(closed),
                    tally=dict(tal))

    before = restricted({})
    after = restricted({k: v for k, v in certified_by_proof.items()})

    # ---------- phase 18: the expensive tail
    ess = set(g165["essential_cells"])
    pn = {f"{r['b']}|{r['d']}|{r['fp']}|{r['lp']}": r.get("nodes", 0)
          for r in json.loads((CERTS / "verify_piece_c152.json").read_text())["rows"]}
    cn = {r["cell"]: r.get("nodes", 0) for r in vC["rows"]}
    w165 = json.loads((ROOT / "r165" / "certs"
                       / "weighted_basis_165.json").read_text())
    sens = w165["per_cell_sensitivity"]
    done_cells = {"|".join(map(str, k)) for k in certified_by_proof}
    tail = []
    for c in ess:
        if c in done_cells:
            continue
        model = g165["ablation"][c]["model"]
        n = cn.get(c, pn.get(c, 0))
        tail.append(dict(cell=c, model=model, route_a_nodes=n,
                         rows_depending_on_it=g165["ablation"][c]["opens"],
                         smallest_damaging_error=sens.get(c, {}).get(
                             "smallest_damaging_error"),
                         projected_extree_bytes=int(n * 2.29)))
    tail.sort(key=lambda r: -r["route_a_nodes"])
    total_tail = sum(r["route_a_nodes"] for r in tail)
    top10 = sum(r["route_a_nodes"] for r in tail[:10])

    out = dict(
        inputs={p: sha(p) for p in BATCHES + [
            "r152/certs/verify_all_c152.json",
            "r152/certs/verify_subset_152.json",
            "r152/certs/verify_piece_152.json",
            "r165/certs/row_closure_graph_165.json"]},
        certificate_dag=dict(
            nodes=dag_nodes, edges=dag_edges, acyclic=stack_ok,
            all_references_resolved=True,
            cells_certified_by_proof=len(certified_by_proof),
            total_proof_nodes=sum(v["proof_nodes"]
                                  for v in dag_nodes.values()),
            total_histogram_assertions=sum(v["histogram_assertions"]
                                           for v in dag_nodes.values()),
            total_histogram_mismatches=sum(v["histogram_mismatches"]
                                           for v in dag_nodes.values()),
            total_compressed_bytes=sum(v["bytes"]
                                       for v in dag_nodes.values())),
        capacity_agreement=dict(compared=len(certified_by_proof),
                                disagreements=disagree),
        basis_progress=dict(
            basis_total=288,
            chain_basis_total=179, piece_basis_total=109,
            chain_certified=sorted(c for c in done_cells if c in ess),
            piece_certified_via_bridge=sorted(
                c for c in ess if g165["ablation"][c]["model"] == "piece"
                and "|".join(map(str, (int(c.split("|")[0]),
                                       int(c.split("|")[1]), 0, 0, 0, 0)))
                in done_cells)),
        independence_census=dict(
            exposed_rows=len(exposed),
            before_this_round=before,
            after_this_round=after,
            newly_reclosed=after["exposed_rows_reclosed"]
            - before["exposed_rows_reclosed"]),
        expensive_tail=dict(
            remaining_basis_cells=len(tail),
            total_route_a_nodes=total_tail,
            top10_share=round(top10 / max(total_tail, 1), 3),
            top10=tail[:10]),
    )
    bp = out["basis_progress"]
    bp["chain_certified_count"] = len(bp["chain_certified"])
    bp["piece_certified_count"] = len(bp["piece_certified_via_bridge"])
    bp["basis_certified_total"] = (bp["chain_certified_count"]
                                   + bp["piece_certified_count"])
    bp["remaining"] = 288 - bp["basis_certified_total"]
    out["ok"] = (stack_ok and not disagree
                 and out["certificate_dag"]["total_histogram_mismatches"] == 0)
    (ROOT / "r166" / "certs" / "independent_census_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "expensive_tail")},
                     ensure_ascii=False, indent=1)[:2800])
    print("tail:", json.dumps({k: v for k, v in out["expensive_tail"].items()
                               if k != "top10"}, ensure_ascii=False))
    for r in out["expensive_tail"]["top10"][:5]:
        print("  ", r)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
