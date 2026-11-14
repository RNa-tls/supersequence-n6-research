/-
Round Z -- Lean 4 core only (no Mathlib).

1. `seam_entry_b`, `seam_entry_e`, `seam_entry_d_c_f`: the seam-entry identities as identities of words (lists).
   A class is a rotation class of words; the next class of a 2-cycle is obtained by moving the moving symbol z past its
   right neighbour.  For an exit `z v1 v2 y4 .. y8`:
   * the b entry `y4..y8 v1 z v2` is a rotation of `v1 z v2 y4..y8`, the class after the exit class (z moved past v1);
   * the e entry `y4..y8 v1 v2 z` is a rotation of `v1 v2 z y4..y8`, two classes on (z moved past v1 and v2);
   * the d entry `y4..y8 v2 v1 z`, the c entry `y4..y8 z v2 v1` and the f entry `y4..y8 v2 z v1` are rotations of
     words of the 2-cycle obtained by exchanging v1 and v2, with z at three consecutive places (c, f, d).
   (The exhaustive check over all 40320 exits is `rZ/src/seam_entry_identities.py`.)
2. `ends_or_next_to_true_le`: in a sequence of `m + 1` rows with `m` seams, the rows that are a chain end or next to a
   marked seam number at most `2 * (#marked) + 2`  (the counting half of the 6-row lemma Z1).
3. `six_row_lemma`: the arithmetic of Lemma Z1:  P6 = A + B, A + E <= M, B <= 2 (L + E) + 2 n  gives
   P6 <= M + E + 2 L + 2 n.
4. `block_full_side`: in a 6 x 6 block, if every cell has its row or its column used, then all rows or all columns
   are used;  `block_overlap`: then the block's overlap is W_B = 7 (a + b - 6).
5. `priced_line_cover`: from the priced line v + lam L <= c for every chain, summed: lam * sum L <= c n - sum v.
   `hamiltonian_769_label_changes`: a single chain with 769 rows and 343 holes has at most 16 symbol changes
   (line 4r - 9d + 4L <= 56, proved by the exhaustive search `rZ/csrc/dsearch_lab.c`).
-/

/-! ### 1. Seam entries -/

section Seam
variable {α : Type} (z v1 v2 y4 y5 y6 y7 y8 : α)

/-- Rotation of a word by three letters (the first three letters go to the end). -/
def rot3 (l : List α) : List α := l.drop 3 ++ l.take 3

/-- b: the entry `y4..y8 v1 z v2` is the rotation by 3 of `v1 z v2 y4..y8`. -/
theorem seam_entry_b : rot3 [v1, z, v2, y4, y5, y6, y7, y8] = [y4, y5, y6, y7, y8, v1, z, v2] := rfl

/-- The exit class `z v1 v2 y4..y8` with z moved past v1 is `v1 z v2 y4..y8`: the b entry is the next class of the
exit's 2-cycle.  (Moving z past its right neighbour: swap the first two letters of a word that starts with z.) -/
theorem next_class_of_exit : (fun l : List α => match l with | a :: b :: t => b :: a :: t | l => l)
    [z, v1, v2, y4, y5, y6, y7, y8] = [v1, z, v2, y4, y5, y6, y7, y8] := rfl

/-- e: the entry `y4..y8 v1 v2 z` is the rotation by 3 of `v1 v2 z y4..y8` (z moved past v1 and v2). -/
theorem seam_entry_e : rot3 [v1, v2, z, y4, y5, y6, y7, y8] = [y4, y5, y6, y7, y8, v1, v2, z] := rfl

/-- d, c, f: rotations of the words of the 2-cycle of `v2 v1 y4 .. y8` (v1, v2 exchanged) with z placed after v1 (d),
before v2 (c) and between v2 and v1 (f). -/
theorem seam_entry_d_c_f :
    rot3 [v2, v1, z, y4, y5, y6, y7, y8] = [y4, y5, y6, y7, y8, v2, v1, z] ∧
    rot3 [z, v2, v1, y4, y5, y6, y7, y8] = [y4, y5, y6, y7, y8, z, v2, v1] ∧
    rot3 [v2, z, v1, y4, y5, y6, y7, y8] = [y4, y5, y6, y7, y8, v2, z, v1] := ⟨rfl, rfl, rfl⟩

end Seam

/-! ### 2. Rows next to marked seams -/

/-- Number of `true` entries. -/
def cntTrue : List Bool → Nat
  | [] => 0
  | true :: l => cntTrue l + 1
  | false :: l => cntTrue l

/-- For seams `s = [s₁, …, s_m]` between rows `0 … m`, `nearCount prev s` counts the rows `1 … m` that are next to a
marked seam (the seam before or after them) or are the last row; `prev` = the seam before row 1 is marked. -/
def nearCount : Bool → List Bool → Nat
  | _, [] => 1                                     -- the last row is a chain end
  | p, s :: l => (if p || s then 1 else 0) + nearCount s l

