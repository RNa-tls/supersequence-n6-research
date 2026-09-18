#!/usr/bin/env python3
"""Round 170 -- the production cost model over the exact 35-cell basis.

Two things have to be settled before any plan built on census-safe targets can
be trusted, and the first is a trap.

JOINT SAFETY.  `safe170.py` derives S(K) one cell at a time, holding every
other selected cell at its exact value.  A plan does not certify one cell -- it
relaxes ALL of them to their safe bounds at once, and individually safe bounds
need not be jointly safe: each row has slack against one relaxation that
several relaxations together can exhaust.  So the joint assignment is tested
directly, and if it fails the bounds are tightened until it holds.  A plan
quoting individually-derived S values without this check would be unsound.

ROUTE AND COST.  Each of the 35 basis cells is (P1)-maximal, so every one needs
its own certificate; nothing is free by domination inside a minimal basis.  A
cell is then classified by how its certificate can actually be obtained:

  CERTIFIED_ALREADY   a verified batch in the current DAG covers it;
  MEASURED_SAFE       round 170 built it genuinely at its safe bound, and the
                      cost is a measurement, not an estimate;
  UNMEASURED          neither -- only round 152's table-dependent node count
                      exists as a reference point.

The last class is reported as unmeasured rather than projected.  Round 169's
78.5 billion node figure came from extrapolating one cost model across 36
cells; this module does not repeat that, because the two cells round 170 did
measure came in at 8.1 million and 218 nodes against safe bounds, four orders
of magnitude apart, which is exactly the spread that makes such extrapolation
worthless.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                               # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD}
    N152 = {parse(r["cell"]): r["nodes"] for r in rows if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    PC = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in prows
          if r["status"] in GOOD}

    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = sorted(set([parse(c) for c in src["minimum"]["cells"]]
                       + [parse(c) for c in
                          bas["minimum"]["witness_completion"]]))
    assert len(BASIS) == bas["minimum"]["cells"]

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    def closes(vals):
        S.apply(set(BASIS), values=vals)
        v = S.verdicts(EXS)
        return all(v[k] == "STRICTLY_CLOSED" for k in EX)

    def exact_of(K):
        return U.get(K) or PC.get((K[0], K[1], 0, 0))

    t0 = time.time()
    assert closes({}), "the basis must close every exposed row at exact values"

    # ---- individual safe bounds
    indiv = {}
    for K in BASIS:
        fb = 120 + K[2] + K[3] + K[4]
        ex = exact_of(K)
        if ex is None:
            indiv[K] = None
            continue
        if closes({K: fb}):
            indiv[K] = fb
            continue
        lo, hi = ex, fb
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if closes({K: mid}):
                lo = mid
            else:
                hi = mid
        indiv[K] = lo
    missing = [cellstr(K) for K, v in indiv.items() if v is None]
    print(f"individual safe bounds derived for "
          f"{len(BASIS) - len(missing)}/{len(BASIS)}", flush=True)

    # ---- joint safety of all of them at once
    joint = {K: v for K, v in indiv.items() if v is not None}
    joint_ok_raw = closes(joint)
    print(f"all bounds applied together: "
          f"{'SAFE' if joint_ok_raw else 'NOT SAFE -- tightening'}",
          flush=True)

    tightened, rounds = dict(joint), 0
    if not joint_ok_raw:
        # walk every relaxed cell back toward its exact value until the joint
        # assignment closes.  Largest slack first, since that is where the
        # shared margin is being spent.
        while not closes(tightened) and rounds < 400:
            rounds += 1
            worst = max((K for K in tightened
                         if tightened[K] > exact_of(K)),
                        key=lambda K: tightened[K] - exact_of(K),
                        default=None)
            if worst is None:
                break
            tightened[worst] -= 1
    joint_ok = closes(tightened)
    total_slack_indiv = sum(v - exact_of(K) for K, v in joint.items())
    total_slack_joint = sum(v - exact_of(K) for K, v in tightened.items())
    print(f"joint assignment {'holds' if joint_ok else 'FAILS'} after "
          f"{rounds} tightening steps; slack {total_slack_indiv} -> "
          f"{total_slack_joint}", flush=True)

    # ---- route and cost per cell
    vb = json.loads((ROOT / "r170" / "certs"
                     / "verification_b_h_170.json").read_text())
    have = {parse(c) for c in vb["certified_cells"]}
    measured = {}
    for tag, rel in (("h", "r170/certs/genuine_target_h_170.json"),
                     ("a2", "r170/certs/genuine_target_a2_170.json")):
        p = ROOT / rel
        if p.exists():
            r = json.loads(p.read_text())
            if r.get("ok"):
                measured[parse(r["cell"])] = r

    plan = []
    for K in BASIS:
        row = dict(cell=cellstr(K), exact_diagnostic=exact_of(K),
                   individual_S=indiv[K], joint_S=tightened.get(K),
                   p1_maximal=True)
        if K in measured:
            m = measured[K]
            row.update(route="MEASURED_SAFE", proof_nodes=m["proof_nodes"],
                       built_at_S=m["census_safe_bound_S"],
                       certificate=m["stored"])
        elif K in have:
            row.update(route="CERTIFIED_ALREADY", proof_nodes=None)
        else:
            row.update(route="UNMEASURED",
                       round_152_nodes_table_dependent=N152.get(K))
        plan.append(row)

    tally = {}
    for r in plan:
        tally[r["route"]] = tally.get(r["route"], 0) + 1
    meas_nodes = sum(r["proof_nodes"] for r in plan
                     if r["route"] == "MEASURED_SAFE")
    lad = {}
    for tag, rel in (("h", "r170/certs/generation_ladder_h_170.json"),
                     ("a2", "r170/certs/generation_ladder_a2_170.json")):
        lad[tag] = json.loads((ROOT / rel).read_text())["total_proof_nodes"]

    out = dict(
        inputs={p: sha(p) for p in
                ("r170/certs/basis_170.json",
                 "r169/certs/p1_closure_169.json",
                 "r152/certs/verify_all_c152.json")},
        basis_size=len(BASIS),
        exposed_rows=len(EX),
        all_members_p1_maximal=True,
        joint_safety=dict(
            individually_safe_bounds=len(joint),
            individually_derived_total_slack=total_slack_indiv,
            all_at_once_is_safe=joint_ok_raw,
            tightening_steps=rounds,
            joint_total_slack=total_slack_joint,
            joint_assignment_holds=joint_ok,
            why_it_matters="a plan relaxes every cell at once; each row's "
                           "slack is shared, so individually safe bounds can "
                           "fail jointly and must be checked, not assumed"),
        route_tally=tally,
        measured_proof_nodes=meas_nodes,
        ladder_investment=lad,
        ladder_amortisation=dict(
            note="a (p) lookup needs the certified cell to dominate the state "
                 "in EVERY component, the first included, so a rung with "
                 "b = 0 can never bound a state with b >= 1.  Ladders are "
                 "therefore per-b-level and do not amortise across the "
                 "basis as a whole",
            h_ladder_b=0, a2_ladder_b=0,
            basis_cells_at_b0=sum(1 for K in BASIS if K[0] == 0),
            basis_cells_at_b_ge_1=sum(1 for K in BASIS if K[0] >= 1)),
        cells_without_a_capacity_reference=missing,
        plan=plan,
        honest_limit="33 of the 35 have no measured table-free cost at a safe "
                     "bound; they are reported as UNMEASURED rather than "
                     "extrapolated, because the two measured cells differ by "
                     "four orders of magnitude",
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = bool(joint_ok)
    (ROOT / "r170" / "certs" / "cost_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "plan")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
