#!/usr/bin/env python3
"""Round 25, sections 1, 3, 4, 9: ordered event words, the O* phase-visit
sequence, and the landing condition expressed as an ordered group product.

The ordered product formulation (section 4): all preparation edges are
forced to ell=5, so each is right-multiplication by a fixed generator
g_j = Sigma^5 * action_j. Writing a_2 for the abandonment joint's action
and (Sigma^m * action_c) for the completer, a landing at hub position j
is exactly the group equation

    Sigma^ell * a_2 * g_{x_1} * ... * g_{x_k} * Sigma^m * action_c = Sigma^j

which depends on the ORDER of the x_i because the generators do not
commute. This is the non-additive object Round 24's impossibility theorem
says a proof must use.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
def _load(n, f):
    p = WORK / f; s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
macro = _load("aopa25", "superperm_partial_f1_macro.py")
exact = macro.exact; core = exact.core; W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}; W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]; HUB = core.hexagon_id(exact.initial_state().p)

def kind(w, a, n):
    return {(2,False,False):"Z2",(2,True,True):"Z2abandon",(3,False,False):"R",
            (3,False,True):"Z3"}.get((w,a,n),"other")
def sym(k): return "R" if k == "R" else ("F" if k == "Z3" else "E")
def root(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state
def abandon_phase(ell):
    c = exact.initial_state()
    for _ in range(ell): c = exact.extend(c, W1).state
    return exact.ORBIT_PHASE[exact.extend(c, W2_10).target][1]

def collect(ell, depth):
    o = HEX0[ell + 1]; out = []
    fr = deque([(root(ell), 0, [])]); seen = {root(ell).stable_key()}
    while fr:
        st, d, tr_ = fr.popleft()
        if d >= depth: continue
        for e in macro.macro_edges(st):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None: continue
            k = kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other": continue
            sq, sph = exact.ORBIT_PHASE[e.run.state.p]; tq, tph = exact.ORBIT_PHASE[t.target]
            ev = {"index": d, "sym": sym(k), "joint": t.move.label,
                  "source_orbit": sq, "source_phase": sph,
                  "target_orbit": tq, "target_phase": tph,
                  "target_hexagon": core.hexagon_id(t.target),
                  "target_is_new_orbit": t.new_orbit, "targets_O_star": tq == o}
            if core.hexagon_id(t.target) == HUB:
                j = HEX0.index(tq) if tq in HEX0 else -1
                evs = tr_ + [ev]
                Z = [x for x in evs if x["sym"] != "R"]
                out.append({"abandonment_ell": ell, "o_star": o, "landing_position": j,
                            "landing_class": ("O_star" if j == ell + 1 else
                                              ("ell_plus_2" if j == ell + 2 else "far")),
                            "P_length": d, "ordered_word": "".join(x["sym"] for x in evs),
                            "n_zero_charge": len(Z), "zero_charge_parity": len(Z) % 2,
                            "n_R": len(evs) - len(Z),
                            "O_star_phase_sequence": [abandon_phase(ell)] +
                                                      [x["target_phase"] for x in evs if x["targets_O_star"]],
                            "events": evs})
                continue
            kk = t.state.stable_key()
            if kk in seen: continue
            seen.add(kk); fr.append((t.state, d + 1, tr_ + [ev]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_ordered_event_words.json"))
    a = ap.parse_args()
    rows = []
    for ell in range(5): rows.extend(collect(ell, a.depth))
    byc = Counter((r["landing_class"], r["zero_charge_parity"]) for r in rows)
    print("landing class -> zero-charge parity:")
    for k in sorted(byc): print(f"  {k[0]:12s} parity={k[1]}  count={byc[k]}")
    ostar_even = all(r["zero_charge_parity"] == 0 for r in rows if r["landing_class"] == "O_star")
    p2_even = all(r["zero_charge_parity"] == 0 for r in rows if r["landing_class"] == "ell_plus_2")
    far_mixed = len({r["zero_charge_parity"] for r in rows if r["landing_class"] == "far"}) > 1
    print(f"\n#Z even at O* landing      : {ostar_even}")
    print(f"#Z even at ell+2 landing   : {p2_even}")
    print(f"#Z parity MIXED at far     : {far_mixed}")
    seqs = sorted({tuple(r["O_star_phase_sequence"]) for r in rows if r["landing_class"] == "O_star"})
    print(f"\nO* phase-visit sequences at O* landing ({len(seqs)} distinct):")
    for s in seqs[:10]: print(f"   {list(s)}")
    rep = {"schema": "rr-ordered-event-words-v1",
           "ordered_product_formulation": (
               "Sigma^ell * a_2 * g_{x_1} * ... * g_{x_k} * Sigma^m * action_c = Sigma^j, "
               "with g_j = Sigma^5 * action_j; order matters because the generators do not commute"),
           "zero_charge_parity_by_landing_class": {f"{k[0]}|parity={k[1]}": v for k, v in sorted(byc.items())},
           "n_Z_even_at_O_star": ostar_even, "n_Z_even_at_ell_plus_2": p2_even,
           "n_Z_parity_mixed_at_far": far_mixed,
           "O_star_phase_sequences_at_O_star_landing": [list(s) for s in seqs],
           "grade": "root-local exhaustive",
           "rows": rows}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)

if __name__ == "__main__":
    main()
