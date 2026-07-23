# F=1, H=0, N=0 obstruction analysis

Status: read-only checkpoint analysis, not a new enumeration and not a nonexistence proof.

## Snapshot

- input snapshot SHA-256: `5fc78a33465b86131ac99d8851bfd7cb827318eba8ee12575c100b43bacced8a`
- retained frontier states: 77932
- retained terminal certificates: 142
- analysed deepest frontier representatives: 200
- analysed F=1 descendant-support representatives: 200

`descendant_support` counts saved frontier/terminal paths through an accepted macro-path prefix. It is not a count of ungenerated descendants.

## Terminal obstruction archetypes

| archetype | terminals | immediate safe N=0 tail condition |
|---|---:|---|
| `C_capacity_gate_without_literal_collision` | 76 | `0 safe tails` |
| `E_mixed_revisit_closure` | 43 | `0 safe tails` |
| `A_N_credit_escape` | 23 | `0 safe tails` |

## Candidate statements and counterexample search

The following are observational tests on this snapshot only. A zero counterexample count is not a theorem.

```json
{
  "repair_before_C4_closure": {
    "operational_test": "fragment reaches its stored noncurrent hex within <=3 safe N=0 macro steps before or at the repeated rot^5;w3:210 diagnostic length",
    "counterexample_count_among_analysed_records": 3,
    "counterexample_samples": [
      {
        "canonical_state_hash": "7614f650ccea99dd357d39cac2dfeefc7a694fd4cadbc77b843b8cf7bd644012",
        "coordinate": [
          10,
          1,
          5,
          0,
          6,
          20,
          0
        ],
        "path": [
          {
            "joint": "w2:10",
            "literal_labels": [
              "w2:10"
            ],
            "rotation_length": 0,
            "rotation_stopped_by_collision": false
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:201",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:201"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:210",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:210"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:201",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:201"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:201",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:201"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          }
        ]
      },
      {
        "canonical_state_hash": "b7289603e7e00ab567405fc7d7232a6381b2d8524e0a75bc6bf296a3d85d65c0",
        "coordinate": [
          10,
          1,
          3,
          0,
          4,
          10,
          0
        ],
        "path": [
          {
            "joint": "w2:10",
            "literal_labels": [
              "w2:10"
            ],
            "rotation_length": 0,
            "rotation_stopped_by_collision": false
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:201",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:201"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:201",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:201"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          }
        ]
      },
      {
        "canonical_state_hash": "856c9785cc55405e181bdf8c7c1fc11d3972f01dbffcb6800d889e0581c9dfd2",
        "coordinate": [
          10,
          1,
          3,
          0,
          4,
          10,
          0
        ],
        "path": [
          {
            "joint": "w2:10",
            "literal_labels": [
              "w2:10"
            ],
            "rotation_length": 0,
            "rotation_stopped_by_collision": false
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:201",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:201"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w3:210",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w3:210"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          },
          {
            "joint": "w2:10",
            "literal_labels": [
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w1:0",
              "w2:10"
            ],
            "rotation_length": 5,
            "rotation_stopped_by_collision": true
          }
        ]
      }
    ],
    "status": "counterexample search only; the C4 diagnostic is outside G2 unless its full-cassette hypotheses are separately proved"
  },
  "terminal_requires_new_E_orbit": {
    "terminal_count_with_new_orbits_needed_zero": 0,
    "counterexample_samples": [],
    "status": "zero would support a conjecture, not prove it"
  },
  "terminal_N_credit_event": {
    "terminals_with_at_least_one_immediate_N_exceeded_candidate": 142,
    "terminal_count": 142,
    "N1_safe_escape_terminal_count": 23,
    "N_exceeded_signature_histogram": {
      "w=3;rot=0;new_orbit=False;abandonment=False": 46,
      "w=3;rot=1;new_orbit=False;abandonment=False": 28,
      "w=3;rot=2;new_orbit=False;abandonment=False": 25,
      "w=3;rot=3;new_orbit=False;abandonment=False": 20,
      "w=3;rot=5;new_orbit=False;abandonment=False": 25
    },
    "interpretation": "An N=1-producing candidate is universal in this snapshot; only the N1-safe subset is a genuine immediate escape. The rest remain blocked by other safe necessary conditions."
  },
  "last_w3_tails_have_one_collision_type": {
    "terminal_w3_option_status_histogram": {
      "collision:fragment_hex": 20,
      "collision:full_hex": 60,
      "pruned": 142
    },
    "status": "more than one nonzero key is an explicit counterexample to a single-type formulation"
  },
  "fragment_after_m_full_cassettes": {
    "observed_terminal_histogram": {
      "3": 13,
      "4": 65,
      "5": 8,
      "6": 39,
      "7": 17
    },
    "observed_maximum": 7,
    "status": "observed bound only; no bound is asserted as a theorem"
  },
  "terminal_safe_N0_dead_horizon": {
    "histogram": {
      "1": 142
    },
    "fragment_distance_histogram": {
      ">3_or_dead": 23,
      "None": 119
    },
    "status": "bounded to three macro steps"
  }
}
```

## Structural reading of this snapshot

1. **Every one of the 142 retained terminals has an immediate `N_exceeded_monotone` candidate.**  Its observed signatures are all non-abandoning, non-new-orbit weight-3 tails: `{'w=3;rot=0;new_orbit=False;abandonment=False': 46, 'w=3;rot=1;new_orbit=False;abandonment=False': 28, 'w=3;rot=2;new_orbit=False;abandonment=False': 25, 'w=3;rot=3;new_orbit=False;abandonment=False': 20, 'w=3;rot=5;new_orbit=False;abandonment=False': 25}`.  Thus its local accounting is `ΔN=1+0−0=1`.
   Only 23 terminals acquire a genuinely safe child when the bound is relaxed to `N<=1`; the others are still rejected by a coverage or F-budget condition.  This is the strongest current theorem *candidate*, not a theorem.
2. The terminal families are not a single collision mechanism.  76 terminals have no immediate literal collision at all; 43 have a mixed revisit closure; and 23 have an N=1-safe escape.
3. The deepest frontier sample is **not** already terminal-like: 198/200 survive the bounded three-step N=0 diagnostic and 132/200 admit four repetitions of the operational `rot^5;w3:210` test.  The high-descendant sample is still less terminal-like: 200/200 survive three steps and 182/200 have diagnostic C4 length four.
4. No retained terminal has `O=25`: its remaining E-orbit requirement ranges over `{17: 47, 18: 41, 19: 42, 20: 11, 22: 1}`.  This does **not** prove that an orbit-opening failure is universal, but it rules out a terminal explanation based on already having met the 25-orbit target.
5. Two tempting uniform statements already fail in this snapshot: repair can be reached before the operational C4 diagnostic in 3 analysed states, and weight-3 rejections split between full-hex and fragment-hex collisions rather than one target type.  The observed terminal maximum of post-fragment `rot^5` runs is 7; it is not a proof of any finite bound.

## Next proof target

The data points to a narrowly stated local lemma to try next: a terminal N=0 prefix has an available non-abandoning weight-3 re-entry into an already opened E-orbit, hence `ΔN=1`.  To turn this from a snapshot fact into a theorem, classify the terminal mask normal forms and prove that the other local tails are blocked by the listed collision/F/capacity alternatives.  Do not replace that proof by the observed C4 diagnostic.

## Machine-readable details

All selected representatives, terminal summaries, collision causes, bounded three-step diagnostics, and paths are in the companion JSON file.
