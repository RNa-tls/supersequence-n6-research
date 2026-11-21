/-
Round Ω -- Lean 4 core only (no Mathlib).

1. `coexistence_from_prefixes`: the logical core of the two-threshold coexistence table (rOmega/src/compat2d.py,
   rOmega/src/compat_cross.py).  If every disjoint placement of two chains restricts to a listed placement of their
   prefixes (prefixes have fewer classes, relabelling is monotone), and no listed placement extends to a disjoint
   placement of the longer chains, then no two longer chains can be placed disjointly.
2. `compat_vs_max`: the knapsack state stores only the largest level seen so far.  For a compatibility relation that is
   antitone in both arguments, a new level i is compatible with every earlier level as soon as it is compatible with
   the largest one; `all_pairs_of_incremental` then gives compatibility of every pair of a list built incrementally.
3. `levelled_cut`: the arithmetic of a cell exclusion -- deficits of the chains bounded below by their tables and a
   least total above Delta give a contradiction with the exact cover count.
-/

/-! ### 1. Coexistence tables from prefix placements -/

section Coexist
variable {α β : Type}

/-- Disjointness of two lists of classes. -/
def Disj (A B : List Nat) : Prop := ∀ c, c ∈ A → c ∉ B

theorem disj_mono {A A' B B' : List Nat} (hA : ∀ c, c ∈ A → c ∈ A') (hB : ∀ c, c ∈ B → c ∈ B')
    (h : Disj A' B') : Disj A B := by
  intro c hc hcB
  exact h c (hA c hc) (hB c hcB)

/-- **Coexistence from prefix placements.**  `cls` = classes of a chain, `pre` = its first-passage prefix at the base
threshold, `act g` = the relabelling (and orientation) `g` acting on a list of classes, monotone for inclusion.
`L` is the complete list of disjoint placements of base chains (completeness hypothesis `hL`), and `hchk` is the
finite check that no listed placement extends to a disjoint placement of the longer chains. -/
theorem coexistence_from_prefixes (cls : α → List Nat) (pre : α → α) (act : β → List Nat → List Nat)
    (L : List (α × α × β))
    (hpre : ∀ x c, c ∈ cls (pre x) → c ∈ cls x)
    (hact : ∀ g (A B : List Nat), (∀ c, c ∈ A → c ∈ B) → ∀ c, c ∈ act g A → c ∈ act g B)
    (hL : ∀ x y g, Disj (cls x) (act g (cls y)) → (x, y, g) ∈ L)
    (hchk : ∀ p, p ∈ L → ∀ x' y', pre x' = p.1 → pre y' = p.2.1 → ¬ Disj (cls x') (act p.2.2 (cls y'))) :
    ∀ x' y' g, ¬ Disj (cls x') (act g (cls y')) := by
  intro x' y' g h
  have h0 : Disj (cls (pre x')) (act g (cls (pre y'))) :=
    disj_mono (hpre x') (hact g _ _ (hpre y')) h
  have hmem := hL (pre x') (pre y') g h0
  exact hchk _ hmem x' y' rfl rfl h

end Coexist

/-! ### 2. Compatibility against the running maximum -/

section Compat

/-- `C` is antitone in both arguments: compatibility of higher levels implies compatibility of lower ones. -/
def Antitone2 (C : Nat → Nat → Prop) : Prop := ∀ a b a' b', C a b → a' ≤ a → b' ≤ b → C a' b'

def lmax : List Nat → Nat
  | [] => 0
  | x :: xs => Nat.max x (lmax xs)

theorem le_lmax : ∀ (xs : List Nat) (x : Nat), x ∈ xs → x ≤ lmax xs
  | [], x, h => by cases h
  | y :: ys, x, h => by
    cases h with
    | head => exact Nat.le_max_left _ _
    | tail _ h' => exact Nat.le_trans (le_lmax ys x h') (Nat.le_max_right _ _)

/-- **A new level compatible with the maximum is compatible with every earlier level.** -/
theorem compat_vs_max (C : Nat → Nat → Prop) (hC : Antitone2 C) (i : Nat) (xs : List Nat)
    (h : C i (lmax xs)) : ∀ x, x ∈ xs → C i x :=
  fun x hx => hC i (lmax xs) i x h (Nat.le_refl i) (le_lmax xs x hx)

/-- Every pair (earlier, later) of a list is compatible when each element was compatible with the maximum of the
elements before it (the knapsack's incremental test). -/
def IncrOK (C : Nat → Nat → Prop) : List Nat → Prop
  | [] => True
  | x :: xs => C x (lmax xs) ∧ IncrOK C xs

/-- The pairwise statement used: for `x :: xs`, the head is compatible with every element of the tail. -/
theorem head_compat (C : Nat → Nat → Prop) (hC : Antitone2 C) (x : Nat) (xs : List Nat)
    (h : IncrOK C (x :: xs)) : ∀ y, y ∈ xs → C x y :=
  compat_vs_max C hC x xs h.1

/-- By induction every element is compatible with every element after it. -/
theorem incremental_pairs (C : Nat → Nat → Prop) (hC : Antitone2 C) :
    ∀ xs : List Nat, IncrOK C xs → ∀ (pre suf : List Nat) (x : Nat), xs = pre ++ x :: suf → ∀ y, y ∈ suf → C x y
  | [], _, pre, suf, x, he, _, _ => by cases pre <;> simp at he
  | z :: zs, h, pre, suf, x, he, y, hy => by
    cases pre with
    | nil =>
      simp at he
      obtain ⟨rfl, rfl⟩ := he
      exact head_compat C hC _ _ h y hy
    | cons p ps =>
      simp at he
      obtain ⟨_, rfl⟩ := he
      exact incremental_pairs C hC (ps ++ x :: suf) h.2 ps suf x rfl y hy

end Compat

/-! ### 3. The cell-exclusion arithmetic -/

/-- Deficits `d i ≥ t i` for every chain and a least total `Σ t > Delta` contradict the exact cover count
`Σ d = Delta` (here with an explicit list of pairs (d, t)). -/
def sumFst : List (Nat × Nat) → Nat
  | [] => 0
  | (a, _) :: l => a + sumFst l
def sumSnd : List (Nat × Nat) → Nat
  | [] => 0
  | (_, b) :: l => b + sumSnd l

theorem sum_ge : ∀ l : List (Nat × Nat), (∀ p, p ∈ l → p.2 ≤ p.1) → sumSnd l ≤ sumFst l
  | [], _ => Nat.le_refl 0
  | (a, b) :: l, h => by
    have h1 : b ≤ a := h (a, b) List.mem_cons_self
    have h2 := sum_ge l (fun p hp => h p (List.mem_cons_of_mem _ hp))
    simp only [sumFst, sumSnd]
    omega

theorem levelled_cut (l : List (Nat × Nat)) (Delta : Nat) (hd : ∀ p, p ∈ l → p.2 ≤ p.1)
    (hcover : sumFst l = Delta) (hlb : Delta < sumSnd l) : False := by
  have := sum_ge l hd
  omega

#print axioms disj_mono
#print axioms coexistence_from_prefixes
#print axioms le_lmax
#print axioms compat_vs_max
#print axioms head_compat
#print axioms incremental_pairs
#print axioms sum_ge
#print axioms levelled_cut
