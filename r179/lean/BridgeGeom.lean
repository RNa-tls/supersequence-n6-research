/-
Round 179 -- geometric (non-arithmetic) lemmas of Bridge(n), for words of ANY length.
Core Lean 4 only (no Mathlib).  Words are `List α`; no length is fixed.

  rot  = R  (cyclic rotation left by one)
  F        = rotate all but the last symbol (the insertion-block step)
  N2       = proper cost-two successor  x1 x2 x3..xn  |->  x3..xn x2 x1

Proved here:
  * `F_rot_eq_N2`     : F (R y) = N2 y                       (Bridge B3, general n)
  * `F_rot_rotInv`    : the proper cost-2 successor of R^{-1} z is F z  (run-end lemma)
  * `rot_iter`        : iter R i l = drop i l ++ take i l  (i <= length)
  * `rot_period`      : iter R length l = l
  * `F_period`        : iter F m (init ++ [z]) = init ++ [z]  where m = init.length
                        (a block has exactly n-1 states; "last state = F^{-1} x", B7)
-/

namespace BridgeGeom

variable {α : Type}

def rot : List α → List α
  | [] => []
  | a :: l => l ++ [a]

def N2 : List α → List α
  | x1 :: x2 :: rest => rest ++ [x2, x1]
  | l => l

/-- F: rotate all symbols except the last one. -/
def F (l : List α) : List α :=
  match l.reverse with
  | [] => []
  | z :: restRev => rot restRev.reverse ++ [z]

/-- k-fold iterate, `iter f (k+1) x = f (iter f k x)` (core Lean has no `f^[k]` notation). -/
def iter (f : List α → List α) : Nat → List α → List α
  | 0, x => x
  | k + 1, x => f (iter f k x)

theorem F_append_single (init : List α) (z : α) : F (init ++ [z]) = rot init ++ [z] := by
  simp [F]

theorem F_rot_eq_N2 (y1 y2 : α) (rest : List α) :
    F (rot (y1 :: y2 :: rest)) = N2 (y1 :: y2 :: rest) := by
  simp only [rot, N2]
  rw [show y2 :: rest ++ [y1] = (y2 :: rest) ++ [y1] from rfl, F_append_single]
  simp [rot]

/-- If z = R x (i.e. x = R^{-1} z), the proper cost-two successor of x is F z. -/
theorem F_rot_rotInv (y1 y2 : α) (rest : List α) :
    N2 (y1 :: y2 :: rest) = F (rot (y1 :: y2 :: rest)) :=
  (F_rot_eq_N2 y1 y2 rest).symm

theorem rot_eq_drop_take (l : List α) : rot l = l.drop 1 ++ l.take 1 := by
  cases l with
  | nil => rfl
  | cons a t => simp [rot]

theorem rot_iter (l : List α) : ∀ i, i ≤ l.length → iter rot i l = l.drop i ++ l.take i := by
  intro i
  induction i with
  | zero => intro _; simp [iter]
  | succ j ih =>
    intro hj
    have hj' : j ≤ l.length := Nat.le_of_succ_le hj
    rw [iter, ih hj']
    -- rot (drop j l ++ take j l), with drop j l nonempty since j < length
    have hlt : j < l.length := Nat.lt_of_succ_le hj
    obtain ⟨a, t, hdrop⟩ : ∃ a t, l.drop j = a :: t := by
      cases h : l.drop j with
      | nil =>
        have := List.length_drop (l := l) (i := j)
        rw [h] at this; simp at this; omega
      | cons a t => exact ⟨a, t, rfl⟩
    rw [hdrop]
    simp only [rot, List.cons_append]
    have h1 : l.drop (j + 1) = t := by
      rw [← List.drop_drop, hdrop]; simp
    have h2 : l.take (j + 1) = l.take j ++ [a] := by
      rw [List.take_succ, List.getElem?_eq_getElem hlt]
      have : l[j] = a := by
        have := congrArg List.head? hdrop
        simp [List.head?_drop] at this
        simpa [List.getElem?_eq_getElem hlt] using this
      simp [this]
    rw [h1, h2]
    simp

theorem rot_period (l : List α) : iter rot l.length l = l := by
  rw [rot_iter l l.length (Nat.le_refl _)]
  simp

theorem F_iter (init : List α) (z : α) : ∀ i, iter F i (init ++ [z]) = iter rot i init ++ [z] := by
  intro i
  induction i with
  | zero => simp [iter]
  | succ j ih =>
    rw [iter, ih, F_append_single, iter]

theorem F_period (init : List α) (z : α) : iter F init.length (init ++ [z]) = init ++ [z] := by
  rw [F_iter, rot_period]

end BridgeGeom

#print axioms BridgeGeom.F_rot_eq_N2
#print axioms BridgeGeom.F_rot_rotInv
#print axioms BridgeGeom.rot_iter
#print axioms BridgeGeom.rot_period
#print axioms BridgeGeom.F_period
