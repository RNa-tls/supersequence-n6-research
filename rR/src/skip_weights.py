#!/usr/bin/env python3
"""Round S -- the skip weight law (used by Theorem S2).
For k consecutive FULL chains C^1..C^k of a trail version, Q_end the run before C^1_0 and N_0 the run after C^k_6:
        w(Q_end, N_0) = 3 + k            (k = 1: Theorem R8 of Round R)
so the detached structure (skip link 3 + k, k closed 7-cycles of weight 14) weighs exactly as much as the natural
passage ((k + 1) links of weight 3, 6 k of weight 2):  3 + k + 14 k = 3 (k + 1) + 12 k.
Checked for every maximal run of consecutive full chains in all 60 trail versions (phi: k <= 4; for k = 5 the skip link
is the wrap of the remaining chain, weight 2).  Also lists the skip weights over mixed runs (with path chains) of the A
versions: these are NOT of the form 3 + k and are not used by any theorem.
usage: skip_weights.py RUNS.bin OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains
from collections import Counter

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); cache = os.environ.get("W_CACHE")
    W = np.load(cache) if cache and os.path.exists(cache) else runs_io.weight_matrix(runs)
    ci = chains.chain_info(W, tofs, mlen)
    law = Counter(); viol = 0; maxrun = Counter(); mixed = Counter(); wrap5 = Counter()
    for t in range(30):
        for v in range(2):
            chs = sorted([c for c in ci["chains"] if c["t"] == t and c["v"] == v], key=lambda c: c["start"]); n = len(chs); isA = mlen[t] > 100
            # longest run of consecutive full chains (cyclic)
            best = 0
            for i in range(n):
                k = 0
                while k < n and chs[(i + k) % n]["full"]: k += 1
                best = max(best, k)
            maxrun[("A" if isA else "phi", best)] += 1
            for i in range(n):
                for k in range(1, n):
                    sk = [chs[(i + 1 + j) % n] for j in range(k)]; w = int(W[chs[i]["runs"][-1], chs[(i + 1 + k) % n]["runs"][0]])
                    if all(c["full"] for c in sk):
                        if k <= n - 2:
                            law[("A" if isA else "phi", k, w)] += 1
                            if w != 3 + k: viol += 1
                        else: wrap5[("A" if isA else "phi", k, w)] += 1       # all other chains skipped: the wrap of chain i
                    elif isA and k <= 6:
                        mixed[("".join("F" if c["full"] else "p" for c in sk), w)] += 1
                    if not all(c["full"] for c in sk) and not isA: break
    out = dict(law_counts=[dict(kind=a, k=k, weight=w, count=c) for (a, k, w), c in sorted(law.items())], violations_of_3_plus_k=viol,
               longest_run_of_consecutive_full_chains=[dict(kind=a, length=l, versions=c) for (a, l), c in sorted(maxrun.items())],
               all_other_chains_skipped=[dict(kind=a, k=k, weight=w, count=c) for (a, k, w), c in sorted(wrap5.items())],
               mixed_runs_A_versions_k_le_6=[dict(pattern=p, weight=w, count=c) for (p, w), c in sorted(mixed.items())],
               skip_weight_law_holds=(viol == 0))
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("law_counts", "violations_of_3_plus_k", "longest_run_of_consecutive_full_chains", "all_other_chains_skipped")}))
main()
