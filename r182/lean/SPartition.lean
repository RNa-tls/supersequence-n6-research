/-
Round 182 -- Lemma S (s-partition) of the r181 report, geometric core, core Lean 4 only.
A cyclic class is the rotation orbit of a duplicate-free word l (length n); the block of special s
containing the class is determined by the unique rotation that ENDS in s.  Proved here:
  * `rot_last`   : for 1 <= i <= n, the i-th rotation ends in l[i-1];
  * `S_exists`   : if s ∈ l, some rotation i ∈ [1, n] ends in s;
  * `S_unique`   : if l is duplicate-free, at most one i ∈ [1, n] does.
Hence every class meets exactly one s-block (and in exactly one state): the s-blocks partition
the classes.  (That a block's n-1 states lie in distinct classes, and the identification
"rotation ending in s <-> block (W, s)", are definitional/elementary and not formalized.)
-/
namespace SPartition

variable {α : Type}

def rot : List α → List α
  | [] => []
  | a :: l => l ++ [a]

def iter (f : List α → List α) : Nat → List α → List α
  | 0, x => x
  | k + 1, x => f (iter f k x)

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

theorem rot_last (l : List α) (i : Nat) (h1 : 1 ≤ i) (h2 : i ≤ l.length) :
    (iter rot i l).getLast? = l[i - 1]? := by
  rw [rot_iter l i h2, List.getLast?_append]
  have ht : (l.take i).getLast? = l[i - 1]? := by
    rw [List.getLast?_eq_getElem?, List.length_take, List.getElem?_take]
    have : min i l.length = i := Nat.min_eq_left h2
    rw [this]
    have : i - 1 < i := by omega
    simp [this]
  rw [ht]
  have : l[i - 1]?.isSome := by
    rw [List.getElem?_eq_getElem (by omega)]; rfl
  cases hh : l[i - 1]? with
  | none => rw [hh] at this; simp at this
  | some v => simp

theorem S_exists (l : List α) (s : α) (hs : s ∈ l) :
    ∃ i, 1 ≤ i ∧ i ≤ l.length ∧ (iter rot i l).getLast? = some s := by
  obtain ⟨j, hj, hjs⟩ := List.getElem_of_mem hs
  refine ⟨j + 1, by omega, by omega, ?_⟩
  rw [rot_last l (j + 1) (by omega) (by omega)]
  simp [List.getElem?_eq_getElem hj, hjs]

theorem S_unique (l : List α) (s : α) (hnd : l.Nodup) (i j : Nat)
    (hi1 : 1 ≤ i) (hi2 : i ≤ l.length) (hj1 : 1 ≤ j) (hj2 : j ≤ l.length)
    (hi : (iter rot i l).getLast? = some s) (hj : (iter rot j l).getLast? = some s) : i = j := by
  rw [rot_last l i hi1 hi2, List.getElem?_eq_getElem (by omega)] at hi
  rw [rot_last l j hj1 hj2, List.getElem?_eq_getElem (by omega)] at hj
  have hi' := Option.some.inj hi
  have hj' := Option.some.inj hj
  have : l[i - 1]'(by omega) = l[j - 1]'(by omega) := by rw [hi', hj']
  have hp := List.pairwise_iff_getElem.1 hnd
  rcases Nat.lt_trichotomy (i - 1) (j - 1) with hlt | heq | hgt
  · exact absurd this (hp (i - 1) (j - 1) (by omega) (by omega) hlt)
  · omega
  · exact absurd this.symm (hp (j - 1) (i - 1) (by omega) (by omega) hgt)

end SPartition

#print axioms SPartition.rot_last
#print axioms SPartition.S_exists
#print axioms SPartition.S_unique