theorem nearCount_le : ∀ (l : List Bool) (p : Bool), nearCount p l ≤ 2 * cntTrue l + (if p then 1 else 0) + 1
  | [], p => by cases p <;> simp [nearCount, cntTrue]
  | s :: l, p => by
    have ih := nearCount_le l s
    cases p <;> cases s <;> simp [nearCount, cntTrue] at ih ⊢ <;> omega

/-- **Counting half of Lemma Z1.**  Rows `0 … m` of one chain, seams `l`: the rows that are a chain end or next to a
marked seam are at most `2 * #marked + 2` (row 0 is a chain end and is counted separately). -/
theorem ends_or_next_to_true_le (l : List Bool) : 1 + nearCount false l ≤ 2 * cntTrue l + 2 := by
  have := nearCount_le l false
  simp at this
  omega

/-! ### 3. The 6-row lemma (arithmetic) -/

/-- `P6 = A + B` with `A` the 6-rows entered and left by d (each sandwiched between two rows of one 2-cycle, so that
`A + E ≤ M`) and `B` the 6-rows next to a non-d seam or a chain end (`B ≤ 2 (L + E) + 2 n`). -/
theorem six_row_lemma (P6 A B E M L n : Nat) (h0 : P6 = A + B) (h1 : A + E ≤ M) (h2 : B ≤ 2 * (L + E) + 2 * n) :
    P6 ≤ M + E + 2 * L + 2 * n := by omega

/-! ### 4. Two-world blocks -/

theorem all_of_forall : ∀ cols : List Bool, (∀ c ∈ cols, c = true) → cols.all id = true
  | [], _ => rfl
  | c :: cs, h => by
    have hc : c = true := h c (List.Mem.head cs)
    have ih := all_of_forall cs (fun x hx => h x (List.Mem.tail c hx))
    subst hc
    simp only [List.all_cons, id, Bool.true_and]
    exact ih

/-- If every cell of a block has its row or its column used, then all rows or all columns are used
(rows and columns given as lists of flags; constructive). -/
theorem block_full_side : ∀ rows cols : List Bool,
    (∀ r ∈ rows, ∀ c ∈ cols, r = true ∨ c = true) → rows.all id = true ∨ cols.all id = true
  | [], _, _ => Or.inl rfl
  | r :: rs, cols, h => by
    cases r with
    | true =>
      have ih := block_full_side rs cols (fun x hx c hc => h x (List.Mem.tail true hx) c hc)
      cases ih with
      | inl h1 => left; simp only [List.all_cons, id, Bool.true_and]; exact h1
      | inr h1 => exact Or.inr h1
    | false =>
      right
      apply all_of_forall
      intro c hc
      cases h false (List.Mem.head rs) c hc with
      | inl h1 => exact absurd h1 Bool.false_ne_true
      | inr h1 => exact h1

/-- The block has 42 classes; its `a` used rows and `b` used columns each have 7 classes, every class lies in at least
one of them, and the overlap is `W_B = (7 a + 7 b) - 42`.  With `a = 6` or `b = 6` this is `7 (a + b - 6)`. -/
theorem block_overlap (a b WB : Nat) (hW : WB + 42 = 7 * a + 7 * b) : WB = 7 * (a + b - 6) := by omega

/-! ### 5. Priced lines and the 769-row chain -/

def sumL : List (Int × Nat) → Int
  | [] => 0
  | (_, x) :: l => (x : Int) + sumL l

def sumV : List (Int × Nat) → Int
  | [] => 0
  | (v, _) :: l => v + sumV l

/-- Every chain `(v, L)` of a cover satisfies `v + lam L ≤ c`; then `lam Σ L ≤ c n - Σ v`. -/
theorem priced_line_cover (lam c : Int) : ∀ l : List (Int × Nat), (∀ q ∈ l, q.1 + lam * q.2 ≤ c) →
    lam * sumL l ≤ c * l.length - sumV l
  | [], _ => by simp [sumL, sumV]
  | (v, x) :: l, h => by
    have h1 := h (v, x) List.mem_cons_self
    have h2 := priced_line_cover lam c l (fun q hq => h q (List.mem_cons_of_mem _ hq))
    simp only [sumL, sumV, List.length_cons] at *
    push_cast
    have e1 : lam * ((x : Int) + sumL l) = lam * x + lam * sumL l := Int.mul_add _ _ _
    have e2 : c * ((l.length : Int) + 1) = c * l.length + c := by rw [Int.mul_add, Int.mul_one]
    rw [e1, e2]
    omega

/-- A single chain with 769 rows and 343 holes (the cell (769, 0, 0)) has line-1 value 4·769 − 9·343 = −11; with
the priced line `4r − 9d + 4L ≤ 56` it has at most 16 symbol changes. -/
theorem hamiltonian_769_label_changes (L : Nat) (hline : 4 * 769 - 9 * 343 + 4 * (L : Int) ≤ 56) : L ≤ 16 := by
  omega

#print axioms seam_entry_b
#print axioms next_class_of_exit
#print axioms seam_entry_e
#print axioms seam_entry_d_c_f
#print axioms ends_or_next_to_true_le
#print axioms six_row_lemma
#print axioms block_full_side
#print axioms block_overlap
#print axioms priced_line_cover
#print axioms hamiltonian_769_label_changes
