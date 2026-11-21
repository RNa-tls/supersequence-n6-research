# Round Ω certificates

* no prefix: exact computation (exhaustive over the stated domain) or proof support.
* `HYPOTHETICAL_*`: knapsack runs with statements that are NOT proved (strength measurements only; they remove no cell).
* `coexistence/`: two-threshold coexistence tables (`compat_*.json`, tool `rOmega/src/compat2d.py` for one base list,
  `rOmega/src/compat_cross.py` for a cross list), the cross placement lists they refine (`*_pairs_disjoint_z.txt`, tool
  `rZ/csrc/disjoint_z.c` LIST=1, X at the identity; columns: nameX nameY same same_rev cross cross_rev | o:image_of_8:rank),
  and `independent_checks/` (direct pair-by-pair judgments by Round X `rX/csrc/disjoint_bits.c`: pair count, placement count,
  sha256 of the full output, lines with placements).  The base lists of the refinement are Round Z certificates
  (`rZ/certs/coexistence/line2_theta200_pairs_disjoint_z.txt.gz`, `line1_theta45_pairs_disjoint_z.txt`).
* `frontier/`: levelled knapsack results (`rOmega/src/frontier_compat.py`, implementation A) and their second
  implementation (`rOmega/src/frontier_compat_enum.py`, `*_second_implementation.json`), the configurations (`config_*.json`;
  table paths point to a scratch directory, the tables themselves are identified by `tables_sha256.txt`), the final result
  `frontier27_final.json` (+ markdown table), intermediate stages (30, 29, 28, 27 without cross tables), the reproduction of
  Round Z's 34 cells, and `strength/` (HYPOTHETICAL long-chain caps).
* `firstpassage/`: summary lines of the first-passage dumps of this round (visited/kept = Halfar) and sha256 of the lists.
* `counting/`: the counting relaxation for (769, 0, 0): Round Z's model with the HiGHS repeated-index defect fixed, and the
  segment-capped model (both feasible; solutions are relaxation solutions, not covers).
* `words/`: the dictionary between the upper-bound (Q, J) and lower-bound (R, N, Δ, W, M) languages for the three 46173 words.
* `lean_axioms_RoundOmega.txt`: output of `lean rOmega/lean/RoundOmega.lean` (exit 0, no sorry, no user axioms).
