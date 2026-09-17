#!/usr/bin/env python3
"""Round 168 phase 18 -- generator-bug controls.

A deliberately broken generator must not be able to manufacture an accepted
upper bound.  Each control patches one line of `r168/src/gen168.py`, runs the
patched generator over twelve cheap cells -- discovering the value and then
building the tree, exactly as the real run does -- and requires that the
result is rejected.

Two rejection mechanisms count, and the report distinguishes them:

  * the independent verifier rejects the tree;
  * the broken generator diverges and hits the node cap.

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


def try_generate(Engine, order):
    certified = {}
    for i in range(CELLS):
        cell = order[i]
        try:
            g = Engine(certified, NODE_CAP)
            cap, err = g.discover(cell)
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
    return None


def main():
    src = GEN.read_text()
    _cap, order = R.parse_capcert(ROOT / "r152" / "certs"
                                  / "cap_cert_all_152.txt")
    rows = []
    t0 = time.time()
    clean = try_generate(load_engine(src), order)
    rows.append(dict(control="unpatched generator (control)",
                     patch_applied=True, rejected=clean is not None,
                     expected_rejected=False, correct=clean is None,
                     detail=clean))
    for name, (old, new) in BUGS.items():
        mutated = src.replace(old, new)
        applied = mutated != src
        res = try_generate(load_engine(mutated), order) if applied else None
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
            and r["detail"]["rejected_by"] != "independent verifier"),
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
