#!/usr/bin/env python3
"""L6 endgame — row evaluation on the COUPLED CHAIN model.

Instead of pricing the hex-simple pieces separately and re-imposing the
companion-hexagon lemma by hand, this evaluator prices a whole nonpure beta
COMPONENT at once: the retained type A (sigma) and type B (sigma^2) dirty
edges stay inside the object and are the only edges permitted to land in an
already visited hexagon.  The companion lemma is then a consequence of literal
hexagon occupancy rather than an extra hypothesis, and the freedom that the
piece model double-counted (each piece choosing its own first port) is gone.

Budgets for one arithmetic row (all derived in RR_ROUND142_REPEAT_DOMAIN_OUTER
and re-checked in this round):

    number of chains      = d + 1 + h
    sum of chain deficits = 5k - G + 5s
    sum of chain tokens   = B* - s
    sum of retained A     = D2        (an A edge spent opening a cycle only
    sum of retained B     = Qs         removes freedom, so the maximum is here)
    required ports        = 120 + G - 5c

`CC(b, D, a, bb)` comes from `outputs/l6chain_144.exe`; unknown cells fall back
to the hexagon count 120, which keeps every verdict sound.
"""
from __future__ import annotations
import json, subprocess, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "outputs" / "l6chain_144.exe"
CACHE = ROOT / "outputs" / "rr_l6_chain_capacity_144.json"
UB = ROOT / "outputs" / "rr_l6_chain_ub_144.txt"
HEXCAP = 120
NEG = -10 ** 9

sys.path.insert(0, str(ROOT / "src"))
from l6_coupled_144 import rows_for                              # noqa: E402

_C: dict = {}
REQUESTED: set = set()


def load_cache():
    global _C
    _C = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    return _C


def write_ub():
    """Every proved chain cell is a sound suffix bound for deeper searches."""
    lines = []
    for key, rec in _C.items():
        if rec.get("capped"):
            continue
        b, d, a, bb = (int(x) for x in key.split("|"))
        lines.append(f"{b} {d} {a + bb} {rec['cc']}")
    base = ROOT / "outputs" / "rr_l6_marked_capacity_table_144.json"
    if base.exists():                      # a = 0 coincides with the piece table
        st = json.loads(base.read_text())
        for b, tab in st["tables"].items():
            for k, v in tab.items():
                dd, mask = k.split("|")
                if mask == "00" and v >= 0:
                    lines.append(f"{b} {dd} 0 {v}")
    UB.write_text("\n".join(lines) + "\n")


def compute(b, d, a, bb, node_cap=0):
    write_ub()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb),
                        str(node_cap), str(UB)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"chain cell {b},{d},{a},{bb} failed: {r.stderr[:300]}")
    c = json.loads(r.stdout)
    _C[f"{b}|{d}|{a}|{bb}"] = dict(cc=c["cc"], nodes=c["nodes"],
                                   capped=c["capped"], seconds=c["seconds"])
    CACHE.write_text(json.dumps(_C, ensure_ascii=False, indent=1))
    return _C[f"{b}|{d}|{a}|{bb}"]


def CC(b, d, a, bb):
    """Chain capacity; HEXCAP for cells not yet proved (sound over-bound)."""
    if min(b, d, a, bb) < 0:
        return None
    rec = _C.get(f"{b}|{d}|{a}|{bb}")
    if rec is None or rec.get("capped"):
        REQUESTED.add((b, d, a, bb))
        return HEXCAP
    return rec["cc"]


def row_bound(r):
    nch = r["d"] + 1 + r["h"]
    Dtot, btot, atot, bbtot = r["D_sum"], r["b_sum"], r["D2"], r["Qs"]
    fallback = [False]

    @lru_cache(maxsize=None)
    def go(i, b, d, a, bb):
        if i == nch - 1:
            v = CC(b, d, a, bb)
            if v == HEXCAP:
                fallback[0] = True
            return v
        best = NEG
        for xb in range(b + 1):
            for xd in range(d + 1):
                for xa in range(a + 1):
                    for xbb in range(bb + 1):
                        v = CC(xb, xd, xa, xbb)
                        if v == HEXCAP:
                            fallback[0] = True
                        t = v + go(i + 1, b - xb, d - xd, a - xa, bb - xbb)
                        if t > best:
                            best = t
        return best

    v = go(0, btot, Dtot, atot, bbtot)
    go.cache_clear()
    return v, nch, fallback[0]


def run(t, use_sigma_deficit=False):
    rows = rows_for(t, use_sigma_deficit)
    strict, surv, fb = 0, 0, 0
    surviving = []
    for r in rows:
        v, nch, used_fb = row_bound(r)
        r["chains"] = nch
        r["chain_bound"] = v
        if v < r["required"]:
            r["verdict"] = "STRICT"
            strict += 1
        else:
            r["verdict"] = "EQUALITY" if v == r["required"] else "OPEN"
            surv += 1
            surviving.append(r)
            if used_fb:
                fb += 1
    return dict(t=t, L=867 + t, rows=len(rows), strict=strict, surviving=surv,
                surviving_using_fallback=fb, surviving_rows=surviving)


if __name__ == "__main__":
    load_cache()
    out = {}
    for t in [int(x) for x in (sys.argv[1:] or ["3"])]:
        res = run(t)
        out[f"L{867 + t}"] = {k: v for k, v in res.items() if k != "surviving_rows"}
        out[f"L{867 + t}_surviving"] = res["surviving_rows"][:80]
        print(f"L{867 + t}", json.dumps(out[f"L{867 + t}"]))
    need = sorted(REQUESTED)
    out["cells_requested_but_unproved"] = [list(x) for x in need]
    (ROOT / "outputs" / "rr_l6_chain_rows_144.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("unproved cells requested:", len(need))
    for x in need[:40]:
        print("   b=%d D=%d a=%d bb=%d" % x)
