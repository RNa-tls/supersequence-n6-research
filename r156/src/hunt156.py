#!/usr/bin/env python3
"""Round 156 Phase 11b -- a targeted hunt for the HARDEST feature patterns.

The generic corpus rarely produces a fixed representative that has pure clean-E
circuits AND dirty type-A AND type-B joints AND heavy joints AND several beta
components at the same time.  This driver keeps generating until it has found
covers realising as many of the 2^8 feature patterns as it can, and runs the
full claim battery on every one of them.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402
from adversarial156 import FEATURES, feature_key                  # noqa: E402


def main(budget=40):
    t0 = time.time()
    rng = random.Random(20260916)
    _, w5 = R.words()
    seen, best, fails = Counter(), {}, []
    runs = 0
    rounds = 0
    while time.time() - t0 < budget * 60:
        rounds += 1
        words = ([(4, w) for w in C.corpus(4, "1234", [R.W4], rng, 600)]
                 + [(5, w) for w in C.corpus(5, "01234", w5, rng, 400)])
        if not words:
            continue
        for n, w in words:
            try:
                st = X.structure(w, n)
            except ValueError:
                continue
            for kh in (False, True):
                for pol in X.POLICIES:
                    r = X.extract(st, keep_heavy=kh, policy=pol)
                    runs += 1
                    key = feature_key(r)
                    seen[key] += 1
                    if sum(key) >= 6 and key not in best:
                        best[key] = dict(n=n, word=w, keep_heavy=kh,
                                         policy=pol, c=r["c"], d=r["d"],
                                         h=r["h"], D2=r["D2"], Qs=r["Qs"],
                                         sigma=r["sigma"], e=r["e"],
                                         chains=r["chains"], ok=r["ok"])
                    if not r["ok"]:
                        if len(fails) < 8:
                            fails.append(dict(n=n, word=w, keep_heavy=kh,
                                              policy=pol,
                                              failures=r["failures"][:5]))
        if time.time() - t0 > budget * 60:
            break
    out = dict(seconds=round(time.time() - t0, 1), rounds=rounds, runs=runs,
               features=list(FEATURES), patterns=len(seen),
               max_features=max((sum(k) for k in seen), default=0),
               rich_patterns={",".join(map(str, k)): v for k, v in
                              sorted(seen.items(), key=lambda kv: -sum(kv[0]))
                              if sum(k) >= 6},
               rich_examples={",".join(map(str, k)): v
                              for k, v in best.items()},
               failures=fails, ok=not fails)
    (ROOT / "r156" / "certs" / "hunt_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rich_examples",)},
                     ensure_ascii=False, indent=1)[:2200])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 40))
