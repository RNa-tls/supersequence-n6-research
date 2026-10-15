#!/usr/bin/env python3
"""Round M -- decode an incumbent of the A-hub reduced model (hub_reduced.py, HUB_DUMP) into full
single-opening trail orders and evaluate them EXACTLY (layered shortest path over all versions and
cuts, all weights).  The phi order and gap types come from the dump; the A-bundles are placed in the
gaps (1 A for S1/F1, 2 for S2/F2, >= 3 for F3) and the rest at the two ends, every assignment of the
six A trails to the slots and every start/end split is tried.  Prints the best exact length.
usage: hub_decode.py FAMILY.json DUMP.json"""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE
import order_ils as OI

def main():
    fam = json.load(open(sys.argv[1])); dump = json.load(open(sys.argv[2]))
    layers, const = TOE.load_layers(fam)
    ev = OI.make_eval(layers, const)
    T = len(layers)
    A = [t for t in range(T) if len(layers[t]) > 100]
    gaps = {int(k): (v[0], v[1]) for k, v in dump["gaps"].items()}
    first = None
    targets = {v[0] for v in gaps.values()}
    phis = [t for t in range(T) if t not in A]
    starts = [t for t in phis if t not in targets]
    first = starts[0] if starts else phis[0]
    seq = [first]; kinds = []
    while seq[-1] in gaps and gaps[seq[-1]][0] not in seq:
        nxt, kind = gaps[seq[-1]]; kinds.append(kind); seq.append(nxt)
    need = {"D": 0, "FD": 0, "S1": 1, "F1": 1, "S2": 2, "F2": 2, "F3": 3}
    slots = [need[k] for k in kinds]
    used = sum(slots)
    print(json.dumps(dict(phi_sequence=seq, gap_kinds=kinds, A_in_gaps=used, covered=len(seq))), flush=True)
    best = None
    extra = 6 - used
    for perm in itertools.permutations(A):
        for s_front in range(extra + 1):
            order = list(perm[:s_front]); p = s_front
            for t, k in zip(seq, slots + [0]):
                order.append(t)
                if k: order += list(perm[p:p + k]); p += k
            order += list(perm[p:])
            if len(order) != T or sorted(order) != list(range(T)): continue
            v = ev(order)
            if best is None or v < best[0]: best = (v, order)
    v, pth = TOE.evaluate(layers, const, best[1], True)
    print(json.dumps(dict(reduced_objective=dump["obj"], best_exact=best[0], J=best[0] - 46085, measured=TOE.build(fam, pth),
                          order=best[1])), flush=True)

if __name__ == "__main__":
    main()
