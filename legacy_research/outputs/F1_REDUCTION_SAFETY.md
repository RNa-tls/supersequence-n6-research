# Partial-F=1 reduction safety audit

Status: read-only bounded-checkpoint audit.  It neither proves a new
prune nor starts an enumeration.

## Proven reduction boundary

For every ordered permutation word `p`, a value relabelling `alpha`
that fixes `p` fixes all six values, hence `alpha=id`.  Therefore an
exact state retaining `p` has trivial residual left-`S_6` stabilizer.
The existing full left-`S_6` canonicalization is already the complete
value-relabel quotient; no additional stabilizer quotient is available
without discarding part of the exact state.

## Dominance boundary

A raw relation `V(x) subset V(y)` is not a completion-preserving
dominance relation by itself.  A completion suffix from `y` leaves
`V(y)\V(x)` unvisited when replayed from `x`; a completion suffix from
`x` may collide with that same difference when replayed from `y`.
Thus a safe prune requires an additional extension simulation or a
coverage certificate, neither of which is supplied by mask inclusion.

## Bounded observations

- checkpoint frontier states: 980
- canonical states whose terminal word is the common representative: 980
- weak local-fingerprint classes with multiple global states: 66
- sampled equal-local pairs with different legal macro-tail sets: 11
- same `(p,B,F,S,H)` groups containing a strict visited-mask inclusion: 0

These are counterexamples to omitting global occupancy from the exact
transition state; they are not a claim that no stronger proved quotient
can ever exist.

## Safe conclusion

Do not install visited-mask inclusion as a prune.  The only currently
proved symmetry reduction is canonical-child quotienting by the full
left `S_6` action already implemented in the exact engine.

