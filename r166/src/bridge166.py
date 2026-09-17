#!/usr/bin/env python3
"""Round 166 -- the CROSS-MODEL bridge: a piece cell is a chain cell.

    LEMMA.  For all b, d, fp, lp:   cap_piece(b, d, fp, lp) <= cap_chain(b, d, 0, 0, 0, 0).

    PROOF.  Take a legal piece walk for (b, d, fp, lp) and read it as a chain
    walk in the cell (b, d, 0, 0, 0, 0).

      * Moves.  A piece walk uses only the clean-E target and the five paid
        targets of its current port.  Both are catalogue moves of the chain
        model, so every step is legal there.
      * The zero budgets bind nothing extra.  With a = bb = 0 no dirty A or B
        move is available; with h = 0 no heavy move is (a heavy move costs at
        least 1); and with e = 0 no arrival may land on an already-used
        hexagon, which is exactly the piece model's fresh-hexagon rule.  So
        the chain model at (b, d, 0, 0, 0, 0) admits EXACTLY the moves the
        piece model admits.
      * Resources.  Tokens are charged identically (a non-clean-E move into an
        already-opened orbit costs one) and the deficit recursion is the same
        (+4 on a fresh orbit, -1 otherwise), so the piece walk's token and
        deficit use is unchanged when read as a chain walk.
      * Acceptance.  The piece model additionally demands a partial first or
        last block when fp or lp is set.  That is a RESTRICTION, so it only
        removes walks.

    Hence every walk counted by cap_piece is counted by cap_chain, and the
    inequality follows.  Equality holds when fp = lp = 0.                    []

This matters because the census reads piece capacities as UPPER bounds, so a
certified chain value at (b, d, 0, 0, 0, 0) may stand in for the piece value
at all four masks.  One chain certificate covers up to four piece cells.

Round 165's domination analysis never tested this: it compared chain cells to
chain cells and piece cells to piece cells only.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
import hidden163 as H                                             # noqa: E402
import routeb164 as R                                             # noqa: E402
import closure165 as CL                                           # noqa: E402

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def move_set_check():
    """The models admit the same moves at a = bb = e = h = 0 -- checked."""
    same = diff = 0
    for v in range(R.N):
        piece_targets = {R.FREE[v]} | set(R.PAID[v])
        chain_targets = set()
        for t, kind, cost in R.MOVES[v]:
            if kind in ("A", "B"):
                continue           # amax = bmax = 0
            if kind == "H":
                continue           # every heavy move costs >= 1 > hmax = 0
            chain_targets.add(t)
        if piece_targets == chain_targets:
            same += 1
        else:
            diff += 1
    return dict(sources=R.N, move_sets_identical=same, differing=diff,
                ok=diff == 0)


def witness_check():
    """Every stored piece witness must also replay as a chain walk."""
    pc, _ = R.parse_pcert(CERTS / "pcert_all_152.txt")
    ok = bad = 0
    fails = []
    for cell, rec in pc.items():
        w = rec["ports"]
        if not w:
            continue
        b, d, fp, lp = cell
        g1, _ = R.replay_piece_witness(cell, w)
        g2, i2 = R.replay_chain_witness((b, d, 0, 0, 0, 0), w)
        if g1 and g2:
            ok += 1
        else:
            bad += 1
            fails.append(dict(cell="|".join(map(str, cell)),
                              piece_ok=bool(g1), chain_ok=bool(g2),
                              detail=str(i2)[:90]))
    return dict(witnesses=ok + bad, both_legal=ok, failures=bad,
                examples=fails[:4], ok=bad == 0)


def value_check():
    """No certified pair may contradict the lemma."""
    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    pC = json.loads((CERTS / "verify_piece_c152.json").read_text())
    chain = {tuple(int(x) for x in r["cell"].split("|")): r["cap"]
             for r in vC["rows"] if r["status"] in GOOD}
    piece = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"]
             for r in pC["rows"] if r["status"] in GOOD}
    cmp_ = viol = miss = 0
    eq = 0
    for k, cp in piece.items():
        kk = (k[0], k[1], 0, 0, 0, 0)
        if kk not in chain:
            miss += 1
            continue
        if cp < 0:
            continue               # -1 means the mask is unreachable
        cmp_ += 1
        if cp > chain[kk]:
            viol += 1
        if k[2] == 0 and k[3] == 0 and cp == chain[kk]:
            eq += 1
    return dict(pairs_compared=cmp_, violations=viol,
                no_chain_counterpart=miss,
                equal_when_mask_is_trivial=eq, ok=viol == 0)


def coverage_and_census():
    g = json.loads((ROOT / "r165" / "certs"
                    / "row_closure_graph_165.json").read_text())
    ess = set(g["essential_cells"])
    pi = [c for c in ess if g["ablation"][c]["model"] == "piece"]
    vP = json.loads((CERTS / "verify_subset_152.json").read_text())
    dual = {tuple(int(x) for x in r["cell"].split("|"))
            for r in vP["rows"] if r["status"] in GOOD}
    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    allchain = {tuple(int(x) for x in r["cell"].split("|")): r["cap"]
                for r in vC["rows"] if r["status"] in GOOD}
    covered, need, nocell = [], Counter(), []
    for c in pi:
        b, d, fp, lp = (int(x) for x in c.split("|"))
        k = (b, d, 0, 0, 0, 0)
        if k not in allchain:
            nocell.append(c)
        elif k in dual:
            covered.append(c)
        else:
            need["|".join(map(str, k))] += 1
    return dict(
        piece_basis_cells=len(pi),
        covered_by_an_already_dual_certified_chain_cell=len(covered),
        covered_cells=sorted(covered),
        chain_cells_that_would_cover_the_rest=len(need),
        piece_cells_those_would_cover=sum(need.values()),
        leverage=round(sum(need.values()) / max(len(need), 1), 2),
        chain_cells_needed=sorted(need),
        piece_basis_cells_with_no_chain_counterpart=len(nocell),
        no_counterpart_cells=sorted(nocell))


def main():
    mv = move_set_check()
    wt = witness_check()
    vl = value_check()
    cov = coverage_and_census()
    out = dict(
        lemma="cap_piece(b,d,fp,lp) <= cap_chain(b,d,0,0,0,0)",
        proof_sketch=__doc__.split("PROOF.")[1].split("Hence")[0].strip(),
        inputs={p: sha(p) for p in
                ("r152/certs/pcert_all_152.txt",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json",
                 "r152/certs/verify_subset_152.json",
                 "r165/certs/row_closure_graph_165.json")},
        move_set_identity=mv,
        witness_replay=wt,
        certified_value_consistency=vl,
        coverage=cov,
        why_round_165_missed_it="its domination scan compared chain cells to "
                                "chain cells and piece cells to piece cells; "
                                "it never crossed the two models",
    )
    out["ok"] = mv["ok"] and wt["ok"] and vl["ok"]
    (ROOT / "r166" / "certs" / "cross_model_bridge_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "proof_sketch")},
                     ensure_ascii=False, indent=1)[:2600])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
