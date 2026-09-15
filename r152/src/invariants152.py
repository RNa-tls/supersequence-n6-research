#!/usr/bin/env python3
"""Round 152 -- structural invariants of the catalogue, checked exhaustively.

Two of them explain why a guard in the searchers is dead code, which matters:
a mutation test that removes a vacuous guard proves nothing, and a reader who
sees the guard is entitled to know whether it is load-bearing.

  I1  clean E is exactly tau:  ORB[FREE[v]] == ORB[v] and
      PHASE[FREE[v]] == PHASE[v] + 1 (mod 5), for all 720 words.
  I2  therefore the guard "a clean E never leaves the current orbit" can never
      fire, because the current orbit is always the orbit of the current word.
  I3  every word has exactly one clean E, one dirty A, one dirty B and five
      paid joints, and the four kinds have pairwise distinct targets.
  I4  dirty A leaves the orbit (it is sigma, not tau): ORB[DA[v]] != ORB[v]
      for all v -- so the phase-distinctness test is NOT dead in general.
  I5  a repeated phase means a repeated word, hence a repeated hexagon, so the
      phase test can only fire where the e budget has already let the walk
      land on a used hexagon.  With e = 0 the phase test is unreachable, which
      is why it must be mutation-tested on cells with e > 0.
  I6  heavy joints never target the current word or its end-rotation.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checker152 as C                                              # noqa: E402

N = C.N


def main():
    r = {}
    r["I1_clean_E_is_tau"] = all(
        C.ORB[C.FREE[v]] == C.ORB[v]
        and (C.PHASE[C.FREE[v]] - C.PHASE[v]) % 5 == 1 for v in range(N))
    r["I2_clean_E_orbit_guard_is_vacuous"] = r["I1_clean_E_is_tau"]
    r["I3_kind_counts"] = all(
        C.FREE[v] is not None and C.DA[v] is not None and C.DB[v] is not None
        and len(C.PAID[v]) == 5
        and len({C.FREE[v], C.DA[v], C.DB[v], *C.PAID[v]}) == 8
        for v in range(N))
    r["I4_dirtyA_leaves_the_orbit"] = all(
        C.ORB[C.DA[v]] != C.ORB[v] for v in range(N))
    # (orbit, phase) is a bijection onto the 720 words, so a reused phase IS a
    # reused word, hence a reused hexagon, hence something the e budget must
    # already have paid for.
    r["I5_orbit_phase_identifies_the_word"] = (
        len({(C.ORB[i], C.PHASE[i]) for i in range(N)}) == N)
    r["I6_heavy_avoids_self_and_end"] = all(
        all(t != v and t != C.IDX[C._end(C.PERMS[v])]
            for t, _ in C.HEAVY[v]) for v in range(N))
    r["heavy_edges"] = sum(len(C.HEAVY[v]) for v in range(N))
    r["ok"] = all(v for v in r.values() if isinstance(v, bool))
    out = Path(__file__).resolve().parent.parent / "certs" / "invariants_152.json"
    out.write_text(json.dumps(r, indent=1) + "\n")
    print(json.dumps(r, indent=1))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
