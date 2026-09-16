#!/usr/bin/env python3
"""Round 164 -- run Route B over everything the repository can actually feed it.

Three things happen here:

  (1) WITNESS REPLAY for every target cell that has one.  This proves the
      LOWER direction cap(K) >= C independently.  It is not the direction the
      census consumes, and the report says so.

  (2) EXHAUSTION-TREE REPLAY for every cell that has a serialised tree.  This
      proves the UPPER direction cap(K) <= C with no search, which is the
      direction the census consumes.  The tree file is a PILOT of 24 cells.

  (3) QUANTIFY THE GAP: for every target with no tree, record the search node
      count the round-152 checker needed, which is the size of the proof
      object that would have to exist for Route B to reach it.
"""
from __future__ import annotations
import hashlib, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import routeb164 as R                                             # noqa: E402

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def sha(rel):
    q = ROOT / rel
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


def main():
    t0 = time.time()
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    chain_targets = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]]
    piece_targets = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"]]

    cap, cap_order = R.parse_capcert(CERTS / "cap_cert_all_152.txt")
    pc, pc_order = R.parse_pcert(CERTS / "pcert_all_152.txt")
    trees = R.parse_extree(CERTS / "extree_pilot_152.txt")
    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    pC = json.loads((CERTS / "verify_piece_c152.json").read_text())
    k6 = lambda s: tuple(int(x) for x in s.split("|"))
    statC = {k6(r["cell"]): r for r in vC["rows"]}
    pkey = lambda r: (r["b"], r["d"], r["fp"], r["lp"])
    statP = {pkey(r): r for r in pC["rows"]}

    # ---------------------------------------------- (1) witness replay
    chain_rows, piece_rows = [], []
    for cell in chain_targets:
        rec = cap[cell]
        st = statC[cell]["status"]
        row = dict(cell="|".join(map(str, cell)), cap=rec["cap"],
                   route_a_status=st, witness_ports=len(rec["ports"]))
        if rec["ports"]:
            ok, info = R.replay_chain_witness(cell, rec["ports"])
            row["lower_bound_replayed"] = bool(ok)
            row["detail"] = info if not ok else None
            row["achieved_ports"] = info.get("ports") if ok else None
            row["lower_bound_matches_cap"] = bool(
                ok and info["ports"] == rec["cap"])
        else:
            row["lower_bound_replayed"] = None      # nothing stored to replay
            row["lower_bound_matches_cap"] = None
        row["upper_bound_proof_object"] = "ABSENT"
        row["route_a_nodes"] = statC[cell].get("nodes")
        chain_rows.append(row)

    for cell in piece_targets:
        rec = pc[cell]
        st = statP[cell]["status"]
        row = dict(cell="|".join(map(str, cell)), cap=rec["cap"],
                   route_a_status=st, witness_ports=len(rec["ports"]))
        if rec["ports"]:
            ok, info = R.replay_piece_witness(cell, rec["ports"])
            row["lower_bound_replayed"] = bool(ok)
            row["detail"] = info if not ok else None
            row["lower_bound_matches_cap"] = bool(
                ok and info["ports"] == rec["cap"])
        else:
            row["lower_bound_replayed"] = None
            row["lower_bound_matches_cap"] = None
        row["upper_bound_proof_object"] = "ABSENT"
        row["route_a_nodes"] = statP[cell].get("nodes")
        piece_rows.append(row)

    # ---------------------------------------------- (2) exhaustion trees
    certified, tree_rows = {}, []
    tot_nodes = tot_hist = tot_forms = tot_subset = 0
    leafs = Counter()
    maxorb = 0
    for cell, capv, toks in trees:
        v = R.TreeVerifier(dict(certified))
        ok, info = v.validate(cell, capv, toks)
        row = dict(cell="|".join(map(str, cell)), cap=capv,
                   tokens=len(toks), nodes=v.nodes,
                   upper_bound_replayed=bool(ok),
                   detail=None if ok else info)
        if ok:
            certified[cell] = capv          # only then may (p) use it later
            w = cap.get(cell, {}).get("ports")
            if w:
                g, winfo = R.replay_chain_witness(cell, w)
                row["lower_bound_replayed"] = bool(g and winfo["ports"] == capv)
        tot_nodes += v.nodes
        tot_hist += v.hist_checks
        tot_forms += v.feas_form_checks
        tot_subset += v.feas_subset_checks
        leafs.update(v.leaf_reasons)
        maxorb = max(maxorb, v.max_open_orbits)
        tree_rows.append(row)

    # ---------------------------------------------- (3) size of the gap
    miss_chain = [r for r in chain_rows if r["upper_bound_proof_object"] == "ABSENT"]
    miss_piece = [r for r in piece_rows if r["upper_bound_proof_object"] == "ABSENT"]
    chain_nodes = [r["route_a_nodes"] for r in miss_chain if r["route_a_nodes"]]
    piece_nodes = [r["route_a_nodes"] for r in miss_piece if r["route_a_nodes"]]
    pilot_nodes = sum(r["nodes"] for r in tree_rows)
    pilot_bytes = (CERTS / "extree_pilot_152.txt").stat().st_size
    bytes_per_node = pilot_bytes / max(pilot_nodes, 1)

    out = dict(
        inputs={p: sha(p) for p in (
            "r152/certs/cap_cert_all_152.txt", "r152/certs/pcert_all_152.txt",
            "r152/certs/extree_pilot_152.txt",
            "r152/certs/verify_all_c152.json",
            "r152/certs/verify_piece_c152.json",
            "r164/certs/targets_164.json")},
        targets=dict(chain=len(chain_targets), piece=len(piece_targets),
                     total=len(chain_targets) + len(piece_targets)),
        lower_bounds=dict(
            chain_with_a_witness=sum(1 for r in chain_rows
                                     if r["witness_ports"]),
            chain_replayed=sum(1 for r in chain_rows
                               if r["lower_bound_matches_cap"]),
            chain_failed=[r["cell"] for r in chain_rows
                          if r["lower_bound_replayed"] is False],
            chain_no_witness=sum(1 for r in chain_rows
                                 if not r["witness_ports"]),
            piece_with_a_witness=sum(1 for r in piece_rows
                                     if r["witness_ports"]),
            piece_replayed=sum(1 for r in piece_rows
                               if r["lower_bound_matches_cap"]),
            piece_failed=[r["cell"] for r in piece_rows
                          if r["lower_bound_replayed"] is False],
            piece_no_witness=sum(1 for r in piece_rows
                                 if not r["witness_ports"])),
        upper_bounds=dict(
            targets_with_a_proof_object=0,
            targets_replay_certified=0,
            note="no target cell has a serialised exhaustion tree, so Route B "
                 "cannot establish the direction the census consumes for any "
                 "of them"),
        exhaustion_trees=dict(
            cells=len(tree_rows),
            all_valid=all(r["upper_bound_replayed"] for r in tree_rows),
            exact=sum(1 for r in tree_rows
                      if r.get("lower_bound_replayed")),
            proof_nodes_replayed=tot_nodes,
            histogram_assertions=tot_hist,
            feas_form_checks=tot_forms,
            feas_subset_checks=tot_subset,
            histogram_discrepancies=0 if all(
                r["upper_bound_replayed"] for r in tree_rows) else None,
            max_open_orbits=maxorb,
            leaf_justifications=dict(leafs),
            rows=tree_rows),
        gap=dict(
            chain_targets_without_a_tree=len(miss_chain),
            piece_targets_without_a_tree=len(miss_piece),
            route_a_nodes_for_those_chain_cells=sum(chain_nodes),
            route_a_nodes_for_those_piece_cells=sum(piece_nodes),
            largest_single_chain_cell_nodes=max(chain_nodes) if chain_nodes else 0,
            largest_single_piece_cell_nodes=max(piece_nodes) if piece_nodes else 0,
            pilot_tree_nodes=pilot_nodes, pilot_tree_bytes=pilot_bytes,
            bytes_per_proof_node=round(bytes_per_node, 2),
            projected_bytes_if_serialised=int(
                (sum(chain_nodes) + sum(piece_nodes)) * bytes_per_node),
            note="the projection uses the pilot's bytes-per-node; it is an "
                 "order-of-magnitude statement, not a measurement"),
        chain_rows=chain_rows, piece_rows=piece_rows,
    )
    lb = out["lower_bounds"]
    out["ok"] = (not lb["chain_failed"] and not lb["piece_failed"]
                 and lb["chain_replayed"] == lb["chain_with_a_witness"]
                 and lb["piece_replayed"] == lb["piece_with_a_witness"]
                 and out["exhaustion_trees"]["all_valid"])
    (ROOT / "r164" / "certs" / "route_b_replay_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    brief = {k: v for k, v in out.items()
             if k not in ("chain_rows", "piece_rows", "inputs")}
    brief["exhaustion_trees"] = {k: v for k, v
                                 in out["exhaustion_trees"].items()
                                 if k != "rows"}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
