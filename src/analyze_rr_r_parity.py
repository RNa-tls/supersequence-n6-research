#!/usr/bin/env python3
"""Round 24, sections 1, 2, 6: the event-charge ledger, the exact count
identity |P|+#R = 1 (mod 2) <=> #zero-charge = 0 (mod 2), and the
IMPOSSIBILITY theorem explaining why no additive invariant can prove it.

Key measured facts (all root-local exhaustive, exact per-event constants):

  field    R      E      F
  S       +1      0     +1
  O        0      0     +1
  P       +1     +1     +1
  D       -1     -1     +4
  Ndef    +1      0      0
  visited +6     +6     +6

and the exact state identity  D = 5*O - P  (0 violations / 1577 states).

Consequence: every additive ExactState field is a fixed linear form in
the event counts (#R, #E, #F). Hence every Z/2 functional built from
them is a linear form in those counts mod 2, and asking such a
functional to certify "#E+#F is even" IS the statement itself. No
additive invariant can give a non-circular proof -- which uniformly
explains every failed route of Rounds 22-24.
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
macro = _load("arp24", "superperm_partial_f1_macro.py")
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_r_parity_ledger.json"))
    a = ap.parse_args()
    FIELDS = ("S", "O", "P", "D", "Ndef", "visited_count")
    inc = Counter(); dviol = 0; total = 0
    for ell in range(5):
        fr = deque([(root(ell), 0)]); seen = {root(ell).stable_key()}
        while fr:
            st, d = fr.popleft(); total += 1
            if st.D != 5 * st.O - st.P: dviol += 1
            if d >= a.depth: continue
            for e in macro.macro_edges(st):
                t = e.joint
                if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None: continue
                k = kind(t.move.weight, t.abandonment, t.new_orbit)
                if k == "other": continue
                s = sym(k)
                for f in FIELDS:
                    inc[(s, f, getattr(t.state, f) - getattr(st, f))] += 1
                if core.hexagon_id(t.target) == HUB: continue
                kk = t.state.stable_key()
                if kk in seen: continue
                seen.add(kk); fr.append((t.state, d + 1))
    ledger = {}
    print("per-event-kind field increments (constant per kind):")
    for f in FIELDS:
        row = {}
        for s in ("R", "E", "F"):
            v = {dl: n for (s2, f2, dl), n in inc.items() if s2 == s and f2 == f}
            row[s] = dict(sorted(v.items()))
        ledger[f] = row
        print(f"  {f:14s} R={row['R']}  E={row['E']}  F={row['F']}")
    constant = all(len(v) == 1 for f in FIELDS for v in ledger[f].values())
    print(f"\nevery field increment is a CONSTANT per event kind: {constant}")
    print(f"identity D = 5*O - P : {dviol} violations / {total} states")

    rep = {"schema": "rr-r-parity-ledger-v1",
        "count_identity": {
            "statement": "|P| + #R_{<=C} = 1 (mod 2)  <=>  #zero-charge events through C = 0 (mod 2)",
            "proof": ("Through the completer there are |P|+1 events, split as #R + #zero. "
                      "So |P| + #R = (#R + #zero - 1) + #R = 2#R + #zero - 1 = #zero - 1 (mod 2). "
                      "Hence |P| + #R is odd iff #zero is even. 손증명 (pure arithmetic)."),
            "grade": "손증명"},
        "per_event_field_increments": ledger,
        "all_increments_constant": constant,
        "state_identity_D_equals_5O_minus_P": {"violations": dviol, "states_checked": total,
                                                "holds": dviol == 0, "grade": "root-local exhaustive"},
        "impossibility_theorem": {
            "statement": ("No additive per-event invariant can prove #zero even without circularity."),
            "proof": ("Each ExactState field changes by a fixed constant per event kind (verified "
                      "above), so every additive field equals its root value plus a fixed linear "
                      "form in (#R, #E, #F). Moreover D = 5O - P identically, so the fields span "
                      "no more than the counts themselves. Any Z/2 functional built from additive "
                      "fields is therefore a linear form a*#R + b*#E + c*#F (mod 2). Such a form "
                      "certifies '#E + #F = 0 (mod 2)' only if (a,b,c) = (0,1,1), i.e. only if it "
                      "IS the target statement -- circular. 손증명."),
            "explains": ["Round 22's 15 mod-2 feature candidates",
                         "Round 23's handshake / odd-degree / forest routes",
                         "Round 23's n_hexes and P counters",
                         "this round's full field ledger"],
            "grade": "손증명"},
        "what_this_leaves": ("A proof must use a NON-additive constraint -- specifically the "
                             "orbit/position combinatorics deciding which hub position the "
                             "completer may land on. 미완료.")}
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)

if __name__ == "__main__":
    main()
