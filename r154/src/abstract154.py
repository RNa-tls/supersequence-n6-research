#!/usr/bin/env python3
"""Round 154 Step 8 -- exhaustive search of an EXPLICITLY DEFINED finite universe.

THE UNIVERSE.  Fix n = 6.  A *locally legal cycle candidate of length m* is a
cyclic sequence (q_1, ..., q_m) of DISTINCT words of S_6 such that for every i
(indices mod m) the pair (q_i, q_{i+1}) is a legal joint, i.e.
omega(end(q_i), q_{i+1}) >= 2.  Every beta-component that avoids the dummy is
such a candidate -- the converse is NOT claimed, and that gap is stated
explicitly in the report.

THE QUOTIENT.  Left S_6 acts on the 720 words, commutes with the whole
catalogue (round 149 Theorem 2.4, rechecked over all 518,400 pairs in round
153) and is transitive, so every candidate has a representative with
q_1 = 123456.  Cyclic rotation is also a symmetry of a cycle, and fixing q_1
kills it as well.  Fixing q_1 = 123456 is therefore an exact quotient, not a
sample: nothing is lost.

WHAT IS COUNTED.  For each m the search is exhaustive over the quotient, and it
reports how many cycles exist and how many distinct EDGE-TYPE MULTISETS occur.
The type-multiset is the natural invariant any "type" classification would have
to be a function of.
"""
from __future__ import annotations
import json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r154" / "src"))
from beta_defs154 import build, end, omega, joint_type               # noqa: E402

N = 6


def main(max_m=3):
    W, IDX = build(N)
    nW = len(W)
    # legal targets and their types, from the source word (not from end(v))
    tgt = [[] for _ in range(nW)]
    ty = [[None] * nW for _ in range(nW)]
    for vi, v in enumerate(W):
        e = end(v)
        for ti, t in enumerate(W):
            g = omega(e, t, N)
            if g == 1:
                continue
            k, _ = joint_type(v, t, N)
            tgt[vi].append(ti)
            ty[vi][ti] = k
    out = dict(n=N, words=nW,
               legal_targets_per_source=sorted({len(x) for x in tgt}),
               universe="cyclic sequences of distinct words, every consecutive "
                        "pair a legal joint (gap >= 2), quotiented by left S6 "
                        "and by cyclic rotation via fixing q_1 = 123456",
               quotient="left S6 (720, transitive, catalogue-equivariant) and "
                        "cyclic rotation; both removed exactly by fixing q_1",
               pruning="none beyond the legality test itself",
               lengths={})
    start = IDX["123456"]
    for m in range(1, max_m + 1):
        t0 = time.time()
        examined = 0
        cycles = 0
        multisets = Counter()
        if m == 1:
            examined = 1
            if ty[start][start] is not None:
                cycles = 1
                multisets[((ty[start][start], 1),)] += 1
        elif m == 2:
            for b in tgt[start]:
                examined += 1
                if b == start:
                    continue
                if ty[b][start] is None:
                    continue
                cycles += 1
                multisets[tuple(sorted(Counter(
                    [ty[start][b], ty[b][start]]).items()))] += 1
        else:
            # depth-first over the (m-1) free positions, exhaustive
            path = [start]
            used = {start}

            def rec(k):
                nonlocal examined, cycles
                cur = path[-1]
                if k == m - 1:
                    for b in tgt[cur]:
                        examined += 1
                        if b in used or ty[b][start] is None:
                            continue
                        cycles += 1
                        types = [ty[path[i]][path[i + 1]] for i in range(m - 1)]
                        types.append(ty[b][start])
                        multisets[tuple(sorted(Counter(types).items()))] += 1
                    return
                for b in tgt[cur]:
                    examined += 1
                    if b in used:
                        continue
                    used.add(b)
                    path.append(b)
                    rec(k + 1)
                    path.pop()
                    used.discard(b)

            rec(0)
        # the size of the universe at this length, before legality is tested
        universe_size = 1
        for _ in range(m - 1):
            universe_size *= (nW - 1)
        out["lengths"][str(m)] = dict(
            universe_upper_bound_after_quotient=universe_size,
            branches_examined=examined,
            exhaustive=True,
            cycles_found=cycles,
            distinct_edge_type_multisets=len(multisets),
            multisets={json.dumps(k): v for k, v in multisets.most_common(40)},
            seconds=round(time.time() - t0, 1))
        print(f"  m={m}: cycles={cycles:,} distinct type multisets="
              f"{len(multisets)} examined={examined:,} "
              f"({out['lengths'][str(m)]['seconds']}s)")
        for k, v in multisets.most_common(8):
            print(f"      x{v:<10,} {k}")
    (ROOT / "r154" / "certs" / "abstract_154.json").write_text(
        json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 3))
