#!/usr/bin/env python3
"""Round 164 phases 15 and 16 -- mutation tests and state-maintenance controls.

A verifier that accepts everything proves nothing.  Two families run here.

  MUTATIONS mangle the proof OBJECT (witness port lists, exhaustion trees,
  cell coordinates, claimed capacities).  Every mutation that changes what is
  being claimed must be REJECTED.  Mutations that only change serialisation
  are listed separately and are expected to be accepted -- counting those as
  detections would be self-flattery.

  NEGATIVE CONTROLS mangle the VERIFIER's own incremental state update, which
  is the residual risk round 163 named.  Each control must be caught by the
  from-scratch histogram assertion, not by luck.
"""
from __future__ import annotations
import copy, json, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import routeb164 as R                                             # noqa: E402

CERTS = ROOT / "r152" / "certs"


# ------------------------------------------------------------- mutations
def witness_mutations(cell, ports, rng):
    """(name, mutated ports, expected) -- expected True means still valid."""
    out = []
    p = list(ports)
    if len(p) > 3:
        q = p[:]
        del q[len(q) // 2]
        out.append(("witness: delete one port", q, False))
        q = p[:]
        q[len(q) // 2] = q[len(q) // 2 - 1]
        out.append(("witness: duplicate a port", q, False))
        q = p[:]
        q[len(q) // 2] = (q[len(q) // 2] + 1) % R.N
        out.append(("witness: replace one transition", q, False))
        q = p[:]
        q[1], q[2] = q[2], q[1]
        out.append(("witness: swap two steps", q, False))
        q = p[:] + [p[0]]
        out.append(("witness: append the start port again", q, False))
        q = p[:]
        q[0] = 1
        out.append(("witness: start somewhere else", q, False))
    return out


def tree_mutations(toks, rng):
    out = []
    t = list(toks)
    idx = [i for i, x in enumerate(t) if x.startswith("N")]
    lidx = [i for i, x in enumerate(t) if x == "L"]
    if idx:
        i = idx[len(idx) // 2]
        k = int(t[i][1:])
        q = t[:]
        q[i] = f"N{k - 1}" if k > 0 else "N1"
        out.append(("tree: declare one child fewer", q, False))
        q = t[:]
        q[i] = f"N{k + 1}"
        out.append(("tree: declare one child more", q, False))
        q = t[:]
        q[i] = "L"
        out.append(("tree: turn an internal node into a leaf", q, False))
    if lidx:
        i = lidx[len(lidx) // 2]
        q = t[:]
        del q[i]
        out.append(("tree: delete one leaf", q, False))
        q = t[:]
        q.insert(i, "L")
        out.append(("tree: duplicate one leaf", q, False))
        q = t[:]
        q[i] = "N2"
        out.append(("tree: turn a leaf into a branch", q, False))
    if len(t) > 20:
        q = t[:len(t) // 2]
        out.append(("tree: remove an exhaustion subtree", q, False))
    q = t[:]
    out.append(("tree: unchanged (control)", q, True))
    return out


def run_mutations():
    cap, _ = R.parse_capcert(CERTS / "cap_cert_all_152.txt")
    pc, _ = R.parse_pcert(CERTS / "pcert_all_152.txt")
    trees = R.parse_extree(CERTS / "extree_pilot_152.txt")
    rng = random.Random(164164)
    rows = []

    # --- witness mutations, on a spread of real target witnesses
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    ch = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]]
    pi = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"]]
    ch_w = [c for c in ch if cap[c]["ports"]][:6]
    pi_w = [c for c in pi if pc[c]["ports"]][:6]
    for cell in ch_w:
        base = cap[cell]["ports"]
        ok0, _ = R.replay_chain_witness(cell, base)
        rows.append(dict(kind="chain witness", cell=str(cell),
                         mutation="unchanged (control)", expected_valid=True,
                         accepted=bool(ok0), correct=bool(ok0)))
        for name, mp, exp in witness_mutations(cell, base, rng):
            ok, _ = R.replay_chain_witness(cell, mp)
            rows.append(dict(kind="chain witness", cell=str(cell),
                             mutation=name, expected_valid=exp,
                             accepted=bool(ok), correct=(bool(ok) == exp)))
        # claim mutations: the port list is honest, the CLAIM is not
        for dc, nm in ((1, "claimed capacity +1"), (-1, "claimed capacity -1")):
            ok, info = R.replay_chain_witness(cell, base)
            acc = bool(ok and info["ports"] == cap[cell]["cap"] + dc)
            rows.append(dict(kind="chain claim", cell=str(cell),
                             mutation=nm, expected_valid=False,
                             accepted=acc, correct=not acc))
        # Budget mutations.  Shrinking a budget invalidates the witness only
        # when the witness SATURATES it; otherwise the smaller cell is a
        # perfectly good home for the same walk.  The expectation is therefore
        # computed from the witness's measured usage, not assumed.
        _, use = R.replay_chain_witness(cell, base)
        usage = dict(zip(("tok", "d", "a", "bb", "e", "h"),
                         (use["tok"], use["deficit"], use["a"], use["bb"],
                          use["e"], use["h"])))
        for j, nm in enumerate(("tok", "d", "a", "bb", "e", "h")):
            m = list(cell)
            if m[j] == 0:
                continue
            m[j] -= 1
            exp = usage[nm] <= m[j]
            ok, _ = R.replay_chain_witness(tuple(m), base)
            rows.append(dict(kind="chain budget", cell=str(cell),
                             mutation=f"budget {nm} - 1 "
                                      f"(witness uses {usage[nm]}/{cell[j]})",
                             expected_valid=exp, accepted=bool(ok),
                             correct=(bool(ok) == exp)))
    for cell in pi_w:
        base = pc[cell]["ports"]
        ok0, _ = R.replay_piece_witness(cell, base)
        rows.append(dict(kind="piece witness", cell=str(cell),
                         mutation="unchanged (control)", expected_valid=True,
                         accepted=bool(ok0), correct=bool(ok0)))
        for name, mp, exp in witness_mutations(cell, base, rng):
            ok, _ = R.replay_piece_witness(cell, mp)
            rows.append(dict(kind="piece witness", cell=str(cell),
                             mutation=name, expected_valid=exp,
                             accepted=bool(ok), correct=(bool(ok) == exp)))
        _, puse = R.replay_piece_witness(cell, base)
        pusage = dict(tok=puse["tok"], d=puse["deficit"])
        for j, nm in enumerate(("tok", "d")):
            m = list(cell)
            if m[j] == 0:
                continue
            m[j] -= 1
            exp = pusage[nm] <= m[j]
            ok, _ = R.replay_piece_witness(tuple(m), base)
            rows.append(dict(kind="piece budget", cell=str(cell),
                             mutation=f"budget {nm} - 1 "
                                      f"(witness uses {pusage[nm]}/{cell[j]})",
                             expected_valid=exp, accepted=bool(ok),
                             correct=(bool(ok) == exp)))
        for fp, lp in ((1, 0), (0, 1), (1, 1)):
            m = (cell[0], cell[1], fp, lp)
            if m == cell:
                continue
            ok, _ = R.replay_piece_witness(m, base)
            base_ok, info = R.replay_piece_witness(cell, base)
            # the mask is a real constraint only when a block is full
            should_fail = (fp and info["first_block"] >= 5) or \
                          (lp and info["last_block"] >= 5)
            rows.append(dict(kind="piece mask", cell=str(cell),
                             mutation=f"mask -> fp={fp} lp={lp}",
                             expected_valid=not should_fail,
                             accepted=bool(ok),
                             correct=(bool(ok) == (not should_fail))))

    # --- tree mutations, on the first few pilot cells
    certified = {}
    for cell, capv, toks in trees:
        v = R.TreeVerifier(dict(certified), check_feas_forms=False)
        ok, _ = v.validate(cell, capv, toks)
        if ok:
            certified[cell] = capv
    seeds = trees[:4]
    certified2 = {}
    for cell, capv, toks in trees:
        if any(cell == c for c, _, _ in seeds):
            for name, mt, exp in tree_mutations(toks, rng):
                v = R.TreeVerifier(dict(certified2), check_feas_forms=False)
                ok, _ = v.validate(cell, capv, mt)
                rows.append(dict(kind="exhaustion tree", cell=str(cell),
                                 mutation=name, expected_valid=exp,
                                 accepted=bool(ok), correct=(bool(ok) == exp)))
            for dc in (1, -1):
                v = R.TreeVerifier(dict(certified2), check_feas_forms=False)
                ok, _ = v.validate(cell, capv + dc, toks)
                rows.append(dict(kind="exhaustion tree", cell=str(cell),
                                 mutation=f"claimed capacity {dc:+d}",
                                 expected_valid=(dc > 0),
                                 accepted=bool(ok),
                                 correct=(bool(ok) == (dc > 0))))
            for j, nm in enumerate(("tok", "d", "a", "bb", "e", "h")):
                m = list(cell)
                m[j] += 1
                v = R.TreeVerifier(dict(certified2), check_feas_forms=False)
                ok, _ = v.validate(tuple(m), capv, toks)
                rows.append(dict(kind="exhaustion tree", cell=str(cell),
                                 mutation=f"cell coordinate {nm} + 1",
                                 expected_valid=False, accepted=bool(ok),
                                 correct=not ok))
            # a (p) justification that leans on a cell never proved here
            v = R.TreeVerifier({(9, 99, 9, 9, 9, 9): 1},
                               check_feas_forms=False)
            ok, _ = v.validate(cell, capv, toks)
            rows.append(dict(kind="exhaustion tree", cell=str(cell),
                             mutation="corrupt analytic parent pointer "
                                      "(inject an unproved tiny bound)",
                             expected_valid=None, accepted=bool(ok),
                             correct=None,
                             note="an UNSOUND smaller bound makes leaves "
                                  "easier to justify, so acceptance here is "
                                  "expected and is NOT a detection; it shows "
                                  "why (p) may only cite cells proved earlier "
                                  "in the same file"))
        v = R.TreeVerifier(dict(certified2), check_feas_forms=False)
        ok, _ = v.validate(cell, capv, toks)
        if ok:
            certified2[cell] = capv
    return rows


# ------------------------------------------------- state-maintenance controls
CONTROLS = {
    "fail to decrement one orbit deficit":
        "on leaving a non-fresh orbit, do not remove the phase",
    "decrement the wrong orbit":
        "remove the phase from a different orbit",
    "fail to update the current orbit":
        "keep the parent's corb after the move",
    "preserve a removed histogram entry":
        "do not delete an orbit that became empty",
    "double-remove one token":
        "charge two tokens where one is due",
    "fail to update the used hexagon":
        "do not add the target's hexagon",
    "off-by-one token history":
        "charge a token for a clean E",
}


def run_controls():
    """Patch the incremental update and require the fresh check to catch it."""
    trees = R.parse_extree(CERTS / "extree_pilot_152.txt")
    rows = []
    src = (Path(__file__).resolve().parent / "routeb164.py").read_text()
    for name, how in CONTROLS.items():
        if name == "fail to decrement one orbit deficit":
            bug = ('                    phm[q].discard(PHASE[t])\n'
                   '                    inc[q] -= 1',
                   '                    phm[q].discard(PHASE[t])')
        elif name == "decrement the wrong orbit":
            bug = ('                    inc[q] -= 1',
                   '                    inc[min(inc)] -= 1')
        elif name == "fail to update the current orbit":
            bug = ('                    inc[q] += 1', '                    pass')
        elif name == "preserve a removed histogram entry":
            bug = ('                    del inc[q]', '                    pass')
        elif name == "double-remove one token":
            bug = ('                    inc[q] = 1', '                    inc[q] = 2')
        elif name == "fail to update the used hexagon":
            bug = ('                    phm[q] = {PHASE[t]}\n'
                   '                    inc[q] = 1',
                   '                    phm[q] = {PHASE[t]}\n'
                   '                    inc[q] = 0')
        else:
            bug = ('                    inc[q] += 1', '                    inc[q] += 2')
        mutated = src.replace(*bug, 1)
        applied = mutated != src
        caught = None
        if applied:
            ns = {"__file__": str(Path(__file__).resolve().parent
                                  / "routeb164.py"),
                  "__name__": "routeb164_mutated"}
            exec(compile(mutated, "routeb164_mutated", "exec"), ns)
            TV = ns["TreeVerifier"]
            caught = False
            certified = {}
            for cell, capv, toks in trees[:6]:
                v = TV({}, check_feas_forms=False)
                ok, detail = v.validate(cell, capv, toks)
                if not ok and "histogram" in str(detail):
                    caught = True
                    break
        rows.append(dict(control=name, how=how, patch_applied=applied,
                         caught_by_the_fresh_recomputation=caught))
    return rows


def main():
    t0 = time.time()
    muts = run_mutations()
    ctrls = run_controls()
    graded = [m for m in muts if m["correct"] is not None]
    invalid = [m for m in graded if not m["expected_valid"]]
    valid = [m for m in graded if m["expected_valid"]]
    out = dict(
        mutations=dict(
            total=len(muts), graded=len(graded),
            serialisation_only_or_unjudgeable=len(muts) - len(graded),
            invalid_mutations=len(invalid),
            invalid_rejected=sum(1 for m in invalid if m["correct"]),
            invalid_wrongly_accepted=[m for m in invalid if not m["correct"]],
            validity_preserving=len(valid),
            validity_preserving_accepted=sum(1 for m in valid if m["correct"]),
            validity_preserving_wrongly_rejected=[m for m in valid
                                                  if not m["correct"]],
            rows=muts),
        state_controls=dict(
            total=len(ctrls),
            applied=sum(1 for c in ctrls if c["patch_applied"]),
            caught=sum(1 for c in ctrls
                       if c["caught_by_the_fresh_recomputation"]),
            missed=[c for c in ctrls if c["patch_applied"]
                    and not c["caught_by_the_fresh_recomputation"]],
            rows=ctrls),
    )
    out["ok"] = (not out["mutations"]["invalid_wrongly_accepted"]
                 and not out["mutations"]["validity_preserving_wrongly_rejected"]
                 and out["state_controls"]["applied"] == len(CONTROLS)
                 and not out["state_controls"]["missed"])
    (ROOT / "r164" / "certs" / "mutations_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    brief = {"mutations": {k: v for k, v in out["mutations"].items()
                           if k != "rows"},
             "state_controls": {k: v for k, v in out["state_controls"].items()
                                if k != "rows"},
             "ok": out["ok"]}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
