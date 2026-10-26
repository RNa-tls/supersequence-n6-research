# P = 32, V = 32 certificate (Round R, section 2)

Claim: no route of the 6A + 24phi multi-opening family with P = 32 pieces and V = 32 visits has G <= 20
(length <= 46182).

* c = 0 (genus 1, crossing): detour lemmas L1/L2 (`rR/certs/detour_lemmas_L1_L2.txt`, two implementations) and the
  Lean chain lemma `detour` (`rR/lean/BracketTree.lean`) remove both extra cuts without increasing G, so G >= 22
  (single-opening optimum, Round P).
* c = 2 (genus 0, bracket trees: siblings, two cycles on one trail, nested): relaxed tables `ckM2.c`, threshold-20
  search `ckM2_search.c`, exact evaluation `ckM_eval.c` of every emitted pattern.  Files here:
  * `ckM2_build.log` -- table build (root 16);
  * `search_thr20.json`, `search_thr20.log` -- forward search and pattern emission (symmetry closure check);
  * `eval_thr20_summary.json` -- exact evaluation of all patterns (sum over chunks);
  * `patterns_sha256.txt` -- sha256 of the concatenated pattern file (not stored: size);
  * `traces.txt` -- completeness traces;
  * `planted_mutation.txt` -- planted G = 20 configurations (c = 1 and c = 2) found by the mutated pipeline.

Reproduction (scratchpad paths as in the logs):

    ckM2 DIR(runs.bin, group.bin) OUT                                   # 41 min, 15 GB
    ckM2_search DIR HKEYDIR(ckB H??.key) OUT 20 s20.json               # patterns in s20.json.patterns.NN
    ckM_eval DIR PATTERNS 20 OUT.json WIT.jsonl                         # per chunk

Note on trace runs: in trace mode (env CKM_TRACE) the search keeps only the states of one configuration, so the
symmetry closure check necessarily reports missing images ("FAILED ... expanding every final state"); trace mode
never uses the symmetry reduction (it expands its single final state).  The check is meaningful only for full runs,
where it passed (search_thr20.json: symmetry_closure_images_missing = 0).
