# Round 40 — `short_ell0` corrected medium run

Status: **INCOMPLETE**.  This is a cap-bounded diagnostic run, so it is not an exhaustion claim unless the frontier is empty.

## Scope and checkpoint lineage

- Only `short_ell0` was run; no other short or long root was started.
- Source: `outputs\checkpoints\rr_short5\r1_complete_v2\short_ell0_pilot.json` (v2 R1-complete pilot only).
- Target: `outputs\checkpoints\rr_short5\r1_complete_v2\short_ell0_medium.json`.
- The migration preserved literal frontier and memo keys, then changed only the hash-bound node-limit/config identity and additive telemetry.
- The current and pilot engine one-step signatures agree on every source-frontier state: 0 mismatches of 84.

## Telemetry

| quantity | value |
|---|---:|
| total expansions | 100250 |
| pre-R nodes | 5 |
| post-R1 nodes | 100245 |
| R1 transitions | 4 |
| unique r_count=1 decorated states | 100320 |
| R2 candidate edges | 53708 |
| Target-A hits | 0 |
| CH1 / CH2 / provisional CH0 events | 1 / 0 / 1 |
| hub completion before / after R1 | 2 / 0 |
| maximum post-R1 depth | 83 |
| frontier r-count distribution | {0: 10, 1: 75} |

`CH0` is a provisional analysis label only; it is not a semantic branch classification or a prune.

## Histograms

- `Phi_at_R1`: `{'0': 1, '1': 3}`
- `M_at_R1` (`M=P-5O` on the accepted R1 child): `{'-3': 1, '-5': 1, '-6': 1, '-7': 1}`
- expanded-node `steps_since_R1`: `{'0': 1, '1': 1, '10': 1, '11': 1, '12': 1, '13': 1, '14': 2, '15': 1, '16': 1, '17': 1, '18': 1, '19': 1, '2': 1, '20': 1, '21': 1, '22': 1, '23': 1, '24': 1, '25': 1, '26': 1, '27': 1, '28': 1, '29': 1, '3': 1, '30': 1, '31': 1, '32': 2, '33': 2, '34': 2, '35': 1, '36': 1, '37': 1, '38': 1, '39': 1, '4': 1, '40': 1, '41': 2, '42': 2, '43': 4, '44': 8, '45': 14, '46': 23, '47': 41, '48': 71, '49': 121, '5': 1, '50': 215, '51': 359, '52': 609, '53': 933, '54': 1444, '55': 2185, '56': 3110, '57': 4276, '58': 5425, '59': 6684, '6': 1, '60': 7842, '61': 8745, '62': 9417, '63': 9399, '64': 8972, '65': 7941, '66': 6701, '67': 5378, '68': 3867, '69': 2639, '7': 1, '70': 1669, '71': 1007, '72': 551, '73': 307, '74': 143, '75': 64, '76': 25, '77': 6, '78': 1, '8': 1, '9': 1}`
- post-R1 prunes: `{'area_a:F_exceeded': 925880, 'area_a:O_exceeded': 40428, 'decorated_memo_duplicate': 4, 'exact_permutation_collision': 1285544, 'r2_not_target': 53708}`

## Key and verification scope

- State-key status: **exhaustive tested-universe equivalence** — finite tested-universe evidence only, not a theorem.
- Independent verifier: `outputs/rr_short_ell0_medium_v2_verified.json`.
