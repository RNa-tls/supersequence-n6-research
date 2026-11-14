# Round Z certificates

* no prefix: exact computation (exhaustive over the stated domain) or proof support.
* `HYPOTHETICAL_*`: knapsack runs with packing statements that are NOT proved (strength measurements only).
* `coexistence/`: disjoint-placement pair lists (`*_pairs_disjoint_z.txt`, tool `rZ/csrc/disjoint_z.c`; columns:
  nameX nameY same same_rev cross cross_rev | orientation:image_of_8:Lehmer_rank ...), second-implementation summaries
  (`rX/csrc/disjoint_bits.c`), triple tests (`rX/csrc/triple_test.c`; `*_second_implementation*`: union pseudo-chains
  + disjoint_z), and classifications.
* `firstpassage/`: summary lines of the first-passage dumps (visited/kept = Halfar) and sha256 of the lists.  The
  lists themselves (hundreds of MB) are rebuilt by `rZ/csrc/fpdump.c` + `rZ/src/fp_split.py`.
* `frontier/`: packing knapsack outputs (Round X `rX/src/frontier_packing.py`) with the Round Z tables, the table
  hashes, and the reconstructed optimal decompositions.
* `words/`: anatomy of the three known 46173 words.
* `priced_line_*`: line searches with a price on symbol changes (`rZ/csrc/dsearch_lab.c`).
* `block_configurations.json`: all arc covers of one {z,t}-block with at most three 2-cycles of one world.
