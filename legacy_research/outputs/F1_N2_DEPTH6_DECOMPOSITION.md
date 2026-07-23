# F=1,H=0,N=2 Area-A depth-six decomposition

Status: **finite complete replay of an existing bounded frontier only**.

~~~json
{
  "charge_two_single_event_paths": 230,
  "checkpoint": "C:\\Users\\parks\\Documents\\Codex\\2026-07-20\\a-n-ge-4-s-n\\outputs\\f1_macro_checkpoints\\A_F1_H0_Nle3_macro_depth6.checkpoint.json",
  "checkpoint_header": {
    "config": {
      "canonical_children": true,
      "max_macro_depth": 6,
      "memory_limit_bytes": 1073741824,
      "n_limit": 3,
      "name": "A_F1_H0_Nle3",
      "node_limit": 20000
    },
    "core_sha256": "18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60",
    "engine_sha256": "9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8",
    "macro_sha256": null
  },
  "checkpoint_sha256": "6b6f73d6751d48760150ff5c2aa10512e5a40aae59c6461e928520c0b4ebe3f8",
  "component_relation_counts": [
    {
      "count": 159,
      "relations": [
        "unresolved",
        "different"
      ],
      "word": "A3R"
    },
    {
      "count": 9,
      "relations": [
        "unresolved",
        "same"
      ],
      "word": "A3R"
    },
    {
      "count": 10816,
      "relations": [
        "unresolved",
        "unresolved"
      ],
      "word": "A3R"
    },
    {
      "count": 230,
      "relations": [
        "single_charge_two"
      ],
      "word": "J"
    },
    {
      "count": 1,
      "relations": [
        "unresolved",
        "different"
      ],
      "word": "RA2"
    },
    {
      "count": 23,
      "relations": [
        "unresolved",
        "unresolved"
      ],
      "word": "RA2"
    },
    {
      "count": 9952,
      "relations": [
        "unresolved",
        "unresolved"
      ],
      "word": "RA3"
    },
    {
      "count": 3,
      "relations": [
        "different",
        "same"
      ],
      "word": "RR"
    },
    {
      "count": 118,
      "relations": [
        "different",
        "unresolved"
      ],
      "word": "RR"
    },
    {
      "count": 172,
      "relations": [
        "unresolved",
        "different"
      ],
      "word": "RR"
    },
    {
      "count": 7,
      "relations": [
        "unresolved",
        "same"
      ],
      "word": "RR"
    },
    {
      "count": 4170,
      "relations": [
        "unresolved",
        "unresolved"
      ],
      "word": "RR"
    }
  ],
  "defect_macro_distance_counts": {
    "1": 7869,
    "2": 6234,
    "3": 4922,
    "4": 3688,
    "5": 2717
  },
  "deficit_phase_counts": {
    "(1, 2)": 290,
    "(1, 3)": 1,
    "(1, 3, 4)": 1376,
    "(1, 4, 4)": 119,
    "(1, 4, 4, 4)": 1098,
    "(2, 2)": 2,
    "(2, 2, 4)": 864,
    "(2, 3, 3)": 1032,
    "(2, 3, 4)": 263,
    "(2, 3, 4, 4)": 5203,
    "(2, 4, 4, 4)": 630,
    "(2, 4, 4, 4, 4)": 2058,
    "(3, 3, 3)": 2,
    "(3, 3, 3, 4)": 2244,
    "(3, 3, 4, 4)": 762,
    "(3, 3, 4, 4, 4)": 6019,
    "(3, 4, 4, 4, 4)": 1186,
    "(3, 4, 4, 4, 4, 4)": 2459,
    "(3,)": 25,
    "(4, 4)": 27
  },
  "fragment_relation_counts": [
    {
      "count": 10431,
      "relations": [
        "no_observable_fragment",
        "different_or_unresolved"
      ],
      "word": "A3R"
    },
    {
      "count": 71,
      "relations": [
        "no_observable_fragment",
        "no_observable_fragment"
      ],
      "word": "A3R"
    },
    {
      "count": 149,
      "relations": [
        "no_observable_fragment",
        "target_component_of_fragment"
      ],
      "word": "A3R"
    },
    {
      "count": 333,
      "relations": [
        "no_observable_fragment",
        "target_is_fragment_hex"
      ],
      "word": "A3R"
    },
    {
      "count": 230,
      "relations": [
        "single_charge_two"
      ],
      "word": "J"
    },
    {
      "count": 24,
      "relations": [
        "no_observable_fragment",
        "no_observable_fragment"
      ],
      "word": "RA2"
    },
    {
      "count": 9952,
      "relations": [
        "no_observable_fragment",
        "no_observable_fragment"
      ],
      "word": "RA3"
    },
    {
      "count": 1070,
      "relations": [
        "different_or_unresolved",
        "different_or_unresolved"
      ],
      "word": "RR"
    },
    {
      "count": 72,
      "relations": [
        "different_or_unresolved",
        "no_observable_fragment"
      ],
      "word": "RR"
    },
    {
      "count": 74,
      "relations": [
        "different_or_unresolved",
        "target_component_of_fragment"
      ],
      "word": "RR"
    },
    {
      "count": 320,
      "relations": [
        "different_or_unresolved",
        "target_is_fragment_hex"
      ],
      "word": "RR"
    },
    {
      "count": 1634,
      "relations": [
        "no_observable_fragment",
        "different_or_unresolved"
      ],
      "word": "RR"
    },
    {
      "count": 1221,
      "relations": [
        "no_observable_fragment",
        "no_observable_fragment"
      ],
      "word": "RR"
    },
    {
      "count": 5,
      "relations": [
        "no_observable_fragment",
        "target_component_of_fragment"
      ],
      "word": "RR"
    },
    {
      "count": 32,
      "relations": [
        "no_observable_fragment",
        "target_is_fragment_hex"
      ],
      "word": "RR"
    },
    {
      "count": 2,
      "relations": [
        "target_component_of_fragment",
        "different_or_unresolved"
      ],
      "word": "RR"
    },
    {
      "count": 4,
      "relations": [
        "target_component_of_fragment",
        "target_component_of_fragment"
      ],
      "word": "RR"
    },
    {
      "count": 36,
      "relations": [
        "target_is_fragment_hex",
        "no_observable_fragment"
      ],
      "word": "RR"
    }
  ],
  "interaction_counts": [
    {
      "count": 6428,
      "hex_support": "disjoint",
      "orbit_support": "disjoint",
      "word": "A3R"
    },
    {
      "count": 64,
      "hex_support": "overlap",
      "orbit_support": "disjoint",
      "word": "A3R"
    },
    {
      "count": 882,
      "hex_support": "disjoint",
      "orbit_support": "overlap",
      "word": "A3R"
    },
    {
      "count": 3610,
      "hex_support": "overlap",
      "orbit_support": "overlap",
      "word": "A3R"
    },
    {
      "count": 13,
      "hex_support": "disjoint",
      "orbit_support": "disjoint",
      "word": "RA2"
    },
    {
      "count": 10,
      "hex_support": "overlap",
      "orbit_support": "disjoint",
      "word": "RA2"
    },
    {
      "count": 1,
      "hex_support": "disjoint",
      "orbit_support": "overlap",
      "word": "RA2"
    },
    {
      "count": 6400,
      "hex_support": "disjoint",
      "orbit_support": "disjoint",
      "word": "RA3"
    },
    {
      "count": 2465,
      "hex_support": "overlap",
      "orbit_support": "disjoint",
      "word": "RA3"
    },
    {
      "count": 1087,
      "hex_support": "disjoint",
      "orbit_support": "overlap",
      "word": "RA3"
    },
    {
      "count": 3030,
      "hex_support": "disjoint",
      "orbit_support": "disjoint",
      "word": "RR"
    },
    {
      "count": 151,
      "hex_support": "overlap",
      "orbit_support": "disjoint",
      "word": "RR"
    },
    {
      "count": 126,
      "hex_support": "disjoint",
      "orbit_support": "overlap",
      "word": "RR"
    },
    {
      "count": 1163,
      "hex_support": "overlap",
      "orbit_support": "overlap",
      "word": "RR"
    }
  ],
  "legal_macro_tail_count_distribution": {
    "0": 53,
    "1": 51,
    "2": 1518,
    "3": 3450,
    "4": 20588
  },
  "local_fingerprint_count": 591,
  "local_fingerprints_with_multiple_tail_sets": 409,
  "malformed_charge_decompositions": 0,
  "minimum_counterexample_word_phase_to_tail_determinacy": {
    "claim_refuted": "ordered defect word plus deficit-phase tuple determines legal macro-tail set",
    "first_example": {
      "path": [
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
            "w3:210"
          ],
          "rotation_length": 3,
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
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w3:120"
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
      "safe_tails": [
        "rot^5;w2:10",
        "rot^5;w3:210"
      ],
      "state_hash": "b35b539e9bfc762d8ed1d25c61bc6ead642aacb5433153e23ee4809345a419d1"
    },
    "local_fingerprint": [
      "A3R",
      [
        2,
        4,
        4,
        4
      ],
      [
        [
          "A3_abandon_w3_new",
          0
        ],
        [
          "R_blocked_w3_existing",
          16
        ]
      ]
    ],
    "second_example": {
      "path": [
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
            "w3:210"
          ],
          "rotation_length": 3,
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
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w3:120"
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
      "safe_tails": [
        "rot^5;w2:10",
        "rot^5;w3:201",
        "rot^5;w3:210"
      ],
      "state_hash": "9304ea7f97fb5d776c7a79b7562feee10d5784483ed7a3bcbae1d0780e2299f9"
    }
  },
  "ordered_word_counts": {
    "A3R": 10984,
    "J": 230,
    "RA2": 24,
    "RA3": 9952,
    "RR": 4470
  },
  "provenance": {
    "reconstructed_code_sha": [
      "b02d3985d3672c24efdc197777cc25080fc9cb3846545db240ceacd649485049",
      "9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8",
      "18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60"
    ],
    "snapshot": "C:\\Users\\parks\\Documents\\Codex\\2026-07-20\\a-n-ge-4-s-n\\outputs\\f1_area_a_explosion_analysis.json",
    "snapshot_checkpoint_sha256": "6b6f73d6751d48760150ff5c2aa10512e5a40aae59c6461e928520c0b4ebe3f8",
    "snapshot_sha256": "16a34548e164746ab678057d8c351d9e4f0e7c6b973c15808efb975f96f313f0",
    "status": "historical checkpoint omitted macro_sha256; reconstructed from matching read-only snapshot"
  },
  "replay_method": {
    "canonical_spot_check_rule": "first five selected paths and every 1000th selected path",
    "canonical_spot_checks": 30,
    "full": "raw literal replay justified by proved left-S6 equivariance"
  },
  "representatives_by_word": {
    "A3R": {
      "coordinate": [
        6,
        1,
        5,
        0,
        4,
        14,
        2
      ],
      "defects": [
        {
          "abandonment": true,
          "delta": {
            "D": 4,
            "F": 1,
            "N": 1,
            "O": 1,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                3,
                3,
                1
              ]
            ],
            "current_hex": 96,
            "fragment_components": [
              [
                1,
                4,
                4
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
                105,
                4
              ],
              [
                138,
                4
              ]
            ]
          },
          "fragment_before": {
            "current_components": [
              [
                1,
                4,
                4
              ]
            ],
            "current_hex": 32,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                4
              ]
            ]
          },
          "kind": "A3_abandon_w3_new",
          "move": "w3:210",
          "new_orbit": true,
          "partial_component_relation": "unresolved",
          "rotation_length": 3,
          "source_orbit": 31,
          "source_phase": 3,
          "support": {
            "hexagons": [
              [
                32,
                28
              ],
              [
                96,
                8
              ]
            ],
            "orbits": [
              [
                105,
                4
              ]
            ]
          },
          "target_fragment_relation_before": "no_observable_fragment",
          "target_hexagon": 96,
          "target_orbit": 105,
          "target_phase": 2,
          "target_phase_mask_after": 4,
          "target_phase_mask_before": 0,
          "weight": 3
        },
        {
          "abandonment": false,
          "delta": {
            "D": -1,
            "F": 0,
            "N": 1,
            "O": 0,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                2,
                2,
                1
              ]
            ],
            "current_hex": 44,
            "fragment_components": [
              [
                1,
                4,
                4
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
                105,
                4
              ],
              [
                109,
                18
              ],
              [
                138,
                4
              ]
            ]
          },
          "fragment_before": {
            "current_components": [],
            "current_hex": 108,
            "fragment_components": [
              [
                1,
                4,
                4
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
                105,
                4
              ],
              [
                109,
                16
              ],
              [
                138,
                4
              ]
            ]
          },
          "kind": "R_blocked_w3_existing",
          "move": "w3:120",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 5,
          "source_orbit": 111,
          "source_phase": 3,
          "support": {
            "hexagons": [
              [
                44,
                4
              ],
              [
                108,
                31
              ]
            ],
            "orbits": [
              [
                109,
                2
              ]
            ]
          },
          "target_fragment_relation_before": "different_or_unresolved",
          "target_hexagon": 44,
          "target_orbit": 109,
          "target_phase": 1,
          "target_phase_mask_after": 18,
          "target_phase_mask_before": 16,
          "weight": 3
        }
      ],
      "deficit_phase_type": [
        2,
        4,
        4,
        4
      ],
      "interaction": {
        "component_relation_pair": [
          "unresolved",
          "unresolved"
        ],
        "first_source_equals_second_target": false,
        "first_target_equals_second_source": false,
        "fragment_relation_pair": [
          "no_observable_fragment",
          "different_or_unresolved"
        ],
        "hex_support_relation": "disjoint",
        "independence_status": "necessary_support_conditions_hold_but_swap_unverified",
        "orbit_support_relation": "disjoint",
        "same_source_orbit": false,
        "same_target_orbit": false,
        "swap_status": "undetermined: exact literal replay is required even when supports are disjoint"
      },
      "legal_macro_tail_count": 2,
      "macro_distance": 2,
      "path": [
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
            "w3:210"
          ],
          "rotation_length": 3,
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
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w3:120"
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
      "state_hash": "b35b539e9bfc762d8ed1d25c61bc6ead642aacb5433153e23ee4809345a419d1"
    },
    "J": {
      "coordinate": [
        6,
        1,
        3,
        0,
        2,
        4,
        2
      ],
      "defects": [
        {
          "abandonment": true,
          "delta": {
            "D": -1,
            "F": 1,
            "N": 2,
            "O": 0,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                5,
                5,
                1
              ]
            ],
            "current_hex": 1,
            "fragment_components": [
              [
                1,
                2,
                2
              ]
            ],
            "fragment_hex": 18,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                17
              ],
              [
                138,
                29
              ]
            ]
          },
          "fragment_before": {
            "current_components": [
              [
                1,
                2,
                2
              ]
            ],
            "current_hex": 18,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                29
              ]
            ]
          },
          "kind": "J_abandon_w3_existing_charge2",
          "move": "w3:120",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 1,
          "source_orbit": 105,
          "source_phase": 1,
          "support": {
            "hexagons": [
              [
                1,
                32
              ],
              [
                18,
                4
              ]
            ],
            "orbits": [
              [
                0,
                16
              ]
            ]
          },
          "target_fragment_relation_before": "no_observable_fragment",
          "target_hexagon": 1,
          "target_orbit": 0,
          "target_phase": 4,
          "target_phase_mask_after": 17,
          "target_phase_mask_before": 1,
          "weight": 3
        }
      ],
      "deficit_phase_type": [
        1,
        3
      ],
      "interaction": null,
      "legal_macro_tail_count": 3,
      "macro_distance": null,
      "path": [
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
        },
        {
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w3:120"
          ],
          "rotation_length": 1,
          "rotation_stopped_by_collision": false
        }
      ],
      "state_hash": "1a1ac861c6531f75c023a9b3ce98645a7105cfc1aed3d03e99708a2a4ffd9334"
    },
    "RA2": {
      "coordinate": [
        6,
        1,
        3,
        0,
        2,
        4,
        2
      ],
      "defects": [
        {
          "abandonment": false,
          "delta": {
            "D": -1,
            "F": 0,
            "N": 1,
            "O": 0,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                1,
                1,
                1
              ]
            ],
            "current_hex": 18,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                13
              ]
            ]
          },
          "fragment_before": {
            "current_components": [],
            "current_hex": 61,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                12
              ]
            ]
          },
          "kind": "R_blocked_w3_existing",
          "move": "w3:120",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 5,
          "source_orbit": 61,
          "source_phase": 0,
          "support": {
            "hexagons": [
              [
                18,
                2
              ],
              [
                61,
                61
              ]
            ],
            "orbits": [
              [
                138,
                1
              ]
            ]
          },
          "target_fragment_relation_before": "no_observable_fragment",
          "target_hexagon": 18,
          "target_orbit": 138,
          "target_phase": 0,
          "target_phase_mask_after": 13,
          "target_phase_mask_before": 12,
          "weight": 3
        },
        {
          "abandonment": true,
          "delta": {
            "D": -1,
            "F": 1,
            "N": 1,
            "O": 0,
            "S": 0
          },
          "fragment_after": {
            "current_components": [
              [
                4,
                4,
                1
              ]
            ],
            "current_hex": 4,
            "fragment_components": [
              [
                1,
                2,
                2
              ]
            ],
            "fragment_hex": 18,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                9
              ],
              [
                138,
                13
              ]
            ]
          },
          "fragment_before": {
            "current_components": [
              [
                1,
                2,
                2
              ]
            ],
            "current_hex": 18,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                13
              ]
            ]
          },
          "kind": "A2_abandon_w2_existing",
          "move": "w2:10",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 1,
          "source_orbit": 105,
          "source_phase": 1,
          "support": {
            "hexagons": [
              [
                4,
                16
              ],
              [
                18,
                4
              ]
            ],
            "orbits": [
              [
                0,
                8
              ]
            ]
          },
          "target_fragment_relation_before": "no_observable_fragment",
          "target_hexagon": 4,
          "target_orbit": 0,
          "target_phase": 3,
          "target_phase_mask_after": 9,
          "target_phase_mask_before": 1,
          "weight": 2
        }
      ],
      "deficit_phase_type": [
        2,
        2
      ],
      "interaction": {
        "component_relation_pair": [
          "unresolved",
          "unresolved"
        ],
        "first_source_equals_second_target": false,
        "first_target_equals_second_source": false,
        "fragment_relation_pair": [
          "no_observable_fragment",
          "no_observable_fragment"
        ],
        "hex_support_relation": "overlap",
        "independence_status": "not_independent_by_support_definition",
        "orbit_support_relation": "disjoint",
        "same_source_orbit": false,
        "same_target_orbit": false,
        "swap_status": "undetermined: exact literal replay is required even when supports are disjoint"
      },
      "legal_macro_tail_count": 3,
      "macro_distance": 1,
      "path": [
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
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w3:120"
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
      "state_hash": "a8185d5454429afeaa56b859c563c63e538a6841dc9ea373485244e3b1b35102"
    },
    "RA3": {
      "coordinate": [
        6,
        1,
        4,
        0,
        3,
        9,
        2
      ],
      "defects": [
        {
          "abandonment": false,
          "delta": {
            "D": -1,
            "F": 0,
            "N": 1,
            "O": 0,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                1,
                1,
                1
              ]
            ],
            "current_hex": 105,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                30
              ]
            ]
          },
          "fragment_before": {
            "current_components": [],
            "current_hex": 76,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                28
              ]
            ]
          },
          "kind": "R_blocked_w3_existing",
          "move": "w3:120",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 5,
          "source_orbit": 76,
          "source_phase": 0,
          "support": {
            "hexagons": [
              [
                76,
                61
              ],
              [
                105,
                2
              ]
            ],
            "orbits": [
              [
                138,
                2
              ]
            ]
          },
          "target_fragment_relation_before": "no_observable_fragment",
          "target_hexagon": 105,
          "target_orbit": 138,
          "target_phase": 1,
          "target_phase_mask_after": 30,
          "target_phase_mask_before": 28,
          "weight": 3
        },
        {
          "abandonment": true,
          "delta": {
            "D": 4,
            "F": 1,
            "N": 1,
            "O": 1,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                4,
                4,
                1
              ]
            ],
            "current_hex": 35,
            "fragment_components": [
              [
                1,
                1,
                1
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
                32,
                8
              ],
              [
                138,
                30
              ]
            ]
          },
          "fragment_before": {
            "current_components": [
              [
                1,
                1,
                1
              ]
            ],
            "current_hex": 105,
            "fragment_components": [],
            "fragment_hex": null,
            "fragment_is_current": false,
            "normal_form_valid": true,
            "orbit_phase_masks": [
              [
                0,
                1
              ],
              [
                138,
                30
              ]
            ]
          },
          "kind": "A3_abandon_w3_new",
          "move": "w3:120",
          "new_orbit": true,
          "partial_component_relation": "unresolved",
          "rotation_length": 0,
          "source_orbit": 138,
          "source_phase": 1,
          "support": {
            "hexagons": [
              [
                35,
                16
              ]
            ],
            "orbits": [
              [
                32,
                8
              ]
            ]
          },
          "target_fragment_relation_before": "no_observable_fragment",
          "target_hexagon": 35,
          "target_orbit": 32,
          "target_phase": 3,
          "target_phase_mask_after": 8,
          "target_phase_mask_before": 0,
          "weight": 3
        }
      ],
      "deficit_phase_type": [
        1,
        4,
        4
      ],
      "interaction": {
        "component_relation_pair": [
          "unresolved",
          "unresolved"
        ],
        "first_source_equals_second_target": false,
        "first_target_equals_second_source": true,
        "fragment_relation_pair": [
          "no_observable_fragment",
          "no_observable_fragment"
        ],
        "hex_support_relation": "disjoint",
        "independence_status": "not_independent_by_support_definition",
        "orbit_support_relation": "overlap",
        "same_source_orbit": false,
        "same_target_orbit": false,
        "swap_status": "undetermined: exact literal replay is required even when supports are disjoint"
      },
      "legal_macro_tail_count": 3,
      "macro_distance": 1,
      "path": [
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
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w3:120"
          ],
          "rotation_length": 5,
          "rotation_stopped_by_collision": true
        },
        {
          "joint": "w3:120",
          "literal_labels": [
            "w3:120"
          ],
          "rotation_length": 0,
          "rotation_stopped_by_collision": false
        }
      ],
      "state_hash": "54d298cda4b975a2a233c641e4c367964173daf46b51bc42de90d232c5c6b387"
    },
    "RR": {
      "coordinate": [
        6,
        1,
        4,
        0,
        3,
        9,
        2
      ],
      "defects": [
        {
          "abandonment": false,
          "delta": {
            "D": -1,
            "F": 0,
            "N": 1,
            "O": 0,
            "S": 1
          },
          "fragment_after": {
            "current_components": [
              [
                5,
                5,
                1
              ]
            ],
            "current_hex": 33,
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
                32,
                22
              ],
              [
                138,
                4
              ]
            ]
          },
          "fragment_before": {
            "current_components": [],
            "current_hex": 45,
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
                32,
                6
              ],
              [
                138,
                4
              ]
            ]
          },
          "kind": "R_blocked_w3_existing",
          "move": "w3:120",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 5,
          "source_orbit": 112,
          "source_phase": 1,
          "support": {
            "hexagons": [
              [
                33,
                32
              ],
              [
                45,
                55
              ]
            ],
            "orbits": [
              [
                32,
                16
              ]
            ]
          },
          "target_fragment_relation_before": "different_or_unresolved",
          "target_hexagon": 33,
          "target_orbit": 32,
          "target_phase": 4,
          "target_phase_mask_after": 22,
          "target_phase_mask_before": 6,
          "weight": 3
        },
        {
          "abandonment": false,
          "delta": {
            "D": -1,
            "F": 0,
            "N": 1,
            "O": 0,
            "S": 1
          },
          "fragment_after": {
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
                32,
                22
              ],
              [
                138,
                4
              ]
            ]
          },
          "fragment_before": {
            "current_components": [],
            "current_hex": 33,
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
                32,
                22
              ],
              [
                138,
                4
              ]
            ]
          },
          "kind": "R_blocked_w3_existing",
          "move": "w3:210",
          "new_orbit": false,
          "partial_component_relation": "unresolved",
          "rotation_length": 5,
          "source_orbit": 34,
          "source_phase": 3,
          "support": {
            "hexagons": [
              [
                18,
                8
              ],
              [
                33,
                31
              ]
            ],
            "orbits": [
              [
                0,
                4
              ]
            ]
          },
          "target_fragment_relation_before": "different_or_unresolved",
          "target_hexagon": 18,
          "target_orbit": 0,
          "target_phase": 2,
          "target_phase_mask_after": 5,
          "target_phase_mask_before": 1,
          "weight": 3
        }
      ],
      "deficit_phase_type": [
        2,
        3,
        4
      ],
      "interaction": {
        "component_relation_pair": [
          "unresolved",
          "unresolved"
        ],
        "first_source_equals_second_target": false,
        "first_target_equals_second_source": false,
        "fragment_relation_pair": [
          "different_or_unresolved",
          "different_or_unresolved"
        ],
        "hex_support_relation": "overlap",
        "independence_status": "not_independent_by_support_definition",
        "orbit_support_relation": "disjoint",
        "same_source_orbit": false,
        "same_target_orbit": false,
        "swap_status": "undetermined: exact literal replay is required even when supports are disjoint"
      },
      "legal_macro_tail_count": 4,
      "macro_distance": 1,
      "path": [
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
          "joint": "w3:120",
          "literal_labels": [
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w1:0",
            "w3:120"
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
      "state_hash": "6871e2d08c32f5d7fb35c1143240c68630d03e5504a1d6b4f11f29ecb45702a0"
    }
  },
  "schema": "f1-n2-area-a-depth6-path-decomposition-v1",
  "scope": "finite complete replay of an existing bounded Area-A frontier; not an N=2 enumeration",
  "selected_F1_H0_N2_frontier_states": 25660
}
~~~
