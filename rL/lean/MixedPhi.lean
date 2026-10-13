/-!
# Round L, LEMMA D: a mixed phi-set costs at least one unit of fragmentation

Two-world routes (specials a, b) cover each phi-set `P = P({a,b}, C)` (42 classes) by world-a
segments of its 6 columns (world-a orbits) and world-b segments of its 6 rows (world-b orbits);
every row meets every column.  Let `A` = classes with special a, `B` = the rest, `α` = number of
columns meeting `A`, `β` = number of rows meeting `B`.  The fragmentation inside `P` satisfies

    7 E_P ≥ Σ_{cols meeting A} (7 - |A ∩ col|) + Σ_{rows meeting B} (7 - |B ∩ row|)
          = 7 (α + β) - 42                                         (columns, rows have 7 cells)

and the combinatorial core proved here is `A, B ≠ ∅ → α + β ≥ 7`, hence `E_P ≥ 1`.
(The exact minimum over all mixed configurations, `min E_P = min(⌈k/7⌉, ⌈(42-k)/7⌉)` for `k`
world-b classes, is computed by MIP in `rL/src/phi_mixed_min.py`.)

Core Lean 4, no Mathlib.  Uses classical logic for the counts.
-/

namespace MixedPhi

open Classical

/-- number of `k : Fin 6` satisfying `p` -/
noncomputable def cnt6 (p : Fin 6 → Prop) : Nat :=
  (if p 0 then 1 else 0) + (if p 1 then 1 else 0) + (if p 2 then 1 else 0) +
  (if p 3 then 1 else 0) + (if p 4 then 1 else 0) + (if p 5 then 1 else 0)

theorem cnt6_all (p : Fin 6 → Prop) (h : ∀ k, p k) : cnt6 p = 6 := by
  unfold cnt6
  simp [h]

theorem cnt6_pos (p : Fin 6 → Prop) (k : Fin 6) (h : p k) : cnt6 p ≥ 1 := by
  unfold cnt6
  match k, h with
  | ⟨0, _⟩, h => have h' : p 0 := h; simp only [if_pos h']; omega
  | ⟨1, _⟩, h => have h' : p 1 := h; simp only [if_pos h']; omega
  | ⟨2, _⟩, h => have h' : p 2 := h; simp only [if_pos h']; omega
  | ⟨3, _⟩, h => have h' : p 3 := h; simp only [if_pos h']; omega
  | ⟨4, _⟩, h => have h' : p 4 := h; simp only [if_pos h']; omega
  | ⟨5, _⟩, h => have h' : p 5 := h; simp only [if_pos h']; omega

/-- combinatorial core: if both specials occur, the active columns and rows number at least 7 -/
theorem active_ge_seven (S : Type) (row col : S → Fin 6)
    (H : ∀ i j, ∃ x, row x = i ∧ col x = j)
    (A : S → Prop) (hA : ∃ x, A x) (hB : ∃ x, ¬ A x) :
    cnt6 (fun j => ∃ x, col x = j ∧ A x) + cnt6 (fun i => ∃ x, row x = i ∧ ¬ A x) ≥ 7 := by
  by_cases hall : ∀ j, ∃ x, col x = j ∧ A x
  · have h1 := cnt6_all _ hall
    obtain ⟨y, hy⟩ := hB
    have h2 := cnt6_pos (fun i => ∃ x, row x = i ∧ ¬ A x) (row y) ⟨y, rfl, hy⟩
    omega
  · have ⟨j0, hj0⟩ : ∃ j0, ¬ ∃ x, col x = j0 ∧ A x :=
      Classical.byContradiction fun hne =>
        hall fun j => Classical.byContradiction fun hj => hne ⟨j, hj⟩
    have hrow : ∀ i, ∃ x, row x = i ∧ ¬ A x := by
      intro i
      obtain ⟨x, hxr, hxc⟩ := H i j0
      exact ⟨x, hxr, fun hax => hj0 ⟨x, hxc, hax⟩⟩
    have h1 := cnt6_all _ hrow
    obtain ⟨x, hx⟩ := hA
    have h2 := cnt6_pos (fun j => ∃ x, col x = j ∧ A x) (col x) ⟨x, rfl, hx⟩
    omega

/-- arithmetic step: `7 E_P ≥ 7(α+β) - 42` and `α + β ≥ 7` give `E_P ≥ 1` (in sevenths: `≥ 7`) -/
theorem mixed_cost (sevenE α β : Nat) (hdef : sevenE + 42 ≥ 7 * (α + β)) (hab : α + β ≥ 7) :
    sevenE ≥ 7 := by
  omega

/-- the phi-set grid: cells `(i, j, d)`; row = position of a, column = position of b; every row
meets every column (for `i = j` the two cells `d = false/true` are the orders `ab`, `ba`) -/
def gridRow (x : Fin 6 × Fin 6 × Bool) : Fin 6 := x.1
def gridCol (x : Fin 6 × Fin 6 × Bool) : Fin 6 := x.2.1

theorem grid_meets : ∀ i j : Fin 6, ∃ x, gridRow x = i ∧ gridCol x = j :=
  fun i j => ⟨(i, j, false), rfl, rfl⟩

theorem phi_set_mixed (A : Fin 6 × Fin 6 × Bool → Prop) (hA : ∃ x, A x) (hB : ∃ x, ¬ A x) :
    cnt6 (fun j => ∃ x, gridCol x = j ∧ A x) + cnt6 (fun i => ∃ x, gridRow x = i ∧ ¬ A x) ≥ 7 :=
  active_ge_seven _ gridRow gridCol grid_meets A hA hB

end MixedPhi
