#!/usr/bin/env python3
"""Round 168 phase 18 -- generator-bug controls.

A deliberately broken generator must not be able to manufacture an accepted
upper bound.  Each control patches one line of `r168/src/gen168.py`, runs the
patched generator over twelve cheap cells -- discovering the value and then
building the tree, exactly as the real run does -- and requires that the
result is rejected.

THREE mechanisms count, and the report distinguishes them.  The third one is
new in round 168 and it is a direct consequence of dropping the table lookup.

  * the independent verifier rejects the tree;
  * the broken generator diverges and hits the node cap;
  * the discovered CAPACITY disagrees with the honest generator's.

The third mechanism is not a weakness of the verifier, it is the shape of the
failure.  Round 166 handed the generator the capacity to prove, so a buggy
generator had to produce a tree for the CORRECT value and could not, and the
verifier rejected it.  Round 168's generator discovers the value itself, so a
bug that loosens the state update makes it discover a value that is too LARGE
and then honestly prove that weaker bound.  The tree really is a complete case
analysis, so the verifier is right to accept it; what is wrong is the number.
A buggy generator therefore cannot manufacture a FALSE bound -- validity of
the tree is the proof -- it can only manufacture a WEAKER one, and that is
caught by capacity agreement (phase 19) and, downstream, by rows failing to
close.

The cap is far above the honest cost of these cells and low enough that
divergence is caught in seconds, so no control is allowed to burn 10^8 nodes
just to demonstrate that it is broken.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
import routeb164 as R                                             # noqa: E402

GEN = ROOT / "r168" / "src" / "gen168.py"
CELLS = 12
NODE_CAP = 2_000_000

BUGS = {
    "missing orbit-phase update": (
        "                    phm[q].add(R.PHASE[t])",
        "                    pass"),
    "incorrect token update (never charge a token)": (
        "                rec(t, q, ports + 1, tok - c, au + (kind == \"A\"),",
        "                rec(t, q, ports + 1, tok, au + (kind == \"A\"),"),
    "missing used-hexagon update": (
        "                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1",
        "                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0)"),
    "incorrect deficit update (+3 instead of +4)": (
        "                    deficit + (4 if fresh else -1))",
        "                    deficit + (3 if fresh else -1))"),
    "skipped legal branch (drop the last legal move)": (
        "        return out",
        "        return out[:-1] if len(out) > 1 else out"),
    "unsound predecessor bound (pretend every cell caps at 0)": (
        "        best = R.UBFALL + a + bb + e",
        "        best = 0"),
}


def load_engine(src):
    ns = {"__file__": str(GEN), "__name__": "gen168_mutated"}
    exec(compile(src, "gen168_mutated", "exec"), ns)
    return ns["Engine"]


def try_generate(Engine, order, honest=None):
    certified, caps = {}, []
    for i in range(CELLS):
        cell = order[i]
        try:
            g = Engine(certified, NODE_CAP)
            cap, err = g.discover(cell)
            if cap is not None:
                caps.append(cap)
            if cap is None:
                return dict(stage="discover", cell="|".join(map(str, cell)),
                            rejected_by="generator diverged past the node cap",
                            detail=str(err)[:110])
            g2 = Engine(certified, NODE_CAP)
            toks, err = g2.build(cell, cap)
        except Exception as e:
            return dict(stage="generate", cell="|".join(map(str, cell)),
                        rejected_by="generator crashed",
                        detail=f"{type(e).__name__}: {e}"[:110])
        if toks is None:
            return dict(stage="build", cell="|".join(map(str, cell)),
                        rejected_by="generator diverged past the node cap",
                        detail=str(err)[:110])
        v = R.TreeVerifier(dict(certified), check_feas_forms=False)
        ok, info = v.validate(cell, cap, toks)
        if not ok:
            return dict(stage="verify", cell="|".join(map(str, cell)),
                        rejected_by="independent verifier",
                        detail=str(info)[:130])
        certified[cell] = cap
    if honest is not None and caps != honest:
        bad = [dict(cell="|".join(map(str, order[j])), honest=honest[j],
                    buggy=caps[j])
               for j in range(min(len(caps), len(honest)))
               if caps[j] != honest[j]]
        return dict(stage="capacity", cell=bad[0]["cell"],
                    rejected_by="capacity disagreement with the honest "
                                "generator",
                    detail=f"{len(bad)} of {len(honest)} cells differ, "
                           f"first: {bad[0]}"[:160],
                    weaker_not_false=all(b["buggy"] > b["honest"]
                                         for b in bad))
    return caps if honest is None else None


def main():
    src = GEN.read_text()
    _cap, order = R.parse_capcert(ROOT / "r152" / "certs"
                                  / "cap_cert_all_152.txt")
    rows = []
    t0 = time.time()
    honest = try_generate(load_engine(src), order)
    clean = None if isinstance(honest, list) else honest
    if not isinstance(honest, list):
        honest = None
    rows.append(dict(control="unpatched generator (control)",
                     patch_applied=True, rejected=clean is not None,
                     expected_rejected=False, correct=clean is None,
                     discovered_capacities=honest, detail=clean))
    for name, (old, new) in BUGS.items():
        mutated = src.replace(old, new)
        applied = mutated != src
        res = try_generate(load_engine(mutated), order, honest) \
            if applied else None
        rows.append(dict(control=name, patch_applied=applied,
                         rejected=res is not None, expected_rejected=True,
                         correct=(applied and res is not None), detail=res))
        print(f"  {name:<56} "
              f"{'rejected' if res else 'accepted':<9}"
              f"{'OK' if (applied and res) else '  MISSED'}"
              + (f"  <- {res['rejected_by']}" if res else ""), flush=True)
    out = dict(
        generator=str(GEN.relative_to(ROOT)),
        generator_sha256=hashlib.sha256(src.encode()).hexdigest(),
        cells_per_control=CELLS, node_cap=NODE_CAP,
        controls=len(BUGS),
        applied=sum(1 for r in rows[1:] if r["patch_applied"]),
        caught=sum(1 for r in rows[1:] if r["correct"]),
        caught_by_the_verifier=sum(
            1 for r in rows[1:] if r["correct"] and r["detail"]
            and r["detail"]["rejected_by"] == "independent verifier"),
        caught_by_divergence=sum(
            1 for r in rows[1:] if r["correct"] and r["detail"]
            and "diverged" in r["detail"]["rejected_by"]),
        caught_by_capacity_disagreement=sum(
            1 for r in rows[1:] if r["correct"] and r["detail"]
            and r["detail"]["rejected_by"].startswith("capacity")),
        every_capacity_failure_was_weaker_not_false=all(
            r["detail"].get("weaker_not_false", True)
            for r in rows[1:] if r["correct"] and r["detail"]
            and r["detail"]["rejected_by"].startswith("capacity")),
        missed=[r["control"] for r in rows[1:] if not r["correct"]],
        control_case_passes=rows[0]["correct"],
        rows=rows)
    out["ok"] = (out["control_case_passes"] and not out["missed"]
                 and out["applied"] == len(BUGS))
    (ROOT / "r168" / "certs" / "generator_controls_168.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
