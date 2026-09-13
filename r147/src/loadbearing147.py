#!/usr/bin/env python3
"""Round 147 Phase 6/13 -- which cells are LOAD-BEARING, and which envelope
inequality does the work.

A cell is load-bearing when some coordinate row's closure actually reads it:
the row is STRICTLY_CLOSED, the model that closes it is the split or merged
chain model, and the cell appears in the budget split that attains that model's
bound.  Those are the cells Phase 6 must verify with the second implementation.

For the same rows this also records the envelope attribution (Phase 13): which
of
        a <= D2,   bb <= Qs,   e <= max(0, Z - Qs),   a + bb + e <= 2g
is active at the attaining split, so no closure rests on an ambiguous shared
charge.  A budget that is capped by two of the inequalities at once is reported
with both, and the caps are recorded as numbers so the reader can check which
one is tight rather than trusting a label.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
ROOT = R147.parent
sys.path.insert(0, str(R147 / "src"))
sys.path.insert(0, str(ROOT / "src"))
import rows147                                                      # noqa: E402
import rows_eval147 as EV                                           # noqa: E402

COORD = rows147.COORD


def attaining_split(r):
    """Re-run the envelope maximisation, remembering the argmax split."""
    nch = r["d"] + 1 + r["h"]
    tot = 2 * r["g"]
    caps = dict(a=min(r["D2"], tot), bb=min(r["Qs"], tot),
                e=min(max(0, r["Z"] - r["Qs"]), tot), total=tot)
    best = (None, None)

    def go(n, b, D, a, bb, e, t, acc, used):
        nonlocal best
        if n == 0:
            if b == 0 and D == 0 and (best[0] is None or acc > best[0]):
                best = (acc, list(used))
            return
        for xa in range(min(a, t) + 1):
            for xbb in range(min(bb, t - xa) + 1):
                for xe in range(min(e, t - xa - xbb) + 1):
                    for xb in range(b + 1):
                        for xd in range(D + 1):
                            if n == 1 and (xb != b or xd != D):
                                continue
                            v, _ = EV.CC(xb, xd, xa, xbb, xe)
                            go(n - 1, b - xb, D - xd, a - xa, bb - xbb,
                               e - xe, t - xa - xbb - xe, acc + v,
                               used + [(xb, xd, xa, xbb, xe)])

    go(nch, r["b_sum"], r["D_sum"], caps["a"], caps["bb"], caps["e"], tot, 0, [])
    return best[0], best[1], caps


def main():
    EV.load_cells()
    EV.PIECE.load_caps()
    ev = json.loads((R147 / "rows" / "rows_eval_147.json").read_text())
    cells, attrib = {}, []
    for t in (3, 4):
        key = f"L{867 + t}"
        if key not in ev.get("layers", {}):
            continue
        groups = {}
        for r in rows147.rows(t):
            groups.setdefault(tuple(r[c] for c in COORD), []).append(r)
        for gk, variants in sorted(groups.items()):
            EV._split.cache_clear()
            res = EV.classify(variants)
            if res["verdict"] != "STRICTLY_CLOSED" or res["closed_by"] == "piece":
                continue
            for r in variants:
                nch = r["d"] + 1 + r["h"]
                if nch == 1 and r["s"] != 0:
                    continue
                v, _ = EV.split_bound(r)
                if v != res["bound"]:
                    continue
                acc, split, caps = attaining_split(r)
                if acc != v or split is None:
                    continue
                use = [sum(p[i] for p in split) for i in (2, 3, 4)]
                active = []
                if use[0] == caps["a"] and caps["a"] > 0:
                    active.append(f"a = D2 = {caps['a']}")
                if use[1] == caps["bb"] and caps["bb"] > 0:
                    active.append(f"bb = Qs = {caps['bb']}")
                if use[2] == caps["e"] and caps["e"] > 0:
                    active.append(f"e = Z-Qs = {caps['e']}")
                if sum(use) == caps["total"] and caps["total"] > 0:
                    active.append(f"a+bb+e = 2g = {caps['total']}")
                if not active:
                    active.append("no envelope cap is tight (budgets unused)")
                attrib.append(dict(zip(COORD, gk)) |
                              dict(s=r["s"], required=res["required"],
                                   bound=v, closed_by=res["closed_by"],
                                   chains=nch, split=split, caps=caps,
                                   used=use, active_inequalities=active))
                for p in split:
                    cells["|".join(map(str, tuple(p) + (0,)))] = True
                break
    out = dict(load_bearing_cells=sorted(cells),
               load_bearing_cell_count=len(cells),
               rows_attributed=len(attrib), attribution=attrib[:400])
    (R147 / "certs" / "loadbearing_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("attribution", "load_bearing_cells")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
