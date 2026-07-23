# Forest recovery and merge status

## Declared status

**all five branches verified; final merge complete**

> 포화 collision-forest cover 전체에서 heavy budget (H≤3) exact port-lift는 실패한다.

The word ‘entire’ here is scoped to the five completed depth-2 seeds of the forest-only canonical-augmentation enumeration. It does not remove NR6, solve other (F,D,N) slabs, or prove `L_6 >= 872`.

## Reproducibility

- Recovery report code SHA-256: `e77695116d6cefed8aad93cf4bccc51464d67d7973571f40cc48fe61ee195fb8`
- Generator code SHA-256: `18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60`
- Independent verifier SHA-256: `b23f20a250cac4c90f4c36a22335edf6b5eaa9bc84ef5b17e3a584dc876d20f6`
- Runner SHA-256: `fd98b21d8a897820cd1989f36098a0abc03949df82c4d084fec4b115875ca634`

## Process recovery

No matching runner/enumerator process is active. The runner script's finally block would log 'runner stopped', but no such final line follows its last 0,27 start record; this is evidence of an abrupt supervisor disappearance rather than a graceful recorded exit. The 0,27 child completed later, so its completion timestamp does not identify the supervisor exit time. Branch stderr logs are empty and the bounded Windows PowerShell/Application event inspection yielded no unambiguous runner termination event. Exact exit time and external cause cannot be recovered from the available artifacts.

Last runner activity: `2026-07-23T05:29:46.9952005+09:00 started seed 0,27 pid 32908: C:\Users\parks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe work\superperm_port_lift.py enumerate-forest-covers --seed 0,27 --node-limit 0 --output outputs\forest_branch_0_27.json`
Last graceful-stop record: `2026-07-23T01:29:37.6174091+09:00 runner stopped`

## Branch validation

| seed | completed | node limit | nodes | certificates | incidence | DP replay | input SHA prefix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0,2 | True | 0 | 39754357 | 326 | True | True | 3fd842db73dd8e56 |
| 0,3 | True | 0 | 15350197 | 326 | True | True | 36d4d4b75d20b755 |
| 0,7 | True | 0 | 33769945 | 326 | True | True | 1e04ea4fb027bed7 |
| 0,15 | True | 0 | 39586915 | 326 | True | True | 24fccd0b2e83ed75 |
| 0,27 | True | 0 | 36888613 | 326 | True | True | 7ce0288fd807b18c |

Each row was freshly checked against its current input certificate SHA set by a recovery-named incidence verifier output and then by a recovery-named full DP replay output. All branch files parse, have `completed:true`, `node_limit:0`, and `aborted_at_node_limit:false`.

## Seed overlap and merge

Raw certificates: 1630; canonical unique classes: 326; cross-seed duplicates removed: 1304.

All ten pairwise intersections have size 326. Each of the 326 classes occurs in all five seeds; no seed-only class exists. The merged JSON and both merged verifier outputs are listed in the machine-readable status file.

## Merged statistics

| H=3 max f-cycles reached | classes |
| --- | --- |
| 9 | 8 |
| 10 | 6 |
| 11 | 20 |
| 12 | 64 |
| 13 | 164 |
| 14 | 64 |

The collision-forest component-partition distribution is in `forest_all_statistics.json`. All 326 merged classes report `complete_lift_exists=false` at H=0,1,2,3, and the merged full DP replay verifies those serialized tables.

## Restart guidance

No restart is required. The current absence of a runner/enumerator process is not treated as a failed branch because every output is complete and freshly verified. No process was restarted by this procedure.
