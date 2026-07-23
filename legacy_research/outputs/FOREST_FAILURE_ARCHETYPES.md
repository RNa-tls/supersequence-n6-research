# Minimal forest port-lift failure certificates

Each row below selects the smallest H=3 reachable-state representative of a coarse diagnostic group. Full reproducible data, including 25 orbit IDs, five double hexagons, collision forest, f-cycle port words, H=3 layer counts, and phase-aware transition summary are in `forest_failure_archetypes.json`.

Analysis SHA-256: `60db6cac5c4a0c46437acc3327d083cc538da188482318dde5995df691eac420`  
Input SHA-256 (`0,2`): `3fd842db73dd8e56e8335a2bde57ef3ba23bb55b91a4a37f475b32e1e6f0c7d3`  
Input SHA-256 (`0,3`): `36d4d4b75d20b75560b151b06e56db287930c21b6001943d9b4fc7b74fa7f194`

| covers | H3 max | first empty layer | forest component partition | representative SHA prefix |
| --- | --- | --- | --- | --- |
| 2 | 10 | 11 | 4,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 9af14ea2589716c4 |
| 4 | 10 | 11 | 6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 4f8e29e895a86c4f |
| 8 | 11 | 12 | 3,3,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 71326819ed81174f |
| 12 | 11 | 12 | 6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 22d7ac99175630cc |
| 14 | 12 | 13 | 3,3,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 12e074ef9cb46aec |
| 50 | 12 | 13 | 6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 5e4b10d5570f3e75 |
| 52 | 13 | 14 | 3,3,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 3caffc1ce14819bb |
| 112 | 13 | 14 | 6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | b9ed7a1371279cd9 |
| 64 | 14 | 15 | 6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 1cbc37bfb4657f58 |
| 2 | 9 | 10 | 3,3,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 46db7f157f2a0ff6 |
| 6 | 9 | 10 | 6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 | 0678f8a967000b76 |

The strict requested grouping (which also fixes the complete H=3 layer-state-count profile) is retained separately in JSON. If it yields singleton groups, that is a finding about the heterogeneity of exact DP state counts rather than permission to collapse them.

The allowed transition data are summarized by weight in the certificates to avoid implying that a mask-free graph gives the exact no-revisit DP path. The exact failure stage reported for each representative is its serialized H=3 first empty layer and maximum reached cycle cardinality.
