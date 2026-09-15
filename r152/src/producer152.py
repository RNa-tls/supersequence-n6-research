#!/usr/bin/env python3
"""Round 152 -- the PRODUCER of capacity certificates.

The producer is UNTRUSTED.  Everything it writes is re-established from scratch
by r152/src/certify152.py:

    * the claimed value   cap(K) = C          is not taken on faith,
    * the witness         a walk with C ports is replayed move by move,
    * the exhaustion      no walk has C+1     is re-searched by the checker.

So the producer may use any heuristic it likes.  It uses the checker's own
search in find-first mode, which is the cheapest source of a witness we have;
if it ever produced a wrong witness or a wrong value the checker would say
DISAGREE rather than silently accept it.

Usage:
    producer152.py --cells r152/certs/pilot_cells_152.json \
                   --out   r152/certs/cap_cert_152.json
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checker152 as CK


def key(args):
    return "|".join(str(x) for x in args)


def produce(cells, node_cap, claimed=None, prune=None):
    # The producer prunes with whatever values it likes -- including the ones
    # it is trying to witness.  A wrong prune can only make it fail to find a
    # witness; it can never make the checker accept a bad one.
    ck = CK.Checker(prune or {}, node_cap)
    out, order = {}, []
    for args in cells:
        cell = tuple(args)
        k = key(args)
        t0 = time.time()
        # find the largest C for which a walk exists, starting from the claim
        # The producer only has to EXHIBIT a walk; proving that no longer walk
        # exists is the checker's job, so it never runs an exhaustive search.
        # It starts from the value claimed elsewhere and, if that is out of
        # reach, walks down until it finds the best walk it can.  A claim that
        # is too LOW leaves the checker reporting DISAGREE; a claim that is too
        # HIGH leaves the witness short, which the checker rejects as
        # WITNESS_BAD.  Neither can be hidden here.
        C, wit = None, None
        c = claimed.get(k) if claimed else None
        if c is None:
            c = 1
            while ck.search(cell, c) == "FOUND":
                C, wit, c = c, list(ck.trail), c + 1
        else:
            while c >= 1:
                if ck.search(cell, c) == "FOUND":
                    C, wit = c, list(ck.trail)
                    break
                c -= 1
        order.append(k)
        out[k] = dict(args=list(args), cap=C, witness=wit,
                      producer_seconds=round(time.time() - t0, 2))
        print(f"  produced {k}: cap={C} ports={len(wit) if wit else 0} "
              f"{out[k]['producer_seconds']}s", flush=True)
    return order, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-text", default=None)
    ap.add_argument("--claimed", action="append", default=[],
                    help="tables whose cc values are the claims to witness")
    ap.add_argument("--prune-table", action="append", default=[],
                    help="extra production tables used ONLY as search heuristics")
    ap.add_argument("--node-cap", type=int, default=2_000_000_000)
    a = ap.parse_args()
    cells = json.load(open(a.cells))
    src_claimed = a.claimed or ["r147/tables/chain_cells_147.json",
                                "r147/tables/heavy_cells_147.json"]
    claimed, prune = {}, {}
    for src in src_claimed + a.prune_table:
        if not (src and Path(src).exists()):
            continue
        tbl = json.load(open(src))
        for k, v in tbl.items():
            prune[tuple(int(x) for x in k.split("|"))] = v["cc"]
            if src in src_claimed:
                claimed[k] = v["cc"]
    order, cellmap = produce(cells, a.node_cap, claimed, prune)
    doc = dict(format="L6-CAPCERT-1", order=order, cells=cellmap)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(doc, open(a.out, "w"), indent=1, sort_keys=True)
    print(f"wrote {a.out}: {len(order)} cells")
    if a.out_text:
        write_text(doc, a.out_text)
        print(f"wrote {a.out_text}")


def write_text(doc, path):
    """The plain-text certificate both checkers read.

    L6-CAPCERT-2
    cell <b> <d> <a> <bb> <e> <h> <cap> <nports>
    <nports port indices>

    A port index is the position of the permutation in the LEXICOGRAPHIC list
    of the 720 permutations of the string "123456"; both checkers rebuild that
    list themselves, so the file carries no table of its own.
    """
    with open(path, "w") as f:
        f.write("L6-CAPCERT-2\n")
        f.write("# cell <b> <d> <a> <bb> <e> <h> <cap> <nports>, then the ports\n")
        f.write("# port index = rank of the permutation in the lexicographic\n")
        f.write("# list of the 720 permutations of \"123456\"\n")
        for k in doc["order"]:
            r = doc["cells"][k]
            w = r["witness"]
            f.write("cell " + " ".join(str(x) for x in r["args"]) +
                    f" {r['cap']} {len(w)}\n")
            f.write(" ".join(str(x) for x in w) + "\n")


if __name__ == "__main__":
    main()
