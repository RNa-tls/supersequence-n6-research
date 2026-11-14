# Round Y certificates

File prefixes mark the kind of evidence:

* no prefix: exact computation (exhaustive over the stated domain) or a proof artefact (Lean axioms).
* `hyp_`: knapsack runs with a HYPOTHETICAL extra constraint (not a theorem). They measure how strong a missing
  statement would have to be; no cell is counted as removed because of them.
* `observation_`: heuristic, non-exhaustive searches. Not proofs.

`python3 rY/src/cert_hashes.py` lists the sha256 of every file here.
