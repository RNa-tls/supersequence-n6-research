# F=1 bounded depth profile

This is a **limited experiment**, not a complete calculation and not an
absence proof for `(F,D,N)=(1,4,*)`.

- mode: `general`
- requested depth: `6`
- completed depth: `6`
- outcome: `completed_target_depth`
- per-stage node cap: `20000`
- working-set cap: `1073741824` bytes
- analysis SHA-256: `26813bd8e01601f532bf916b91811f56497a4136b3ac6d9813f1105081b6e22e`
- exact-state engine SHA-256: `9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8`
- core group-code SHA-256: `18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60`
- final checkpoint SHA-256: `3fcfd43b22d77aa99c4cf92d44a58b50a1e4553af40b08b2a5393677935d6eb2`

| reached depth | expanded source states | new canonical states | generated transitions | memo duplicates | peak working set | checkpoint bytes | seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 89 | 550 | 0 | 40177664 | 65378 | 1.152 |
| 2 | 89 | 177 | 48815 | 0 | 41152512 | 146494 | 4.004 |
| 3 | 177 | 265 | 97092 | 0 | 42627072 | 239310 | 6.519 |
| 4 | 265 | 353 | 145083 | 0 | 42283008 | 343381 | 9.347 |
| 5 | 353 | 441 | 192980 | 0 | 43577344 | 459157 | 12.127 |
| 6 | 441 | 980 | 240672 | 0 | 45621248 | 929361 | 20.75 |

Full machine-readable histograms, fingerprints, long-lived representatives,
and counterexample paths are in `f1_depth_profile.json`.
