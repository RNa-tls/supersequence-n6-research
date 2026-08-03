# Round 52 - top-8 interruption and resume audit

## Scope

Read-only audit only: no v6 checkpoint was written or resumed. The worker has no recoverable process-exit record in this repository; absence of stderr is not treated as evidence of a normal exit. The termination cause is therefore **UNKNOWN**.

## Atomic checkpoint ledger

| child | base | current total | additional v6 | frontier | status |
| --- | ---: | ---: | ---: | ---: | --- |
| `short_ell2_r1_70` | 5000 | 55000 | 50000 | 11 | `CAP_REACHED_NONEMPTY_FRONTIER` |
| `short_ell4_r1_12` | 5000 | 40457 | 35457 | 0 | `NATURALLY_EXHAUSTED` |
| `short_ell1_r1_98` | 5000 | 5461 | 461 | 0 | `NATURALLY_EXHAUSTED` |
| `short_ell2_r1_40` | 5000 | 5697 | 697 | 0 | `NATURALLY_EXHAUSTED` |
| `short_ell3_r1_64` | 5000 | 27737 | 22737 | 0 | `NATURALLY_EXHAUSTED` |
| `short_ell2_r1_37` | 5000 | 55000 | 50000 | 19 | `CAP_REACHED_NONEMPTY_FRONTIER` |
| `short_ell2_r1_107` | 5000 | 5731 | 731 | 0 | `NATURALLY_EXHAUSTED` |
| `short_ell3_r1_56` | 5000 | 12737 | 7737 | 0 | `NATURALLY_EXHAUSTED` |

Atomic payload total is 207820; it comprises 40,000 historical base expansions plus 167820 additional v6 expansions. The authoritative ledger is therefore 167820, not the earlier console estimate of 206,083. That estimate was not an atomic eight-checkpoint ledger and is superseded. The 400,000 figure is only the sum of caps: natural exhaustion legitimately stops a branch below cap.

## Resume safety

Every checkpoint JSON-parsed and passed the v5 loader's read-only config/root/child/schema/complete-frontier test. Each original Round-50 source checkpoint SHA is independently verified against the immutable aggregate result. The v6 writer did not preserve its auxiliary `top8_continuation` field after its first atomic rewrite, so base provenance is externally verified rather than asserted from the current v6 payload; this is serializer metadata loss, not engine-state corruption.

All eight payloads are endpoints: six have empty frontiers (natural exhaustion), while two reached the exact 50,000-additional-expansion cap with nonempty frontiers. **No branch remains resumable and no worker is started.**

The engine-level read-only loader accepts every payload, but the historical v6
driver itself requires the dropped `top8_continuation.source_sha256` field and
would reject a subsequent `--resume`. Thus a future deeper study must begin
from a separately audited namespace or an explicit provenance migration; it
must not silently reuse this driver/checkpoint pair. This did not block the
present task because no child was interrupted below its declared endpoint.

The audit did not resume a worker. Once the endpoint condition was confirmed,
the separate read-only component-bridge analysis was run against these exact
payloads; see `RR_SHORT5_TOP8_CONTINUATION_CODEX.md`.

- audit payload: `outputs/rr_short5_top8_interruption_audit.json`
- audit script SHA-256: `ec1461df87b6d018c25f0436c9f9b87e6ec7a6bd4457060e2df0984018386829`
