/-
Round W -- Lean 4 core only (no Mathlib).

1. `ins_lemma`: the letter-level insertion lemma for windows of any length `n` over any alphabet.  Windows are
   functions `Nat → α`; "the last `n - w` letters of `x` are the first `n - w` letters of `y`" is
   `Over n w x y := ∀ j, j + w < n → x (w + j) = y j` (a step of weight at most `w`).
   If a piece starts with `P1` and ends with `T`, its cut link `T → P1` has weight `wi`, its predecessor ends
   with `X` (`X → P1` of weight `w1`) and its successor starts with `Y` (`T → Y` of weight `w2`), and
   `wi ≤ w1`, `wi ≤ w2`, then `X → Y` has weight at most `w1 + w2 - wi`.
2. `sum_ge_conv`: for chains with `r_i` pieces and deficits `d_i ≥ f r_i`, the total deficit is at least
   `conv f m (Σ r_i)`, the `m`-fold min-plus convolution, given as any function `P` with
   `P 0 0 = 0` and `P (m+1) (x + r) ≤ P m x + f r` (the knapsack tables of `rW/src/frontier.py` are such `P`).
3. `junction_bound`: the deficit accounting of a cell with free junctions (end pieces cut off).
-/

def Over {α : Type} (n w : Nat) (x y : Nat → α) : Prop := ∀ j, j + w < n → x (w + j) = y j

theorem ins_lemma {α : Type} (n wi w1 w2 : Nat) (X P1 T Y : Nat → α)
    (h1 : Over n w1 X P1) (hi : Over n wi T P1) (h2 : Over n w2 T Y)
    (hw1 : wi ≤ w1) (hw2 : wi ≤ w2) : Over n (w1 + w2 - wi) X Y := by
  intro j hj
  -- Y j = T (w2 + j) = P1 (w2 + j - wi) = X (w1 + (w2 + j - wi)) = X (w1 + w2 - wi + j)
  have e2 : T (w2 + j) = Y j := h2 j (by omega)
  have ei : T (wi + (w2 - wi + j)) = P1 (w2 - wi + j) := hi (w2 - wi + j) (by omega)
  have e1 : X (w1 + (w2 - wi + j)) = P1 (w2 - wi + j) := h1 (w2 - wi + j) (by omega)
  have a1 : wi + (w2 - wi + j) = w2 + j := by omega
  have a2 : w1 + (w2 - wi + j) = w1 + w2 - wi + j := by omega
  rw [a1] at ei
  rw [a2] at e1
  rw [e1, ← ei, e2]

/-- The insertion cost is nonnegative: `w(X,Y) ≤ w1 + w2 - wi` in the weight form `ins = w1 + w2 - w3 - wi ≥ 0`. -/
theorem ins_nonneg (w1 w2 w3 wi : Nat) (h : w3 ≤ w1 + w2 - wi) (hw : wi ≤ w1) : 0 ≤ (w1 : Int) + w2 - w3 - wi := by
  omega

/-! ### The knapsack bound -/

/-- Sum of a list of naturals. -/
def lsum : List Nat → Nat
  | [] => 0
  | a :: l => a + lsum l

/-- Chains are pairs (pieces, deficit). -/
theorem sum_ge_conv (f : Nat → Nat) (P : Nat → Nat → Nat)
    (h0 : P 0 0 = 0) (hstep : ∀ m x r, P (m + 1) (x + r) ≤ P m x + f r) :
    ∀ (L : List (Nat × Nat)), (∀ c ∈ L, f c.1 ≤ c.2) →
      P L.length (lsum (L.map Prod.fst)) ≤ lsum (L.map Prod.snd) := by
  intro L
  induction L with
  | nil => intro _; simp [lsum, h0]
  | cons c L ih =>
    intro hL
    have hc : f c.1 ≤ c.2 := hL c (List.mem_cons_self ..)
    have hr : ∀ d ∈ L, f d.1 ≤ d.2 := fun d hd => hL d (List.mem_cons_of_mem _ hd)
    have ih' := ih hr
    have hs := hstep L.length (lsum (L.map Prod.fst)) c.1
    simp only [List.length_cons, List.map_cons, lsum]
    have e : c.1 + lsum (L.map Prod.fst) = lsum (L.map Prod.fst) + c.1 := by omega
    rw [e]
    omega

/-- The cell accounting with free junctions: the deficit is the deficit of the remaining chains plus the deficits
of the end pieces; pairs give at least 8 each, less at most 6 for every row shared by two pairs; loops give at
least 1 each. -/
theorem junction_bound (Dchains Dends Dloops Fii Fi s B : Nat)
    (hc : B ≤ Dchains) (he : 8 * Fii ≤ Dends + 6 * s) (hl : Fi ≤ Dloops) :
    B + Fi + 8 * Fii - 6 * s ≤ Dchains + Dends + Dloops := by
  omega

#print axioms ins_lemma
#print axioms ins_nonneg
#print axioms sum_ge_conv
#print axioms junction_bound
