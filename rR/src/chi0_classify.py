#!/usr/bin/env python3
"""Round R, section 3 -- exact classification of the zero-charge visits (chi = 0, not the first visit).
chi(v) = (w_in - 3) + [mid(last piece)] + sum_i eps_i,  eps_i = E'_i - [mid f_i] + [mid f_{i-1}] >= 0.
chi = 0  <=>  w_in = 3 (cross-trail w3 arcs go only from inner runs into MID runs), the last piece starts at a chain
start, and every jump is tight:
   mid -> start  with E' = -1 : only the wrap C_6 -> C_0 of a full chain (the mid piece is a full-chain suffix C_a..C_6);
   start -> mid  with E' = +1 : a w3 arc into a mid run;
   start -> start with E' = 0 : a w3 arc into a chain start;
   mid -> mid is never tight (w2 into a mid run is the natural link).
Hence a chi = 0 visit is a word of the grammar
   ROT = [C_a .. C_6] wrap [C_0 .. C_j]   (full chain C, 1 <= a <= 6, 0 <= j <= a-1)
   V   = ROT ( J3m ROT | J3s START )*      (J3m: tight w3 jump into the mid run D_b that starts the next ROT,
                                          J3s: tight w3 jump into a chain start, START = [E_0 .. x] any version interval)
This program enumerates, per trail version, the tight-jump graph and counts:
  * the ROT pieces (full chains x rotations a x prefix lengths j) and their ports;
  * tight jumps out of every run (as last run of a start piece) into mid runs that start a ROT (full-chain mid runs) and
    into chain starts;
  * the rotation macro states: (chain, a) with entry run C_a (mid, w_in = 3 needs a cross w3 arc into C_a) and exit
    run C_j; complete rotations (j = a - 1) have the ports of the standard option S(C_a);
  * which complete rotations admit a zero-charge ENTRY (some cross-trail w3 arc into C_a) and a free EXIT (some
    cross-trail w3 arc out of C_{a-1}), i.e. can sit inside a chain of chi = 0 visits.
usage: chi0_classify.py RUNS.bin OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs)
    W = runs_io.weight_matrix(runs); ci = chains.chain_info(W, tofs, mlen)
    cid, pos, clen, full, cut = ci["cid"], ci["pos"], ci["clen"], ci["full"], ci["cut"]
    T = np.array([x[0] for x in tv]); V = np.array([x[1] for x in tv])
    # predecessor run (exit run of an option) inside its version
    pred = np.zeros(N, np.int64)
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]; m = mlen[t]
            for k in range(m): pred[o0 + k] = o0 + (k - 1) % m
    same = (T[:, None] == T[None, :]) & (V[:, None] == V[None, :])
    cross = T[:, None] != T[None, :]
    w3 = W == 3
    # runs with a cross-trail w3 arc INTO them (zero-cost entry) / OUT of them (zero-cost exit into a mid run)
    w3_in = (w3 & cross).any(0); w3_out = (w3 & cross).any(1)
    out = dict(per_version=[], summary={})
    tot_rot = tot_full_rot = tot_free = 0; tot_j3m = tot_j3s = 0
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]; m = mlen[t]; idx = np.arange(o0, o0 + m)
            fulls = sorted({int(cid[r]) for r in idx if full[r]})
            nrot = 0; ncomplete = 0; nfree = 0; free_list = []
            for c in fulls:
                rr = ci["chains"][c]["runs"]       # C_0 .. C_6
                assert W[rr[6], rr[0]] == 2
                for a in range(1, 7):
                    nrot += a                      # prefixes C_0..C_j, j = 0..a-1
                    ncomplete += 1
                    ent, ex = rr[a], rr[a - 1]
                    if w3_in[ent] and w3_out[ex]: nfree += 1; free_list.append([c, a])
            # tight jumps from any run x (last run of a start piece) to a mid run of a full chain (J3m) or to a chain start (J3s)
            sub = W[np.ix_(idx, idx)]
            j3m = int(((sub == 3) & (np.array([full[r] and pos[r] > 0 for r in idx])[None, :])).sum())
            j3s = int(((sub == 3) & (np.array([pos[r] == 0 for r in idx])[None, :])).sum())
            # exclude natural links (x -> its version successor) from J3s
            nat = sum(1 for k in range(m) if sub[k, (k + 1) % m] == 3 and pos[idx[(k + 1) % m]] == 0)
            j3s -= nat
            out["per_version"].append(dict(trail=t, version=v, runs=m, full_chains=len(fulls), rot_pieces=nrot, complete_rotations=ncomplete,
                                           complete_rotations_free_both_ports=nfree, tight_jumps_into_full_mid=j3m, tight_jumps_into_starts_nonnatural=j3s))
            tot_rot += nrot; tot_full_rot += ncomplete; tot_free += nfree; tot_j3m += j3m; tot_j3s += j3s
    out["summary"] = dict(rot_pieces=tot_rot, complete_rotations=tot_full_rot, complete_rotations_free_both_ports=tot_free,
                          tight_jumps_into_full_mid=tot_j3m, tight_jumps_into_starts_nonnatural=tot_j3s,
                          cross_w3_arcs=int((w3 & cross).sum()),
                          cross_w3_entry_runs=int(w3_in.sum()), cross_w3_exit_runs=int(w3_out.sum()))
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    print(json.dumps(out["summary"]))
    from collections import Counter
    print("per phi version (complete rotations free on both ports):", Counter(d["complete_rotations_free_both_ports"] for d in out["per_version"] if d["runs"] == 42))
    print("per A version:", [d["complete_rotations_free_both_ports"] for d in out["per_version"] if d["runs"] > 100])

main()
