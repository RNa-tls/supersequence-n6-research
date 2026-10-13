/-!
# Round L, section 1: audit of the r = 0 target inequality (n = 8)

Length identity of r = 0 routes (Round I, `rI/lean/R0Identity.lean`):

    L = 45364 + q + τ + λ,

`q` = number of chains, `τ` = number of trails, `λ = Σ (c - 4)` over the joins between trails.
With `E = q - 720` (fragmentation, `q ≥ 720`) this is `L = 46085 + E + (τ - 1) + λ`.

The Round K report wrote the target as `Σ (k_T + 1) + λ ≥ 822` (`Σ (k_T+1) = q + τ`).
That threshold only gives `L ≥ 46186`; the correct threshold for `L ≥ 46187` is `823`,
equivalently `E + (τ - 1) + λ ≥ 102`, or `Σ s_T - λ ≤ 17` with `Σ s_T = 840 - (q + τ)`.

Core Lean 4, no Mathlib, no axioms beyond the standard ones.
-/

namespace TargetAudit

/-- the length of an r = 0 route in terms of its chain / trail / linking counts -/
def len (q τ lam : Nat) : Nat := 45364 + q + τ + lam

theorem target_823 (q τ lam : Nat) : len q τ lam ≥ 46187 ↔ q + τ + lam ≥ 823 := by
  unfold len; omega

/-- the Round K threshold 822 is one short: it is equivalent to `L ≥ 46186` only -/
theorem threshold_822 (q τ lam : Nat) : len q τ lam ≥ 46186 ↔ q + τ + lam ≥ 822 := by
  unfold len; omega

theorem threshold_822_not_enough : len 720 101 1 = 46186 ∧ 720 + 101 + 1 = 822 := by
  unfold len; decide

/-- fragmentation form: `L = 46085 + E + (τ - 1) + λ`, `E = q - 720` -/
theorem frag_form (q τ lam : Nat) (hq : q ≥ 720) (hτ : τ ≥ 1) :
    len q τ lam = 46085 + (q - 720) + (τ - 1) + lam := by
  unfold len; omega

theorem target_frag (q τ lam : Nat) (hq : q ≥ 720) (hτ : τ ≥ 1) :
    len q τ lam ≥ 46187 ↔ (q - 720) + (τ - 1) + lam ≥ 102 := by
  unfold len; omega

/-- saving form: with `S = 840 - (q + τ)` (as an integer), `L = 46204 - S + λ` -/
theorem saving_form (q τ lam : Nat) :
    (len q τ lam : Int) = 46204 - (840 - ((q : Int) + τ)) + lam := by
  unfold len; omega

theorem target_saving (q τ lam : Nat) :
    len q τ lam ≥ 46187 ↔ (840 - ((q : Int) + τ)) - lam ≤ 17 := by
  unfold len; omega

/-- the three record words: `q = 768`, `τ = 32` and `λ = 23` (46187) or `λ = 24` (46188) -/
theorem records : len 768 32 23 = 46187 ∧ len 768 32 24 = 46188 ∧
    (768 - 720) + (32 - 1) + 23 = 102 := by
  unfold len; decide

end TargetAudit
