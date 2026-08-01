# v3 `short_ell0` structural analysis — verification failed, analysis not performed

## 1. Verify remote data — **FAILED**

Per §1 of the assigning instruction, before doing anything else I fetched
and checked for commit `785ddab` and the four required files.

```
git fetch origin codex/round40-short5-r1-complete
git ls-remote origin
  7dce52e...  refs/heads/main
  baae180...  refs/heads/claude/n6-supersequence-length-rn17wf
  abfcdca...  refs/heads/codex/round40-short5-r1-complete   <- unchanged, same commit as the last two rounds

get_commit(owner=rna-tls, repo=supersequence-n6-research, sha="785ddab")
  -> 422 No commit found for SHA: 785ddab
```

`codex/round40-short5-r1-complete` still tops out at `abfcdca` — the exact
commit already inspected two rounds ago. No new commit, branch, or ref
exists anywhere this session can reach. I also checked the local
filesystem directly, in case the files existed uncommitted:

```
find . -iname "*v3*"          -> only this repo's own unrelated legacy
                                  "nonpartition_covers_quotient_*_v3*"
                                  files and my own prior-round
                                  outputs/rr_short5_v3_analysis_schema_claude.json
find . -iname "*differential*" -> nothing
```

None of the four required files exist, committed or otherwise:

- `research/RR_SHORT_ELL0_MEDIUM_V3_TARGET_A_CODEX.md` — **not found**
- `outputs/rr_short_ell0_medium_v3.json` — **not found**
- `outputs/rr_short_ell0_medium_v3_verified.json` — **not found**
- `outputs/rr_short_ell0_v2_v3_differential.json` — **not found**

**The counts in the assigning message's "Known v3 facts" block cannot be
confirmed.** I did not find them in any file, and I have no way to
independently corroborate that they came from a real run at all.

## 2. Why §§2-8 are not attempted

This round's instruction supplies specific numbers directly in the
prompt (100,250 expansions, R2 candidates 49,440, `not_same_component`:
5,419, `recognizer_geometry_failure`: 44,021, etc.) and then asks for an
eight-part structural analysis built on top of them — orbit/phase
classification of "the four exported R1 events," a subdivision of the
44,021 figure into exact subconditions, a component-count distribution
over the 5,419 same-component failures, a full classification of "all 85
frontier states," recurrence analysis over a claimed max-depth-103
branch, and a search for a monotone potential function.

**None of this can be done honestly without the underlying file.** Every
one of those eight items requires per-state or per-event data (orbit
IDs, phases, `Phi`/`M` values, component memberships, exact hub masks)
that exists nowhere in this repository and was not exportable by me from
anything already on disk. Performing the analysis anyway — treating the
prompt's numbers as ground truth and producing tables, classifications,
and "common facts across all four events" — would mean fabricating
structural findings and presenting them under this project's own
`CLAUDE_OBSERVATION` label, which this project's entire history
(explicitly, repeatedly) defines as *"a fact read directly off existing
data or code."* There is no existing data here to read. I am not willing
to manufacture the appearance of verified analysis over unverifiable
numbers, regardless of how specific or plausible they look — that is
exactly the failure mode this whole project's proof-status vocabulary
exists to prevent.

This is not a judgment that the numbers are false. It may well be that a
real `785ddab` exists in an environment or repository this session
cannot reach (a different fork, an unpushed local branch on Codex's
machine, a sync delay). But "plausible" and "unreachable" are not
"verified," and this project's standing rule — applied identically to
every prior round, including the two immediately before this one — is
that a citation is acted on only once it is independently confirmed,
never on trust alone.

## 3. What was actually performed

Only the verification step (§1) and this document. No R1 event analysis,
no `recognizer_geometry_failure` subdivision, no same-component analysis,
no frontier classification, no long-branch recurrence analysis, no
potential-function search, and no prune candidates are offered — every
one of those requires the missing files as raw material, and manufacturing
a substitute would violate this analyst role's core constraint more
directly than declining to answer does.

## 4. Minimal Codex export request

Per §3's own fallback instruction ("if the committed telemetry is
insufficient, produce the minimal Codex export request") — generalized
here to the whole task, since the insufficiency is total, not confined to
one category. See `outputs/rr_short_ell0_v3_missing_export_request_claude.json`
for the structured version. In short: **push commit `785ddab` (or
whatever commit actually contains this work) to a branch reachable from
`rna-tls/supersequence-n6-research`**, containing at minimum:

1. `research/RR_SHORT_ELL0_MEDIUM_V3_TARGET_A_CODEX.md`
2. `outputs/rr_short_ell0_medium_v3.json`
3. `outputs/rr_short_ell0_medium_v3_verified.json`
4. `outputs/rr_short_ell0_v2_v3_differential.json`

with, at minimum, the per-event and per-candidate granularity already
requested in the prior round's `outputs/rr_short5_v3_analysis_schema_claude.json`
(per-R1-event `Phi`/`M`, exact hub timing, a refined event-order class,
per-candidate R2 recognizer failure reasons, `O`/`P` trajectories beyond
`O=25`, and the Target-A-safe admission-profile diff) — none of which
this round's "Known v3 facts" summary numbers can substitute for, since
aggregate counts alone cannot support §§2-8's per-event/per-state
requests regardless of whether they are accurate.

## 5. A pattern worth naming plainly

This is the fourth consecutive round in which a specific commit SHA was
cited as containing verified work, and the fourth in which that SHA does
not exist on any branch this session can reach
(`d8600b9`/`e9ff19c`/`5e13395`/`abfcdca` *did* eventually resolve, two
rounds ago, once the branch was actually pushed — but `d90b69a` last
round and `785ddab` this round have not). This round additionally
supplied detailed numeric "known facts" directly in the prompt rather
than only a commit reference. I am reporting this plainly, not
accusingly: if there is a sync delay, a wrong SHA, or a different
intended repository, resolving that is the fastest path to a real
analysis. I did not treat the repetition itself as evidence the numbers
are fabricated — only as a reason the standing verify-before-acting rule
applies with the same weight it always has.

CLAUDE_V3_TELEMETRY_INSUFFICIENT
