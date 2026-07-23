# N=1 escapes from N=0 terminals

Status: limited experiment on immutable N=0 terminal certificates; not an N=1 enumeration.

## Summary

- terminal certificates read: 142
- N=1 escape roots: 25
- bounded macro-node cap: 50000
- depth: 3

## Defect archetypes

- `{"component_relation": "same", "fragment_relation": "different_or_unresolved", "phase_before": 1, "rotation_length": 5, "type": "R_blocked_w3_existing", "weight": 3}`: 21 roots; survivors at depth 1/2/3 aggregated as [63, 168, 444].
- `{"component_relation": "different_or_unresolved", "fragment_relation": "different_or_unresolved", "phase_before": 16, "rotation_length": 5, "type": "R_blocked_w3_existing", "weight": 3}`: 1 roots; survivors at depth 1/2/3 aggregated as [3, 9, 24].
- `{"component_relation": "same", "fragment_relation": "different_or_unresolved", "phase_before": 17, "rotation_length": 5, "type": "R_blocked_w3_existing", "weight": 3}`: 2 roots; survivors at depth 1/2/3 aggregated as [4, 10, 28].
- `{"component_relation": "different_or_unresolved", "fragment_relation": "different_or_unresolved", "phase_before": 4, "rotation_length": 5, "type": "R_blocked_w3_existing", "weight": 3}`: 1 roots; survivors at depth 1/2/3 aggregated as [2, 6, 16].

## Bounded findings

All recorded escapes are `R_blocked_w3_existing`; the other two
proved defect normal forms do not occur in this particular N=0-terminal
sample.  Every escape survives three bounded N<=1 macro steps.  This is
a restricted observation, not evidence for an N=1 completion.

Candidate A and B are proved algebraically by the one-defect lemma.
Candidate C is not tested by a complete repair predicate, and candidate
D needs a paired exact N=0/N=1 capacity comparison; neither is promoted
to a theorem.

All component and split-hexagon relations below refer only to the current partial port-incidence graph, not to a completed skeleton.

