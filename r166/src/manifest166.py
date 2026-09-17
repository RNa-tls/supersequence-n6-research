#!/usr/bin/env python3
"""Round 166 phase 11 -- certificate manifest and compression measurement.

Compression is deterministic (gzip with mtime = 0) and is NOT part of the
trust base: the verifier decompresses to the canonical text and checks that.
The manifest records both raw and compressed density so the storage curve is
measured rather than guessed.
"""
from __future__ import annotations
import gzip, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import routeb164 as R                                             # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

BATCHES = ["r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz"]


def main():
    g165 = json.loads((ROOT / "r165" / "certs"
                       / "row_closure_graph_165.json").read_text())
    ess = set(g165["essential_cells"])
    rows, total_nodes, total_raw, total_gz = [], 0, 0, 0
    certified = {}
    for rel in BATCHES:
        p = ROOT / rel
        if not p.exists():
            continue
        raw = p.read_bytes()
        text = gzip.decompress(raw).decode()
        refs, trees = V.parse_batch(text)
        nodes = sum(len(t[2]) for t in trees)
        for cell, capv, _ in trees:
            certified[cell] = capv
        chain_basis = [c for c, _, _ in trees
                       if "|".join(map(str, c)) in ess]
        rows.append(dict(
            path=rel, sha256=hashlib.sha256(raw).hexdigest(),
            refs=[r[1] for r in refs], trees=len(trees),
            proof_nodes=nodes, raw_bytes=len(text.encode()),
            compressed_bytes=len(raw),
            raw_bytes_per_node=round(len(text.encode()) / max(nodes, 1), 3),
            compressed_bytes_per_node=round(len(raw) / max(nodes, 1), 4),
            compression_ratio=round(len(text.encode()) / max(len(raw), 1), 1),
            chain_basis_cells=sorted(chain_basis and
                                     ["|".join(map(str, c))
                                      for c in chain_basis])))
        total_nodes += nodes
        total_raw += len(text.encode())
        total_gz += len(raw)

    # which piece basis cells the bridge covers from these chain cells
    piece_basis = [c for c in ess if g165["ablation"][c]["model"] == "piece"]
    have = {"|".join(map(str, c)) for c in certified}
    bridged = sorted(c for c in piece_basis
                     if "|".join(map(str, (int(c.split("|")[0]),
                                           int(c.split("|")[1]),
                                           0, 0, 0, 0))) in have)
    chain_basis_done = sorted(c for c in ess
                              if g165["ablation"][c]["model"] == "chain"
                              and c in have)
    out = dict(
        batches=rows,
        totals=dict(batches=len(rows), cells=len(certified),
                    proof_nodes=total_nodes, raw_bytes=total_raw,
                    compressed_bytes=total_gz,
                    raw_bytes_per_node=round(total_raw / max(total_nodes, 1), 3),
                    compressed_bytes_per_node=round(
                        total_gz / max(total_nodes, 1), 4),
                    compression_ratio=round(total_raw / max(total_gz, 1), 1)),
        basis_coverage=dict(
            chain_certified=chain_basis_done,
            chain_certified_count=len(chain_basis_done),
            piece_certified_via_bridge=bridged,
            piece_certified_count=len(bridged),
            total=len(chain_basis_done) + len(bridged),
            basis_total=288,
            remaining=288 - len(chain_basis_done) - len(bridged)),
        compression_note="gzip with mtime = 0, so the container is "
                         "byte-deterministic; the verifier decompresses to the "
                         "canonical text and checks that, so compression is "
                         "outside the trust base",
        reference_safety=dict(
            cycles="rejected (the verifier keeps a DFS stack)",
            hash_confusion="a reference carries the predecessor's exact "
                           "sha256 and is rejected on any mismatch",
            missing_dependency="a reference to a missing file is rejected",
            substitution="redirecting a reference to another existing file "
                         "fails the hash check"),
    )
    out["ok"] = bool(rows)
    (ROOT / "r166" / "certs" / "extree_manifest_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("compression_note", "reference_safety")},
                     ensure_ascii=False, indent=1)[:2400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
