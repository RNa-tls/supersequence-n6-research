# Round Q record word (n = 8)

`superperm8_46183.txt` is an r = 0 superpermutation of `12345678` of length **46183**: every one of the 40320
permutations occurs as a window of length 8.  Previous best: 46184 (`rP/records/superperm8_46184.txt`).

| file | length | sha256 (prefix) | q | J | G | pieces | visits |
|---|---|---|---|---|---|---|---|
| `superperm8_46183.txt` | 46183 | b4d07ecd6357 | 781 | 98 | 21 | 31 | 31 |
| `superperm8_46183_b.txt` | 46183 | 47af755bfbcb | 781 | 98 | 21 | 31 | 31 |

It is a **multi-opening** word of the 6A + 24φ closed-trail family: 29 trails are opened once, and A trail 22 is cut
into two pieces (a single split).  Route (trail ids, in word order; `22` occurs twice):

    3 5 27 21 19 17 29 7 6 4 1 0 | 22 | 8 11 12 13 | 22 | 14 15 28 18 10 9 20 16 2 26 23 24 25

* the two pieces of trail 22 (version 0) are runs 213 .. 15 (475 runs, cyclically) and runs 16 .. 212 (197 runs);
* word `_b` has trail 28 right after 27 instead of after 15; its 26-trail path is exactly the trail order of the Round P word a
  (`rP/records/superperm8_46184.txt`) with trail 8 and the block 11 12 13 deleted, and those four trails sit in the bracket;
* in the virtual-cover picture (report §6.2) this is the path P (26 vertices) plus the cycle
  Z = (22 at run 16, 8, 11, 12, 13); G = 1 + (path cost 19) + (cycle cost 1) = 21, J = 77 + G = 98,
  length = 46085 + J = 46183.

**How to verify** (each check is independent of the search code):

    python3 rI/src/minicheck.py rQ/records/superperm8_46183.txt
    python3 rI/src/r0verifyA.py rQ/records/superperm8_46183.txt
    python3 rI/src/r0verifyB.py rQ/records/superperm8_46183.txt
    python3 rM/src/verify_r0_independent.py rQ/records/superperm8_46183.txt
    gcc -O2 -o permcheck rQ/csrc/permcheck.c && ./permcheck rQ/records/superperm8_46183.txt
    sha256sum -c rQ/records/superperm8_46183.sha256          (run inside rQ/records)
    python3 rQ/src/word_pieces.py rQ/records/superperm8_46183.txt rM/certs/family_46187.json

**Rebuild from the route parameters** (exact DP over all other options, independent of the search):

    python3 rQ/src/split_witness.py rM/certs/family_46187.json \
        3,5,27,21,19,17,29,7,6,4,1,0,22,14,15,28,18,10,9,20,16,2,26,23,24,25,8,11,12,13 26 12 16 OUT.txt

**Symmetry orbits.** The order-12 symmetry group of the family maps every version cycle onto a version cycle with the
cyclic order preserved; the 12 images of each word are 12 distinct valid words of length 46183 (6 distinct trail orders,
each with two option choices), and the two orbits are disjoint (24 words).  `rQ/src/orbit_words.py` rebuilds and checks
them; hashes in `rQ/certs/orbit_46183.json` and `rQ/certs/orbit_46183_b.json`.

**Exhaustiveness.** Among all single splits (one trail cut into two pieces, every other trail one piece) the least G is 21,
attained exactly by the 12 configurations of these two orbits (`rQ/certs/single_split_exact_thr20.json`).

Rebuild of `_b`: `python3 rQ/src/split_witness.py rM/certs/family_46187.json 3,5,27,28,21,19,17,29,7,6,4,1,0,22,14,15,18,10,9,20,16,2,26,23,24,25,8,11,12,13 26 13 16 OUT.txt`.

Earlier Round Q interim files: the two files `multiopen_46184_excision_*.txt` of the interim commit were single-opening
words (degenerate excision moves) and were removed; the genuine 32-piece 46184 words are `multiopen_46184_E4_*.txt`.
`multiopen_46185_split_A22.txt` is a 31-piece single split of length 46185.
