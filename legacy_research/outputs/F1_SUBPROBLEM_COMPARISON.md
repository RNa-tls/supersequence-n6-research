# F=1 restricted-subproblem comparison

Both rows retain `F=0` ancestors, since an `F=1` state cannot otherwise be
reached.  The restrictions are monotone after they appear.

- analysis SHA-256: `26813bd8e01601f532bf916b91811f56497a4136b3ac6d9813f1105081b6e22e`
- exact-state engine SHA-256: `9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8`
- core group-code SHA-256: `18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60`

| region | completed depth | final canonical frontier | fragment types | checkpoint SHA-256 | stop/completion |
|---|---:|---:|---:|---|---|
| A: F=1,H=0,N<=3 | 6 | 24 | 10 | c518f3f2ad736e020f367f6472030fa8ca42431af1d38347ef24d348a4eddc57 | completed_target_depth |
| B: F=1,N=0,H<=3 | 6 | 542 | 5 | fecceed57e3ec0c67779875793f23b90d07fbc7da77786147631ea565b7c0e01 | completed_target_depth |

Recommendation is made only from these bounded measurements and is not a
claim that either region is exhaustively solved.

**Recommended first complete subproblem:** A.
