# Root ledger: the count units, disambiguated

Round 38, Part B.

## 1. The problem

The number **7** has been used for two entirely unrelated objects, and
"7 remaining roots" is ambiguous between two different *questions* about
the same 33 roots.

## 2. The corrected ledger

```
33  audited roots total          = 5 short-family + 6 long-FOUND + 22 long-INCOMPLETE
```

Split by **Q2** (is there a Target A boundary that could still complete?):

```
28  roots certified Q2-IMPOSSIBLE   (all 28 long-excursion roots; Round 37 envelope)
 5  roots UNRESOLVED for Q2         (the 5 short-family roots, envelope +14)
--
33
```

Split by **Q1** (is there any Target A boundary at all?):

```
26  roots FOUND_TARGET_A            (1,398 boundaries between them)
 7  roots INCOMPLETE_TIMEOUT        (5 short-family + long_q1_140 + long_q1_178)
--
33
```

The continuation-management stage of Round 37 audited exactly those **7
Q1-incomplete roots**, and the Round 37 envelope then closed **2** of them
(`long_q1_140`, `long_q1_178`) **for Q2**:

```
 7  audited in the continuation stage
 2  newly closed for Q2 by the root envelope
 5  final unresolved short roots
```

**Both "7" and "5" are correct — of different questions.** 7 is the Q1
count; 5 is the Q2 count. The 2 that differ are Q2-closed but still
Q1-open, because the envelope theorem is Q2-only machinery and says
nothing about Q1 by construction.

## 3. The unrelated collision

Rounds 32–34 also speak of **"the 7 remaining survivors."** That 7 counts
**Target B boundary STATES** (7 of the 18 currently known Target A
boundaries survived the capacity theorem and were exhaustively searched for
Target B in Round 34). It has no relationship whatsoever to the 7 Q1-
incomplete **roots**. Different object, different unit, coincidentally the
same integer.

| phrase | unit | object | value |
|---|---|---|---|
| "7 remaining survivors" (R32–34) | boundary **states** | Target B survivors of the known 18 | 7 |
| "7 incomplete roots" (R36–37) | search **roots** | roots whose Q1 search timed out | 7 |
| "5 unresolved roots" (R37–38) | search **roots** | roots not closed for Q2 | 5 |
| "28 closed roots" (R37) | search **roots** | roots certified Q2-impossible | 28 |
| "1,398 boundaries" (R36) | boundary **states** = words | Q1 boundaries found | 1,398 |
| "18 currently known" | boundary **states** | the historical Target A corpus | 18 |

## 4. Edits applied

* `STATUS.md`, Round 32 section — "the 7 remaining survivors" now reads
  "the 7 remaining Target B BOUNDARY survivors (a boundary-state count,
  unrelated to the later 7-ROOT continuation-audit count)".
* `STATUS.md`, Round 37 section — "converting 2 of the 7
  previously-INCOMPLETE roots" now names the unit explicitly and states
  that the Q2-unresolved count is 5.
* `research/RR_INCOMPLETE_ROOT_AUDIT.md` — a count-unit warning box at the
  top.
* `research/RR_ENUMERATOR_CORRECTNESS.md` — "7 of 33 roots" now carries
  "by the Q1 count unit" and names the Q2 count alongside.

## 5. The invariants a test now enforces

```
33 == 28 + 5          (Q2 split)
33 == 26 + 7          (Q1 split)
 7 ==  2 + 5          (continuation-stage split)
```

`tests/test_rr_capacity_soundness.py` asserts all three against the live
JSON outputs, so a future drift in any of these counts fails immediately
rather than propagating into prose.
