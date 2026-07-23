# F=1, H=0, N=0 committed-checkpoint resume

Status: `N=0 search interrupted again; resumable checkpoint verified`.

Scope: this runner concerns only the NR6/exact-state subcase `F=1, H=0, N=0`.  It makes no claim about `N>0`, other F slabs, or the full superpermutation lower bound.

```json
{
    "automatic_restart":  false,
    "started_at":  "2026-07-23T14:33:39.9771092+09:00",
    "uncommitted_tmp_comparison_only":  "C:\\Users\\parks\\Documents\\Codex\\2026-07-20\\a-n-ge-4-s-n\\outputs\\f1_small_n0.checkpoint.json.tmp",
    "next_step":  "Do not restart automatically.  Preserve this new checkpoint and validate it before any future resume.",
    "state":  "N=0 search interrupted again; resumable checkpoint verified",
    "run_checkpoint":  {
                           "parse_ok":  true,
                           "size_bytes":  309489953,
                           "summary":  {
                                           "schema":  "partial-f1-macro-checkpoint-v1",
                                           "macro_sha256":  "b02d3985d3672c24efdc197777cc25080fc9cb3846545db240ceacd649485049",
                                           "engine_sha256":  "9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8",
                                           "core_sha256":  "18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60",
                                           "config":  {
                                                          "canonical_children":  true,
                                                          "max_macro_depth":  null,
                                                          "memory_limit_bytes":  0,
                                                          "n_limit":  0,
                                                          "name":  "small_F1_H0_N0",
                                                          "node_limit":  0
                                                      },
                                           "expanded":  36250,
                                           "accepted":  114182,
                                           "frontier":  77932,
                                           "terminal_certificates":  142,
                                           "success_certificates":  0,
                                           "prunes":  {
                                                          "F_exceeded":  611630,
                                                          "N_exceeded_monotone":  75035,
                                                          "collision":  66355,
                                                          "memo_duplicate":  1,
                                                          "remaining_cover_capacity_impossible":  334
                                                      }
                                       },
                           "last_write":  "2026-07-23T14:57:19.6878560+09:00",
                           "exists":  true
                       },
    "resume_source":  "C:\\Users\\parks\\Documents\\Codex\\2026-07-20\\a-n-ge-4-s-n\\outputs\\f1_small_n0.checkpoint.json",
    "schema":  "partial-f1-n0-committed-resume-v1",
    "exit_code":  null,
    "result":  {
                   "completed":  false,
                   "path":  "C:\\Users\\parks\\Documents\\Codex\\2026-07-20\\a-n-ge-4-s-n\\outputs\\f1_small_n0_committed_resume_search.json",
                   "parse_error":  null,
                   "exists":  false
               },
    "ended_at":  "2026-07-23T14:58:46.3088055+09:00"
}
```
