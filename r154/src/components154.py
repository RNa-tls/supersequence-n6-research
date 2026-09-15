#!/usr/bin/env python3
"""Round 154 Steps 2-4 -- the beta-components of real covers, with signatures.

beta is a permutation, so every beta-component is a directed cycle and there is
no other topology available.  Any classification must therefore be by the EDGE
LABELS on that cycle, not by its shape.  This file computes, for every cover the
repository actually contains, the signature of every beta-component:

    (length, sorted multiset of edge types, contains the dummy,
     number of distinct hexagons touched, number of distinct tau-orbits touched)

and reports how many distinct signatures occur.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r154" / "src"))
from beta_defs154 import build, sigma, tau, classes, splice          # noqa: E402


def geom(n):
    W, IDX = build(n)
    HEX, _ = classes(W, sigma)
    ORB, _ = classes(W, tau)
    return W, IDX, HEX, ORB


def census(W_word, n, label):
    S = splice(W_word, n)
    _, IDX, HEX, ORB = geom(n)
    rows = []
    for c in S["comps"]:
        types = []
        for q in c:
            t = S["edge_type"].get(q, ("?", None))[0]
            types.append(t)
        has_dummy = S["dummy"] in c
        words = [S["passes"][q][0] for q in c if q != S["dummy"]]
        rows.append(dict(
            length=len(c),
            types=tuple(sorted(Counter(types).items())),
            dummy=has_dummy,
            hexagons=len({HEX[IDX[w]] for w in words}),
            orbits=len({ORB[IDX[w]] for w in words}),
            pure_cleanE=(not has_dummy and all(t == "E" for t in types))))
    return dict(label=label, n=n, P=S["P"], G=S["G"], K=S["K"],
                fixed_representative=S["fixed_representative"],
                components=rows)


def main():
    covers = []
    w872 = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    covers.append((w872, 6, "n6_872_witness"))
    try:
        sys.path.insert(0, str(ROOT))
        from data import known_witnesses as KW
        for name in dir(KW):
            if name.startswith("_"):
                continue
            v = getattr(KW, name)
            if isinstance(v, str) and set(v) <= set("123456") and len(v) > 10:
                nn = len(set(v))
                covers.append((v, nn, f"known:{name}"))
    except Exception as exc:                                    # noqa: BLE001
        print("known_witnesses:", exc)
    p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
    if p5.exists():
        for i, rec in enumerate(json.loads(p5.read_text())):
            w = rec["word"] if isinstance(rec, dict) else rec
            if not isinstance(w, str):
                continue
            al = sorted(set(w))
            if len(al) != 5:
                continue
            # the file uses 0..4; the construction is alphabet-agnostic but the
            # helpers build "12345", so relabel
            m = dict(zip(al, "12345"))
            covers.append(("".join(m[ch] for ch in w), 5, f"n5_minimum_{i}"))

    out = dict(covers=[], signatures={}, errors=[])
    allsig = Counter()
    for w, n, label in covers:
        try:
            c = census(w, n, label)
        except Exception as exc:                                # noqa: BLE001
            out["errors"].append(dict(label=label, error=str(exc)))
            continue
        sig = Counter()
        for r in c["components"]:
            key = json.dumps(dict(length=r["length"], types=r["types"],
                                  dummy=r["dummy"], hexagons=r["hexagons"],
                                  orbits=r["orbits"]), sort_keys=True)
            sig[key] += 1
            allsig[key] += 1
        out["covers"].append(dict(
            label=label, n=n, P=c["P"], G=c["G"], K=c["K"],
            fixed_representative=c["fixed_representative"],
            components=len(c["components"]),
            pure_cleanE=sum(r["pure_cleanE"] for r in c["components"]),
            distinct_signatures=len(sig),
            signature_counts={k: v for k, v in sig.most_common()}))
    out["signatures"] = {k: v for k, v in allsig.most_common()}
    out["distinct_signatures_overall"] = len(allsig)
    (ROOT / "r154" / "certs" / "components_154.json").write_text(
        json.dumps(out, indent=1) + "\n")
    for c in out["covers"]:
        print(f"  {c['label']:22s} n={c['n']} P={c['P']} G={c['G']} K={c['K']} "
              f"fixedrep={c['fixed_representative']} components={c['components']}"
              f" pureE={c['pure_cleanE']} distinct signatures="
              f"{c['distinct_signatures']}")
    print("errors:", out["errors"])
    print("distinct signatures over all covers:",
          out["distinct_signatures_overall"])
    for k, v in list(allsig.most_common())[:20]:
        print(f"    x{v:3d}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
