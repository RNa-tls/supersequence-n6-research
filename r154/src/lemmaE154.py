#!/usr/bin/env python3
"""Round 154 -- the two structural lemmas the classification actually needs,
proved and then checked exhaustively.

LEMMA 0 (no fixed point).  beta has no fixed point, so every beta-component has
length >= 2.
  Proof.  For a pass q, beta(q) = q would mean the joint out of end(v_q) lands
  on v_q itself.  The unique target at overlap gap 1 from end(v) is v, and a
  gap-1 step is the successor INSIDE a pass, never a joint between two passes.
  So that edge is not a joint, a contradiction.  And beta(dummy) = 1 != dummy
  whenever P >= 1.  The check below confirms the one string fact used: for all
  720 words the unique gap-1 target of end(v) is v.

LEMMA E (pure clean-E circuits).  A beta-component that avoids the dummy and
all of whose edges are clean E lies in a single tau-orbit, has length exactly
n - 1, and uses every element of that orbit.
  Proof.  The clean-E target of v is tau(v): same tau-orbit, phase + 1.  So
  following E edges from v walks the tau-orbit of v cyclically.  A tau-orbit
  has exactly n - 1 elements (checked below for n = 6: all 144 orbits have 5),
  and tau restricted to it is an (n-1)-cycle, so the first return to v is after
  n - 1 steps and every element has been used.  Since beta is a permutation the
  component is exactly that set.

These two, plus "beta is a permutation", are the whole of what the repository's
component classification rests on.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r154" / "src"))
from beta_defs154 import build, sigma, tau, end, omega, classes      # noqa: E402


def main():
    n = 6
    W, IDX = build(n)
    ORB, nq = classes(W, tau)
    HEX, nh = classes(W, sigma)

    # Lemma 0's string fact
    gap1_unique_and_self = all(
        [t for t in W if omega(end(v), t, n) == 1] == [v] for v in W)

    # Lemma E's string facts
    tau_is_cleanE = []
    for v in W:
        e = end(v)
        tgt = [t for t in W if omega(e, t, n) == 2
               and not [1 for o in range(1, 2)
                        if len(set((e + t[n - 2:])[o:o + n])) == n]]
        tau_is_cleanE.append(tgt == [tau(v)])
    orbit_sizes = Counter(sum(1 for i in range(len(W)) if ORB[i] == q)
                          for q in range(nq))
    tau_cycles_the_orbit = True
    for q in range(nq):
        mem = [i for i in range(len(W)) if ORB[i] == q]
        x = W[mem[0]]
        seen = []
        for _ in range(len(mem)):
            seen.append(x)
            x = tau(x)
        if x != W[mem[0]] or len(set(seen)) != len(mem):
            tau_cycles_the_orbit = False
            break

    out = dict(
        n=n, words=len(W), hexagons=nh, orbits=nq,
        lemma0_unique_gap1_target_is_v=gap1_unique_and_self,
        lemmaE_clean_w2_target_is_tau=all(tau_is_cleanE),
        orbit_sizes=dict(orbit_sizes),
        tau_restricted_to_an_orbit_is_a_full_cycle=tau_cycles_the_orbit,
        conclusion=dict(
            every_component_is_a_directed_cycle="beta = T . alpha^-1 is a "
                "permutation, so in-degree = out-degree = 1 everywhere",
            minimum_component_length=2,
            pure_cleanE_component_length=n - 1,
            number_of_topologies="one per length; a directed cycle, nothing "
                                 "else is available"))
    out["ok"] = (gap1_unique_and_self and all(tau_is_cleanE)
                 and set(orbit_sizes) == {n - 1} and tau_cycles_the_orbit)
    (ROOT / "r154" / "certs" / "lemmas_154.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
