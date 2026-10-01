/-
Final round -- Lemma C0 (word core), core Lean 4 only.  Repairs the load-bearing input C1(g=0).
Row start p = (a :: beta ++ [b]) ++ [s]  (n = |beta| + 3).  Block states: iter F i p, i < n-1, and
iter F i (init ++ [z]) = iter rot i init ++ [z]  (F_iter, as in r179 BridgeGeom).
A compatible successor start has the form beta ++ sigma(a, b, s) for one of the 6 orders sigma.
Proved: for each order except (a, b, s) [= phi p] the successor is either a state of p's own block
(order (b, a, s): it equals F p) or has a state with index <= |beta| < n-1 that is a ROTATION
(same cyclic class) of a state of p with index in {0, 1, |beta|+1} (all < n-1).  Hence if p is a
full row, no full row other than phi p can follow it (both states visible => shared visible class),
and a charge-0 trail is p, phi p, ..., i.e. at most n-2 rows since phi has order n-2:  C1(0).
-/
namespace C0Core

variable {α : Type}

def rot : List α → List α
  | [] => []
  | a :: l => l ++ [a]

def iter (f : List α → List α) : Nat → List α → List α
  | 0, x => x
  | k + 1, x => f (iter f k x)

/-- F: rotate all symbols except the last one. -/
def F (l : List α) : List α :=
  match l.reverse with
  | [] => []
  | z :: restRev => rot restRev.reverse ++ [z]

theorem F_append_single (init : List α) (z : α) : F (init ++ [z]) = rot init ++ [z] := by
  simp [F]

theorem F_iter (init : List α) (z : α) : ∀ i, iter F i (init ++ [z]) = iter rot i init ++ [z] := by
  intro i
  induction i with
  | zero => simp [iter]
  | succ j ih => rw [iter, ih, F_append_single, iter]

theorem rot_iter (l : List α) : ∀ i, i ≤ l.length → iter rot i l = l.drop i ++ l.take i := by
  intro i
  induction i with
  | zero => intro _; simp [iter]
  | succ j ih =>
    intro hj
    have hj' : j ≤ l.length := Nat.le_of_succ_le hj
    rw [iter, ih hj']
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

/-- rotating `A ++ B` by |A| gives `B ++ A`. -/
theorem rot_split (A B : List α) : iter rot A.length (A ++ B) = B ++ A := by
  rw [rot_iter _ _ (by simp)]; simp

variable (a b s : α) (β : List α)

/-- order (a, b, s): phi p -- the only order that can carry a full successor. -/
def phiStart : List α := β ++ [a, b] ++ [s]

/-- order (b, a, s): the successor start is F p, a state of the same block. -/
theorem order_bas : β ++ [b, a] ++ [s] = iter F 1 ((a :: β ++ [b]) ++ [s]) := by
  rw [F_iter]; simp [iter, rot]

/-- order (b, s, a): successor start (its state 0) = rot (state 0 of p). -/
theorem order_bsa : β ++ [b, s] ++ [a] = rot ((a :: β ++ [b]) ++ [s]) := by
  simp [rot]

/-- order (s, b, a): successor start (state 0) = rot^2 (state |beta|+1 of p). -/
theorem order_sba :
    β ++ [s, b] ++ [a] = rot (rot (iter F (β.length + 1) ((a :: β ++ [b]) ++ [s]))) := by
  rw [F_iter]
  have : iter rot (β.length + 1) (a :: β ++ [b]) = [b] ++ (a :: β) := by
    have h := rot_split (a :: β) [b]
    simpa using h
  rw [this]; simp [rot]

/-- order (a, s, b): state |beta| of the successor = rot^(|beta|+1) (state 1 of p). -/
theorem order_asb :
    iter F β.length ((β ++ [a, s]) ++ [b])
      = iter rot (β.length + 1) (iter F 1 ((a :: β ++ [b]) ++ [s])) := by
  rw [F_iter, F_iter]
  have h1 : iter rot β.length (β ++ [a, s]) = [a, s] ++ β := rot_split β [a, s]
  rw [h1]
  have h2 : iter rot 1 (a :: β ++ [b]) ++ [s] = (β ++ [b]) ++ [a, s] := by simp [iter, rot]
  rw [h2]
  have h3 : iter rot (β ++ [b]).length ((β ++ [b]) ++ [a, s]) = [a, s] ++ (β ++ [b]) :=
    rot_split (β ++ [b]) [a, s]
  simp only [List.length_append, List.length_singleton] at h3
  rw [h3]; simp

/-- order (s, a, b): state |beta| of the successor = rot^(|beta|+2) (state 0 of p). -/
theorem order_sab :
    iter F β.length ((β ++ [s, a]) ++ [b])
      = iter rot (β.length + 2) ((a :: β ++ [b]) ++ [s]) := by
  rw [F_iter]
  have h1 : iter rot β.length (β ++ [s, a]) = [s, a] ++ β := rot_split β [s, a]
  rw [h1]
  have h3 : iter rot (a :: β ++ [b]).length ((a :: β ++ [b]) ++ [s]) = [s] ++ (a :: β ++ [b]) :=
    rot_split (a :: β ++ [b]) [s]
  have hl : (a :: β ++ [b]).length = β.length + 2 := by simp
  rw [hl] at h3
  rw [h3]; simp

end C0Core

#print axioms C0Core.order_bas
#print axioms C0Core.order_bsa
#print axioms C0Core.order_sba
#print axioms C0Core.order_asb
#print axioms C0Core.order_sab
