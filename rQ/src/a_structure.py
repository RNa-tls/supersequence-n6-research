#!/usr/bin/env python3
"""Round Q, section 4 -- internal structure of the A trails (and phi trails for comparison).
For a trail-version: chains = maximal w2 segments of the version cycle (full chains 7 runs with a w2 wrap p7 -> p1,
short chains); links = the version's w3 joins (chain end -> next chain start).  Census of all weight-2 and weight-3
joins between runs of the SAME trail-version that are not version joins:
  w2: wraps (p7 -> p1 of the same full chain); w3: alternative links (chain end -> start of another chain),
  rotation arcs (into a run that is not a chain start), and the rest.
usage: a_structure.py FAMILY.json OUT.json"""
import sys, json
from collections import Counter
import numpy as np

def main():
    fam = json.load(open(sys.argv[1])); out = []
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            runs = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]; m = len(runs)
            F = np.array([[int(c) for c in p] for p in runs], np.int64)
            L = np.array([[int(c) for c in (p[7:] + p[:7])] for p in runs], np.int64)
            W = np.full((m, m), 8, np.int64)
            for sft in range(7, 0, -1):
                k = 8 - sft; a = (L[:, sft:] * (8 ** np.arange(k))).sum(1); b = (F[:, :k] * (8 ** np.arange(k))).sum(1)
                W[a[:, None] == b[None, :]] = sft
            np.fill_diagonal(W, 99)
            c = np.array([W[(i - 1) % m, i] for i in range(m)])
            starts = [i for i in range(m) if c[i] == 3]                    # chain starts (entered by a link)
            chain_of = np.zeros(m, int); pos = np.zeros(m, int); chains = []
            for ci, st in enumerate(starts):
                nxt = starts[(ci + 1) % len(starts)]; L_ = (nxt - st) % m or m
                chains.append(list(range(st, st + L_)))
                for j, r in enumerate(range(st, st + L_)): chain_of[r % m] = ci; pos[r % m] = j
            lens = Counter(len(ch) for ch in chains)
            ver = {((i - 1) % m, i) for i in range(m)}
            cnt = Counter(); alt = []
            for i in range(m):
                for j in range(m):
                    if i == j or (i, j) in ver or W[i, j] > 3: continue
                    ci, cj = chain_of[i], chain_of[j]
                    if W[i, j] == 2:
                        kind = "w2_wrap" if ci == cj and pos[i] == len(chains[ci]) - 1 and pos[j] == 0 else "w2_other"
                    else:
                        i_end = pos[i] == len(chains[ci]) - 1; j_start = pos[j] == 0
                        kind = "w3_alt_link" if (i_end and j_start) else ("w3_into_start" if j_start else ("w3_from_end_rot" if i_end else "w3_rot_rot"))
                        if kind == "w3_alt_link": alt.append((int(ci), int(cj)))
                    cnt[kind] += 1
            rec = dict(trail=t, version=v, runs=m, chains=len(chains), chain_lengths=dict(sorted(lens.items())), joins=dict(sorted(cnt.items())))
            if m > 100: rec["alt_links_chain_pairs"] = alt
            out.append(rec)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    for r in out:
        if r["trail"] in (0, 1, 28) : print(json.dumps({k: v for k, v in r.items() if k != "alt_links_chain_pairs"}), r.get("alt_links_chain_pairs", ""))

main()
