# Forest overnight status

Updated: 2026-07-23T05:26:22.4828460+09:00
Runner SHA-256: fd98b21d8a897820cd1989f36098a0abc03949df82c4d084fec4b115875ca634

| seed | state | PID | CPU s | working set MB | nodes | certificates | incidence | DP replay |
|---|---|---:|---:|---:|---:|---:|---|---|
| 0,2 | verified |  |  |  | 39754357 | 326 | True | True |
| 0,3 | verified |  |  |  | 15350197 | 326 | True | True |
| 0,7 | running | 40920 | 12230.52 | 3558.5 |  |  | False | False |
| 0,15 | running | 31376 | 2715.77 | 1649.1 |  |  | False | False |
| 0,27 | queued |  |  |  |  |  | False | False |

Final merge permitted: **False**

A running branch has no safe checkpoint/resume artifact in the current enumerator; its heartbeat records CPU/memory/time only.  A process that exits without `completed: true` is recorded as failed and is not automatically restarted.

The machine-readable JSON contains the exact restart command for every branch.