```json
{
  "bounded_experiment": {
    "cap_hit": false,
    "depth": 3,
    "generated_nodes": 777,
    "node_cap": 50000
  },
  "candidate_lemmas": {
    "A_one_defect_allows_one_N_increasing_revisit": {
      "reason": "Delta N is nonnegative and final N=1, so a second DeltaN=1 joint is impossible",
      "status": "proved for an N<=1 trajectory"
    },
    "B_after_defect_all_other_joints_follow_zero_defect_flow": {
      "reason": "the one-defect theorem leaves every other joint with DeltaN=0",
      "status": "proved"
    },
    "C_split_repair_consumes_defect": {
      "counterexamples": null,
      "definition": "defect target equals the currently observable noncurrent fragment hexagon",
      "observable_fragment_states": 25,
      "reason": "same-hex incidence is not a complete definition of repair; no theorem follows",
      "same_hex_count": 0,
      "states_checked": 25,
      "status": "limited experiment"
    },
    "D_one_defect_bypasses_at_most_one_capacity_gate": {
      "definition": "requires a paired exact N=0/N=1 continuation comparison, not supplied by a local tail",
      "immediate_N2_prunes_after_defect": 24,
      "reason": "capacity is a global exact-mask condition; only bounded observations are available",
      "states_checked": 25,
      "status": "not determined"
    }
  },
  "code_sha256": {
    "analysis": "1d9baf7240c89ab07f5c3ec59e62a7b624973a4f30603a66df435cb5f5715722",
    "core": "18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60",
    "engine": "9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8",
    "macro": "b02d3985d3672c24efdc197777cc25080fc9cb3846545db240ceacd649485049"
  },
  "distinct_terminal_states_with_escape": 23,
  "escape_archetypes": {
    "{\"component_relation\": \"different_or_unresolved\", \"fragment_relation\": \"different_or_unresolved\", \"phase_before\": 16, \"rotation_length\": 5, \"type\": \"R_blocked_w3_existing\", \"weight\": 3}": {
      "aggregate_survivors_by_depth": [
        3,
        9,
        24
      ],
      "count": 1,
      "minimum_representative": "86abf802890ccbf5b297fdab3012f1ca9c5287fe64a56b1a0375d70ca6d02ebc"
    },
    "{\"component_relation\": \"different_or_unresolved\", \"fragment_relation\": \"different_or_unresolved\", \"phase_before\": 4, \"rotation_length\": 5, \"type\": \"R_blocked_w3_existing\", \"weight\": 3}": {
      "aggregate_survivors_by_depth": [
        2,
        6,
        16
      ],
      "count": 1,
      "minimum_representative": "9e4f7b35d7b336abe887e070b3189959ce7e0cc0567436079ad358c7dc721887"
    },
    "{\"component_relation\": \"same\", \"fragment_relation\": \"different_or_unresolved\", \"phase_before\": 1, \"rotation_length\": 5, \"type\": \"R_blocked_w3_existing\", \"weight\": 3}": {
      "aggregate_survivors_by_depth": [
        63,
        168,
        444
      ],
      "count": 21,
      "minimum_representative": "3fd6af794c8b932ad656bd3a6dacc9ef8617f16f9fc47cbd8ec68fca4eb6f8d8"
    },
    "{\"component_relation\": \"same\", \"fragment_relation\": \"different_or_unresolved\", \"phase_before\": 17, \"rotation_length\": 5, \"type\": \"R_blocked_w3_existing\", \"weight\": 3}": {
      "aggregate_survivors_by_depth": [
        4,
        10,
        28
      ],
      "count": 2,
      "minimum_representative": "855b0cc200c0df1eb3dabda75fe30b63fbf5fd9a4f7dac7ab285e2283798e8a0"
    }
  },
  "escape_root_count": 25,
  "escape_roots": [
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          22
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "3fd6af794c8b932ad656bd3a6dacc9ef8617f16f9fc47cbd8ec68fca4eb6f8d8",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        7,
        1,
        6,
        0,
        6,
        23,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        6,
        1,
        5,
        0,
        6,
        24,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          1,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "12eddd546c64a8fdadf5a7291b121c1115cb52b27e412b752d02b666eef9c779",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        8,
        1,
        6,
        0,
        6,
        22,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            24
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        7,
        1,
        5,
        0,
        6,
        23,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            24
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          22
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "1eaf8a7958ffed3a0805c5d7367b62da31d5954f95f6e4ffc6580a7755204702",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        8,
        1,
        7,
        0,
        7,
        27,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            1
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        7,
        1,
        6,
        0,
        7,
        28,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            1
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          2
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "a919afc24f34a0ab83173919fefc1e07c918b97309492dbbcf1c50663dca55a8",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        8,
        1,
        7,
        0,
        7,
        27,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
          "joint": "w2:10",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        7,
        1,
        6,
        0,
        7,
        28,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          1,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "86abf802890ccbf5b297fdab3012f1ca9c5287fe64a56b1a0375d70ca6d02ebc",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        6,
        0,
        6,
        21,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 33,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            28
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
        {
          "joint": "w2:10",
          "literal_labels": [
            "w1:0",
            "w2:10"
          ],
          "rotation_length": 1,
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
      ],
      "terminal_coordinate": [
        8,
        1,
        5,
        0,
        6,
        22,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 33,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            28
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          3,
          3,
          3,
          2,
          3,
          3,
          3,
          1,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          9,
          24
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "86abf802890ccbf5b297fdab3012f1ca9c5287fe64a56b1a0375d70ca6d02ebc",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "different_or_unresolved",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 105,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 32,
        "target_phase": 1,
        "target_phase_mask_after": 18,
        "target_phase_mask_before": 16,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        6,
        0,
        6,
        21,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            2,
            2,
            1
          ]
        ],
        "current_hex": 105,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 33,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            18
          ],
          [
            77,
            2
          ],
          [
            120,
            28
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
        {
          "joint": "w2:10",
          "literal_labels": [
            "w1:0",
            "w2:10"
          ],
          "rotation_length": 1,
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
      ],
      "terminal_coordinate": [
        8,
        1,
        5,
        0,
        6,
        22,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 33,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            28
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          1,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "243826207283d68af0fe045367f4e70303ba427bde86498c798d42f49b555956",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        6,
        0,
        6,
        21,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            28
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        5,
        0,
        6,
        22,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            28
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          22
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "a0de4928490fa40c3c7ed1035863ed1a5d7062862c64ffe0a8d152f19efc937e",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        7,
        0,
        7,
        26,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            17
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        6,
        0,
        7,
        27,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            17
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          2
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "875466f84be322c091e0bc844d647fbd86802c21386af928487e3dd521cbda6a",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        7,
        0,
        7,
        26,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            6
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
          "joint": "w2:10",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        6,
        0,
        7,
        27,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            6
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          2,
          2,
          3,
          3,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          2,
          5,
          15
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "855b0cc200c0df1eb3dabda75fe30b63fbf5fd9a4f7dac7ab285e2283798e8a0",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 21,
        "target_phase_mask_before": 17,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        5,
        0,
        5,
        16,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            21
          ],
          [
            19,
            6
          ],
          [
            32,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            12
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 15,
        "safe": 2
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        4,
        0,
        5,
        17,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            17
          ],
          [
            19,
            6
          ],
          [
            32,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            12
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          2,
          3,
          2
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          20
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "7272c1e2328045ca69cd9a1430c25ea39b32ae6578126251b43f4ef68d4a54dc",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            2,
            8
          ],
          [
            26,
            2
          ],
          [
            32,
            2
          ],
          [
            120,
            16
          ],
          [
            137,
            4
          ],
          [
            138,
            4
          ],
          [
            140,
            16
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            2,
            8
          ],
          [
            26,
            2
          ],
          [
            32,
            2
          ],
          [
            120,
            16
          ],
          [
            137,
            4
          ],
          [
            138,
            4
          ],
          [
            140,
            16
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          22
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "e5c4623ea7b15bd5763792102a1ee4e8af94fd8b273a908813c4fe9775a8545e",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        7,
        0,
        7,
        26,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            4,
            0,
            3
          ]
        ],
        "fragment_hex": 90,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            77,
            2
          ],
          [
            93,
            12
          ],
          [
            104,
            16
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 15,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 2,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        6,
        0,
        7,
        27,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            4,
            0,
            3
          ]
        ],
        "fragment_hex": 90,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            77,
            2
          ],
          [
            93,
            12
          ],
          [
            104,
            16
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          1,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "bc8578db124ad98919e0b329a48a00c6a0e00f458b0bf6731e7f093ac6ccd6c2",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        7,
        0,
        7,
        26,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            40,
            1
          ],
          [
            77,
            2
          ],
          [
            120,
            24
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        6,
        0,
        7,
        27,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            40,
            1
          ],
          [
            77,
            2
          ],
          [
            120,
            24
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          2,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "7eb2bb3afa7475fbecfab5722c89c975fc813657cac390f885fb0cb8655d2983",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            1
          ],
          [
            70,
            8
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            1
          ],
          [
            70,
            8
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          2
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "b12798934e01bfe8a09eca8999c6f1ad1b065ecf3e468b4321160eaa00018173",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            15,
            1
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            15,
            1
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          2,
          3,
          2,
          3,
          3,
          3,
          2
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          20
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "9e4f7b35d7b336abe887e070b3189959ce7e0cc0567436079ad358c7dc721887",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 39,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            4
          ],
          [
            38,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 1,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 39,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            4
          ],
          [
            38,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          2,
          3,
          3,
          3,
          1,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          2,
          6,
          16
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "9e4f7b35d7b336abe887e070b3189959ce7e0cc0567436079ad358c7dc721887",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "different_or_unresolved",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 105,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 32,
        "target_phase": 1,
        "target_phase_mask_after": 6,
        "target_phase_mask_before": 4,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            2,
            2,
            1
          ]
        ],
        "current_hex": 105,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 39,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            6
          ],
          [
            38,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 2
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 1,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            5,
            0,
            2
          ]
        ],
        "fragment_hex": 39,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            4
          ],
          [
            38,
            16
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          22
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "6382b9a149c78d1c6c05b2706cae09f151f41e13d2b838ae7a301846ec261f24",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        6,
        0,
        6,
        21,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            2,
            12
          ],
          [
            32,
            6
          ],
          [
            38,
            16
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 15,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        5,
        0,
        6,
        22,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            2,
            12
          ],
          [
            32,
            6
          ],
          [
            38,
            16
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          2,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "1c06f623623f8743d15c4409f32c078c3d27a519cba54711a2757f40158f74bb",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            2,
            8
          ],
          [
            32,
            2
          ],
          [
            67,
            1
          ],
          [
            70,
            8
          ],
          [
            101,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 16,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            2,
            8
          ],
          [
            32,
            2
          ],
          [
            67,
            1
          ],
          [
            70,
            8
          ],
          [
            101,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          2,
          2,
          3,
          2,
          3,
          3,
          2,
          3
        ],
        "survivors_by_macro_depth": [
          2,
          5,
          13
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "14050b008d0d28e7670790ebd674d02b11e0f22ea596708e64ee4e549695ad0b",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 21,
        "target_phase_mask_before": 17,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        6,
        0,
        6,
        21,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            21
          ],
          [
            6,
            4
          ],
          [
            32,
            2
          ],
          [
            56,
            24
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 15,
        "pruned:N_exceeded_monotone": 1,
        "safe": 2
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        5,
        0,
        6,
        22,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            17
          ],
          [
            6,
            4
          ],
          [
            32,
            2
          ],
          [
            56,
            24
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          2,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "63c02c9ef135e0cafe564acb777165829fe42cb9fa011453bffcacc5ff95d22f",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            28,
            2
          ],
          [
            32,
            2
          ],
          [
            55,
            1
          ],
          [
            56,
            8
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 16,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            28,
            2
          ],
          [
            32,
            2
          ],
          [
            55,
            1
          ],
          [
            56,
            8
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          2,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "7f6f41fe262df7587319cdf5560424584661889e98c6331731c1428f133dd9cf",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            2,
            8
          ],
          [
            26,
            2
          ],
          [
            32,
            2
          ],
          [
            54,
            1
          ],
          [
            56,
            8
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 16,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
        }
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            1,
            5,
            5
          ]
        ],
        "fragment_hex": 32,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            2,
            8
          ],
          [
            26,
            2
          ],
          [
            32,
            2
          ],
          [
            54,
            1
          ],
          [
            56,
            8
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          1,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          21
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "695bf2bca8c58ce44ff8234664d91dd3f6bcd1845036353cc725f34191dd0018",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        7,
        0,
        7,
        26,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            24
          ],
          [
            126,
            2
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        6,
        0,
        7,
        27,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            24
          ],
          [
            126,
            2
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          3,
          3
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          22
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "6d547fa528801de158c2ea3ba5f9cae9c086ada2d68165a9dbd3f5c57a5389a6",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            1
          ],
          [
            68,
            8
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
        },
        {
          "joint": "w2:10",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            66,
            1
          ],
          [
            68,
            8
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    },
    {
      "N0_escape_class": "A_N_credit_escape (recomputed: terminal has an N=1-safe tail)",
      "bounded_continuation": {
        "safe_tail_counts_encountered": [
          3,
          2,
          3,
          3,
          2,
          3,
          3,
          1,
          3,
          3,
          3,
          2
        ],
        "survivors_by_macro_depth": [
          3,
          8,
          20
        ],
        "truncated_by_global_node_cap": false
      },
      "canonical_state_hash": "eade339f3d3dcd65afd564b1420250c2948727fc2d092a8fbf3f4fbb8a25b522",
      "defect": {
        "abandonment": false,
        "delta": {
          "D": -1,
          "F": 0,
          "N": 1,
          "O": 0,
          "S": 1
        },
        "fragment_hex_component_relation": "different_or_unresolved",
        "joint_type": "R_blocked_w3_existing",
        "new_orbit": false,
        "partial_port_component_relation": "same",
        "rotation_length": 5,
        "source_orbit": 0,
        "target_hexagon": 18,
        "target_is_observed_fragment_hex": false,
        "target_orbit": 0,
        "target_phase": 2,
        "target_phase_mask_after": 5,
        "target_phase_mask_before": 1,
        "weight": 3
      },
      "post_defect_coordinate": [
        9,
        1,
        8,
        0,
        8,
        31,
        1
      ],
      "post_defect_fragment": {
        "current_components": [
          [
            3,
            3,
            1
          ]
        ],
        "current_hex": 18,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            5
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            135,
            16
          ],
          [
            138,
            4
          ]
        ]
      },
      "post_defect_immediate_rejections": {
        "pruned:F_exceeded": 17,
        "pruned:N_exceeded_monotone": 1,
        "safe": 3
      },
      "representative_path": [
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
          "joint": "w2:10",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w2:10"
          ],
          "rotation_length": 4,
          "rotation_stopped_by_collision": false
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
      ],
      "terminal_coordinate": [
        8,
        1,
        7,
        0,
        8,
        32,
        0
      ],
      "terminal_fragment": {
        "current_components": [
          [
            0,
            0,
            1
          ]
        ],
        "current_hex": 0,
        "fragment_components": [
          [
            2,
            0,
            5
          ]
        ],
        "fragment_hex": 105,
        "fragment_is_current": false,
        "normal_form_valid": true,
        "orbit_phase_masks": [
          [
            0,
            1
          ],
          [
            4,
            8
          ],
          [
            32,
            2
          ],
          [
            77,
            2
          ],
          [
            120,
            16
          ],
          [
            122,
            4
          ],
          [
            135,
            16
          ],
          [
            138,
            4
          ]
        ]
      }
    }
  ],
  "input_checkpoint": {
    "path": "outputs\\f1_small_n0.committed_resume.checkpoint.5fc78a33465b861.backup.json",
    "sha256": "5fc78a33465b86131ac99d8851bfd7cb827318eba8ee12575c100b43bacced8a"
  },
  "limitations": "Partial component relations are computed from current pass-start ports, not a completed 25-orbit skeleton. Any missing relation is unresolved, not false.",
  "schema": "f1-n1-terminal-escape-analysis-v1",
  "scope": "read-only source checkpoint plus bounded N<=1 continuation; no N=1 exhaustive claim",
  "terminal_input_count": 142
}
```
