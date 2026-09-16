#!/usr/bin/env python3
"""Round 156 -- cross-implementation agreement.

r156/src/extract156.py was written from the definitions without looking at the
audited modules at run time.  This driver runs it side by side with

    src/l6_splicing_145.py : analyse()     (node H.splice)
    src/l6_extraction_145.py : extract()   (node H.extract, the audit target)

on the same words and compares every shared quantity.  Agreement is not proof,
but a DISAGREEMENT would mean one of the two is wrong, so it is worth knowing.

The comparison uses the audited module's own default cut policy, which is the
one r156 calls `light_first`.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402
import l6_splicing_145 as SP                                      # noqa: E402
import l6_extraction_145 as EX                                    # noqa: E402

SPLICE_KEYS = ("P", "G", "O", "k", "S", "H", "D2", "Qs", "K", "R_int",
               "c", "d", "g", "z", "Z", "Bstar", "blocks")
EXTRACT_KEYS = ("P", "G", "O", "k", "S", "H", "D2", "Qs", "K", "R_int",
                "c", "d", "g", "h", "Bstar", "blocks", "chains", "sigma",
                "sum_P", "sum_D", "sum_tok")


def main():
    t0 = time.time()
    rng = random.Random(606060)
    ws, w5 = R.words()
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 700))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 300))]
    tally, diffs = Counter(), []
    for tag, n, W in pool:
        st = X.structure(W, n)
        sp = SP.analyse(W, n)
        tally["words"] += 1
        if not sp["ok"]:
            tally["splice_not_ok"] += 1
        mine = X.extract(st, keep_heavy=False, policy="light_first")
        bad = [kk for kk in SPLICE_KEYS if mine[kk] != sp[kk]]
        if bad:
            tally["splice_disagreement"] += 1
            if len(diffs) < 6:
                diffs.append(dict(tag=tag, n=n, kind="splice", keys=bad,
                                  mine={kk: mine[kk] for kk in bad},
                                  theirs={kk: sp[kk] for kk in bad}))
        for kh in (False, True):
            mine = X.extract(st, keep_heavy=kh, policy="light_first")
            th = EX.extract(W, n, keep_heavy=kh)
            tally["extract_pairs"] += 1
            if not th["ok"]:
                tally["target_not_ok"] += 1
            bad = [kk for kk in EXTRACT_KEYS if mine[kk] != th[kk]]
            # the target reports hex_repeats / retained_AB under other names
            if mine["hex_repeats"] != th["hex_repeats"]:
                bad.append("hex_repeats")
            if mine["retained_AB"] != th["retained_AB"]:
                bad.append("retained_AB")
            if bad:
                tally["extract_disagreement"] += 1
                if len(diffs) < 12:
                    diffs.append(dict(tag=tag, n=n, keep_heavy=kh,
                                      kind="extract", keys=bad,
                                      mine={kk: mine[kk] for kk in bad},
                                      theirs={kk: th[kk] for kk in bad}))
    out = dict(seconds=round(time.time() - t0, 1), tally=dict(tally),
               splice_keys=list(SPLICE_KEYS), extract_keys=list(EXTRACT_KEYS),
               disagreements=diffs,
               ok=(not tally["splice_disagreement"]
                   and not tally["extract_disagreement"]
                   and not tally["splice_not_ok"]
                   and not tally["target_not_ok"]))
    (ROOT / "r156" / "certs" / "agreement_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
