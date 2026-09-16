#!/usr/bin/env python3
"""Round 156 -- run the independent extraction audit over every real cover
available, under EVERY cut policy and both heavy modes."""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402

W4 = "123412314231243121342132413214321"


def words():
    out = []
    out.append(("n4_optimum", 4, W4))
    raw = json.loads((ROOT / "outputs" / "rr_nr6_n5_minima_142.json").read_text())
    w5 = sorted({e["word"] for e in raw if isinstance(e, dict) and "word" in e})
    for i, w in enumerate(w5):
        out.append((f"n5_min_{i}", 5, w))
    out.append(("n6_witness_872", 6,
                (ROOT / "data" / "verified_872_witness.txt").read_text().strip()))
    return out, w5


def sweep(tag, n, W, stats, bad, rng):
    st = X.structure(W, n)
    for kh in (False, True):
        for pol in X.POLICIES:
            r = X.extract(st, keep_heavy=kh, policy=pol, rng=rng)
            stats["runs"] += 1
            if not r["ok"]:
                stats["failures"] += 1
                if len(bad) < 12:
                    bad.append(dict(tag=tag, keep_heavy=kh, policy=pol,
                                    failures=r["failures"][:6]))
            for key, cond in (("with_AB", r["retained_AB"] > 0),
                              ("with_heavy", r["h"] > 0),
                              ("multi_chain", r["chains"] > 1),
                              ("sigma_pos", r["sigma"] > 0),
                              ("shared_cut", r["shared"] > 0),
                              ("e_pos", r["e"] > 0),
                              ("g_pos", r["g"] > 0),
                              ("c_pos", r["c"] > 0),
                              ("D2_pos", r["D2"] > 0),
                              ("Qs_pos", r["Qs"] > 0),
                              ("tok_pos", r["sum_tok"] > 0)):
                if cond:
                    stats[key] += 1
    return st


def main():
    t0 = time.time()
    rng = random.Random(20260916)
    stats, bad = Counter(), []
    named = {}
    ws, w5 = words()
    for tag, n, W in ws:
        st = sweep(tag, n, W, stats, bad, rng)
        named[tag] = X.extract(st)
        named[tag].pop("per_chain", None)
    # ---- dirty corpora
    c4 = C.corpus(4, "1234", [W4], rng, 900)
    c5 = C.corpus(5, "01234", w5, rng, 400)
    corp = {"n4": (4, c4), "n5": (5, c5)}
    for name, (n, cs) in corp.items():
        for i, w in enumerate(cs):
            sweep(f"{name}_{i}", n, w, stats, bad, rng)
    out = dict(seconds=round(time.time() - t0, 1),
               policies=list(X.POLICIES),
               corpus={"n4": len(c4), "n5": len(c5)},
               named=named, stats=dict(stats), bad=bad,
               ok=(stats["failures"] == 0))
    (ROOT / "r156" / "certs" / "real_covers_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "named"},
                     ensure_ascii=False)[:2000])
    for k, v in named.items():
        print(k, json.dumps({x: v[x] for x in
                             ("P", "G", "O", "k", "c", "d", "g", "K", "R_int",
                              "Z", "H", "Bstar", "chains", "sigma", "sum_P",
                              "required", "MASTER_holds", "ok")}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
