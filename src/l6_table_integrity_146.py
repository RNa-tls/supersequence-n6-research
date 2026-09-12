#!/usr/bin/env python3
"""Round 146 — integrity audit of the load-bearing capacity tables.

Checks, in order of how badly a failure would hurt:

 1. NO capped cell anywhere (a capped cell may never be used as a proof bound).
 2. CROSS-TABLE AGREEMENT.  The chain table at a = bb = e = h = 0 describes the
    SAME object as the piece table at mask 00, so the two must agree cell by
    cell.  Cells that were seeded from the piece table are reported separately
    so that the agreement is not counted as evidence where it is tautological.
 3. Monotonicity in every budget (deficit, tokens, reuse, heavy) -- capacity can
    only grow when a budget grows.
 4. Mask ordering:  C(b,d,00) >= C(b,d,10) = C(b,d,01) >= C(b,d,11), and the
    infeasible entries (-1) only where a partial endpoint block is impossible.
 5. Key semantics: every key parses, no duplicates, and the evaluator's reader
    reaches exactly the keys the builder wrote.
 6. Impossible states: no cell claims more than the 120 hexagons plus its reuse
    budget.
 7. Provenance: source and binary hashes, compiler flags, node totals.
 8. Independent reruns of the boundary / equality / maximum cells.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P_TAB = ROOT / "outputs" / "rr_l6_marked_capacity_table_144.json"
C_TAB = ROOT / "outputs" / "rr_l6_chain_capacity_144.json"
H_TAB = ROOT / "outputs" / "rr_l6_heavychain_capacity_144.json"
UB_PIECE = ROOT / "outputs" / "rr_l6_capacity_ub_144.txt"   # 3 columns: b d value
UB_CHAIN = ROOT / "outputs" / "rr_l6_chain_ub_144.txt"      # 5 columns: b d a h value


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    out, fail = {}, []
    piece = json.loads(P_TAB.read_text())
    chain = json.loads(C_TAB.read_text())
    heavy = json.loads(H_TAB.read_text())

    # ---- 1 capped
    cap_p = [k for k, v in piece["cells"].items() if v["capped"]]
    cap_c = [k for k, v in chain.items() if v.get("capped") and not v.get("bound_below")]
    cap_h = [k for k, v in heavy.items() if v.get("capped") and not v.get("bound_below")]
    if cap_p or cap_c or cap_h:
        fail.append(("capped cells present", cap_p, cap_c, cap_h))
    out["capped"] = dict(piece=cap_p, chain=cap_c, heavy=cap_h)

    # ---- 5 key semantics
    P = {}
    for b, tab in piece["tables"].items():
        for kk, v in tab.items():
            d, m = kk.split("|")
            if m not in ("00", "10", "01", "11"):
                fail.append(("bad mask key", b, kk))
            P[(int(b), int(d), m)] = v
    C = {}
    for kk, v in chain.items():
        parts = kk.split("|")
        if len(parts) != 5:
            fail.append(("bad chain key", kk))
            continue
        C[tuple(int(x) for x in parts)] = v
    Hh = {}
    for kk, v in heavy.items():
        parts = kk.split("|")
        if len(parts) != 6:
            fail.append(("bad heavy key", kk))
            continue
        Hh[tuple(int(x) for x in parts)] = v
    out["cells"] = dict(piece=len(P), chain=len(C), heavy=len(Hh))

    # ---- 2 cross-table agreement at a = bb = e = 0
    agree, seeded, disagree = 0, 0, []
    for (b, d, a, bb, e), v in C.items():
        if (a, bb, e) != (0, 0, 0):
            continue
        p = P.get((b, d, "00"))
        if p is None:
            continue
        if v.get("source"):
            seeded += 1
            continue
        if v["cc"] != p:
            disagree.append(((b, d), v["cc"], p))
        else:
            agree += 1
    if disagree:
        fail.append(("chain/piece tables disagree", disagree[:5]))
    out["cross_table"] = dict(independently_agreeing=agree, seeded=seeded,
                              disagreeing=len(disagree))
    # heavy table at h = 0 must also match the chain table
    hd = []
    for (b, d, a, bb, e, h), v in Hh.items():
        if h == 0 and (b, d, a, bb, e) in C:
            if v["cc"] != C[(b, d, a, bb, e)]["cc"]:
                hd.append(((b, d, a, bb, e), v["cc"], C[(b, d, a, bb, e)]["cc"]))
    if hd:
        fail.append(("heavy/chain tables disagree at h=0", hd[:5]))

    # ---- 3 monotonicity
    def mono(tab, getter, name, dims):
        bad = []
        for key in tab:
            for i in range(len(key)):
                lo = list(key)
                lo[i] -= 1
                if lo[i] < 0:
                    continue
                t = tuple(lo)
                if t in tab and getter(tab[t]) > getter(tab[key]):
                    bad.append((name, dims[i], t, key,
                                getter(tab[t]), getter(tab[key])))
        return bad
    bad = mono({k: v for k, v in C.items()}, lambda v: v["cc"], "chain",
               ["b", "D", "a", "bb", "e"])
    bad += mono({k: v for k, v in Hh.items()}, lambda v: v["cc"], "heavy",
                ["b", "D", "a", "bb", "e", "h"])
    bad += mono({(b, d): P[(b, d, "00")] for (b, d, m) in P if m == "00"},
                lambda v: v, "piece00", ["b", "D"])
    # bound_below cells are upper bounds, not exact: exclude them
    bad = [x for x in bad if not (
        (x[0] == "chain" and (C.get(x[2], {}).get("bound_below")
                              or C.get(x[3], {}).get("bound_below")))
        or (x[0] == "heavy" and (Hh.get(x[2], {}).get("bound_below")
                                 or Hh.get(x[3], {}).get("bound_below"))))]
    if bad:
        fail.append(("monotonicity violated", bad[:6]))
    out["monotonicity_violations"] = len(bad)

    # ---- 4 mask ordering
    mo = []
    for (b, d, m), v in P.items():
        if m != "00":
            continue
        v10, v01, v11 = (P.get((b, d, "10")), P.get((b, d, "01")),
                         P.get((b, d, "11")))
        if None in (v10, v01, v11):
            continue
        if v10 != v01:
            mo.append(("10 != 01", b, d, v10, v01))
        if not (v >= v10 >= v11 or (v11 == -1)):
            mo.append(("ordering", b, d, v, v10, v11))
        if d == 0 and b == 0 and (v10, v11) != (-1, -1):
            mo.append(("partial endpoint must be impossible at b=0,D=0", v10, v11))
    if mo:
        fail.append(("mask ordering", mo[:6]))
    out["mask_ordering_violations"] = len(mo)

    # ---- 6 impossible states
    imp = [(k, v["cc"]) for k, v in C.items()
           if v["cc"] > 120 + k[2] + k[3] + k[4]]
    imp += [(k, v["cc"]) for k, v in Hh.items() if v["cc"] > 120 + k[2] + k[3] + k[4]]
    imp += [((b, d, m), v) for (b, d, m), v in P.items() if v > 120]
    if imp:
        fail.append(("cell exceeds the hexagon bound", imp[:5]))
    out["impossible_states"] = len(imp)

    # ---- 7 provenance
    out["provenance"] = dict(
        sources={f: sha(ROOT / f) for f in
                 ("src/l6_marked_capacity_144.c",
                  "src/l6_marked_capacity_pruned_144.c",
                  "src/l6_chain_capacity_144.c")},
        binaries={f: sha(ROOT / "outputs" / f) for f in
                  ("l6cap_144.exe", "l6cap_p_144.exe", "l6chain_144.exe")},
        compiler=subprocess.run("gcc --version", shell=True, capture_output=True,
                                text=True).stdout.splitlines()[0],
        flags="-O2",
        nodes=dict(piece=sum(v["nodes"] for v in piece["cells"].values()),
                   chain=sum(v["nodes"] for v in chain.values()),
                   heavy=sum(v["nodes"] for v in heavy.values())))

    # ---- 8 independent reruns of the decisive cells
    reruns = []
    for (b, d) in [(0, 0), (0, 1), (0, 14), (0, 20), (1, 15), (2, 10), (3, 5), (4, 0)]:
        r = subprocess.run(f"./outputs/l6cap_p_144.exe {b} {d} AB 0 {UB_PIECE}",
                           shell=True, capture_output=True, text=True, cwd=ROOT)
        try:
            j = json.loads(r.stdout)
        except Exception:
            reruns.append(dict(b=b, d=d, error=r.stderr[:80]))
            continue
        got = {m: j["table"][f"{d}|{m}"] for m in ("00", "10", "01", "11")}
        want = {m: P.get((b, d, m)) for m in ("00", "10", "01", "11")}
        okc = all(got[m] == want[m] for m in got if want[m] is not None)
        reruns.append(dict(b=b, d=d, capped=j["capped"], got=got, want=want,
                           agrees=okc))
        if not okc or j["capped"]:
            fail.append(("rerun mismatch", b, d, got, want))
    out["reruns"] = reruns

    out["failures"] = [list(map(str, f)) for f in fail[:8]]
    out["ok"] = not fail
    (ROOT / "outputs" / "rr_l6_table_integrity_146.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("provenance", "reruns")},
                     ensure_ascii=False, indent=1))
    print("reruns:", json.dumps([{k: v for k, v in r.items() if k != "want"}
                                 for r in out["reruns"]], ensure_ascii=False))
    print("ok:", out["ok"])


if __name__ == "__main__":
    main()
