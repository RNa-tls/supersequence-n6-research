#!/usr/bin/env python3
"""Round 147 Phase 10 -- classify the surviving rows.

For every row that is not STRICTLY_CLOSED, derive the exact data the residual
hard core needs, and cluster the survivors into structural classes.  Nothing
here is assumed about Q1/Q2: the corrected computation is authoritative, so the
survivor list is whatever rows_eval147 produced.

Per survivor:
    resource vector      (k, Z, H, B*, G, g, c, d, D2, Qs, h)
    required ports       120 + G - 5c
    decomposition        d+1 nonpure components, c pure circuits, 2g shared
                         repeats, K = G+1-2g beta components
    budgets              a <= D2, bb <= Qs, e <= max(0,Z-Qs), a+bb+e <= 2g
    hexagon reuse        R_int, bounded by D2+Qs <= R_int <= 2g
    orbit budget         tokens B*-s, deficit 5k-G+5s
    pure circuits        c full tau-orbits, each meeting five hexagons, whose
                         hexagons must cover the 120 - (ports of the chain part)
                         hexagons the chains do not use when the incidence bound
                         is tight
Structural class key: (required, d, c, g, h, D2, Qs, Z, b_sum, D_sum) -- the data
that determines the residual search, with k/H/B* folded in through those.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R147 / "src"))
import rows147                                                      # noqa: E402

COORD = rows147.COORD


def describe(r):
    G, g, c, d = r["G"], r["g"], r["c"], r["d"]
    tot = 2 * g
    return dict(
        resource={k: r[k] for k in COORD},
        required=120 + G - 5 * c,
        K=G + 1 - 2 * g,
        components=dict(nonpure=d + 1, pure_circuits=c, shared_repeats=tot),
        budgets=dict(a_max=min(r["D2"], tot), bb_max=min(r["Qs"], tot),
                     e_max=min(max(0, r["Z"] - r["Qs"]), tot),
                     sum_max=tot, heavy_max=r["h"]),
        hexagon_reuse=dict(lower=r["D2"] + r["Qs"], upper=tot),
        orbit=dict(tokens=r["b_sum"], deficit=r["D_sum"], s=r["s"]),
        pure_circuit_requirement=dict(
            circuits=c, hexagons_per_circuit=5,
            hexagons_to_cover=120 - (120 + G - 5 * c) + 5 * c - 0
            if False else None),
        chain_count=d + 1 + r["h"])


def main(argv):
    ev = json.loads((R147 / "rows" / "rows_eval_147.json").read_text())
    out = {"layers": {}}
    for t in (3, 4):
        key = f"L{867 + t}"
        surv = ev.get(f"{key}_survivors")
        if surv is None:
            continue
        rowsbyc = {}
        for r in rows147.rows(t):
            rowsbyc.setdefault(tuple(r[c] for c in COORD), []).append(r)
        items = []
        for s in surv:
            gk = tuple(s[c] for c in COORD)
            variants = rowsbyc.get(gk, [])
            items.append(dict(verdict=s["verdict"], bounds=s.get("bounds"),
                              required=s.get("required"),
                              detail=[describe(r) for r in variants]))
        cls = Counter()
        for s in surv:
            cls[(s.get("required"), s["d"], s["c"], s["g"], s["h"], s["D2"],
                 s["Qs"], s["Z"])] += 1
        out["layers"][key] = dict(
            survivors=len(surv),
            by_verdict=dict(Counter(s["verdict"] for s in surv)),
            structural_classes=len(cls),
            classes=[dict(zip(("required", "d", "c", "g", "h", "D2", "Qs", "Z"),
                              k)) | {"rows": v}
                     for k, v in sorted(cls.items(), key=lambda x: -x[1])][:40],
        )
        out[f"{key}_detail"] = items[:80]
        print(f"{key}: survivors={len(surv)} "
              f"verdicts={json.dumps(dict(Counter(s['verdict'] for s in surv)))} "
              f"structural_classes={len(cls)}", flush=True)
    (R147 / "rows" / "survivors_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