```json
{
  "code_sha256": {
    "analysis": "008323dbd12053f3d9d915ef11b567575ce5ac8fc74ac79dcd32c2065bd8facc",
    "core": "18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60",
    "engine": "9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8",
    "macro": "b02d3985d3672c24efdc197777cc25080fc9cb3846545db240ceacd649485049"
  },
  "different_legal_tail_samples": [
    {
      "first_hash": "39751565ede4d49b8d56e9afeb98dd0badf008e68bbeb19c600ad4c4099084ca",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [
        "r3:w3:210"
      ],
      "other_hash": "b3f405bc387e640dfba371d8cb1bdc24308264ca6656f59d7739ac9f3ddbeede",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [
        "r3:w3:120"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 0, (1, 8), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "41174ec2bd4f24de0f3440af11a0d0e38c8de153b3574b6d464c84034f303e9f",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [
        "r0:w3:201"
      ],
      "other_hash": "a4a8ea569cb804511eafe29cc20eceed3c1f4a3b11ed164e46a6b68c1bf44404",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 1, (1, 4), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "d3f4e52c70f2ad52d7555fb604a64e2f353138c18444e4cddb53c5e1ae506ffc",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [
        "r4:w3:201"
      ],
      "other_hash": "eb0995fde2f2b07a9b2aa17faafbdd2011b79a5054aa83eadb48f09b85b90dc4",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 2, (1, 2), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "506e4d60b8488a9967b8522d4948d85080a154568e08038a5bc04627f140ba2a",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [
        "r3:w2:10"
      ],
      "other_hash": "ccb4870b044414c694819cc1d472774c8d1590826d8f1169e1b20a7ef58f3ba6",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [
        "r3:w3:201"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 3, (1, 1), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "e4ebb9fbbdf624a50f78539d7690b5459e2637b1a237411bd7a0936bc12504a9",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:210"
      ],
      "first_only": [],
      "other_hash": "dc26e5ef062e4f115558c041737ae3337b0301f7f06bae8249c49c9e3837893a",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [
        "r5:w3:201"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 3, (1, 16), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "b478b3a843b10a01efdfc0ad17ba45c110975c33141b68fb5fbbf0cca621dc4f",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [
        "r1:w3:120"
      ],
      "other_hash": "4736b7bd4c67e85ab854ef62eef9d0272f5fa099f63f67937cd95432ee59db5f",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 3, (1, 8), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "afd1c01846f4d3af64eadfb316d6edafb1616d6b625cda3ee4dd68ca25de638b",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [],
      "other_hash": "52518149f96b3a6326ce6d1a0fcb7cff291afa9e508609fd936abb5facf24497",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [
        "r4:w3:120"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 3, (1, 4), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "eae3ce3da28b94604b97a833469bced8685951adda82a2aacb3245d04ac32876",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "first_only": [
        "r3:w2:10"
      ],
      "other_hash": "caf334bc8b7ac2101c53fc01aaeceecc88a9fe927af3fe108d0af7bf4dfdc6d2",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210",
        "r5:w2:10",
        "r5:w3:120",
        "r5:w3:201",
        "r5:w3:210"
      ],
      "other_only": [
        "r4:w2:10"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 0, 2, 3, (1, 2), ((0, 0, 1),), (), True, False)"
    },
    {
      "first_hash": "9f5bf13f93c587a80898a3f91a674a808bd1b729c7c570a6ea966cfc43672b8b",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210"
      ],
      "first_only": [
        "r2:w3:120"
      ],
      "other_hash": "5017e6fd81c798cc8cba3e6ac4effedf4e4bd8cd2d2f6e3e20ddc7a770ca4db9",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210"
      ],
      "other_only": [
        "r2:w3:201"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 1, 2, 0, (16, 8), ((5, 0, 2),), ((4, 2, 5),), False, False)"
    },
    {
      "first_hash": "a9a1175c312dab70f4b1510c57ef7fefbe2ca201a2fc15f4bd16c446d653e7f1",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210"
      ],
      "first_only": [
        "r3:w3:201"
      ],
      "other_hash": "d60a48247bb4cce502d1808f5db9c9fe32c7f31c00bbf0d0459ae3cf1c5bd8f8",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:210",
        "r4:w2:10",
        "r4:w3:120",
        "r4:w3:201",
        "r4:w3:210"
      ],
      "other_only": [],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 1, 2, 2, (16, 1), ((5, 0, 2),), ((0, 4, 5),), False, False)"
    },
    {
      "first_hash": "d0e90a48a502c8bd4151a57bb0b5065ff01de81c6bffead52b35d57ef40cc9ef",
      "first_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:120",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210"
      ],
      "first_only": [
        "r1:w3:120"
      ],
      "other_hash": "5684bcc0305c0703ade1c3bd6a4fe39375b062ab24c42dfb0a0d0d0415d58c6c",
      "other_legal_macro_tails": [
        "r0:w2:10",
        "r0:w3:120",
        "r0:w3:201",
        "r0:w3:210",
        "r1:w2:10",
        "r1:w3:201",
        "r1:w3:210",
        "r2:w2:10",
        "r2:w3:120",
        "r2:w3:201",
        "r2:w3:210",
        "r3:w2:10",
        "r3:w3:120",
        "r3:w3:201",
        "r3:w3:210"
      ],
      "other_only": [
        "r1:w3:201"
      ],
      "weak_local_fingerprint": "((0, 1, 2, 3, 4, 5), 1, 2, 0, (8, 8), ((4, 0, 3),), ((4, 1, 4),), False, False)"
    }
  ],
  "input": {
    "path": "outputs\\f1_profile_depth6.checkpoint.json",
    "sha256": "3fcfd43b22d77aa99c4cf92d44a58b50a1e4553af40b08b2a5393677935d6eb2"
  },
  "limitations": "Absence of a pair in this bounded checkpoint would not prove a dominance rule. No relation from this audit is used by the search engine.",
  "observations": {
    "common_terminal_word_count": 980,
    "different_tail_set_pairs_found": 11,
    "distinct_terminal_words_after_canonicalization": 1,
    "frontier_canonicality": "not recomputed here; the checkpoint was emitted by canonical-child search and this audit avoids 720-image re-canonicalization while the unbounded search is live",
    "frontier_states": 980,
    "strict_inclusion_pairs_found": 0,
    "weak_fingerprint_classes": 87,
    "weak_fingerprint_multi_state_classes": 66
  },
  "proofs": {
    "left_S6_residual_stabilizer": "trivial: alpha(p_i)=p_i for all six distinct entries of p forces alpha=id",
    "mask_inclusion_not_a_standalone_dominance": "a completion suffix cannot be transferred in either direction without either leaving V(y)\\V(x) uncovered or colliding with it"
  },
  "schema": "partial-f1-reduction-safety-audit-v1",
  "scope": "read-only bounded checkpoint; no new search and no installed pruning",
  "strict_mask_inclusion_samples": []
}
```
