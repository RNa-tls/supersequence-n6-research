# Stale pre-R-only checkpoint namespace

`short_ell0.json` and `recovery_backups/` in this directory were written by
the pre-correction short-root traversal.  That implementation terminalized
every R edge, so it did not enqueue the first R child of an `r_count=0` short
root.  These files are retained only for forensic comparison and must never
be resumed or used for a completeness conclusion.

Corrected searches use the sibling namespace `r1_complete_v2/`.  See
`research/RR_SHORT5_R1_COMPLETENESS_CORRECTION_CODEX.md` and
`outputs/rr_short5_r1_completeness_audit.json`.
