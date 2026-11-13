/-
Round V -- the suffix argument behind the piece-count lemma, and small arithmetic, Lean 4 core only.

A chain is a list of pieces; with a line (a, b, c) each piece has the value  a - b * (its deficit),  and the value of a
chain is the sum.  `suffix_positive`: a list of integers with positive sum has a suffix whose sum is at least the sum
of the list and all of whose nonempty prefixes have positive sum.  Since a contiguous part of a chain is a chain, a
chain of value v >= 1 therefore contains, as a suffix, a chain of value >= v all of whose nonempty prefixes have
positive value -- and such chains are exactly the ones visited by the line search.  Hence: if no visited chain of
value >= v has fewer than m pieces, then no chain at all of value >= v has fewer than m pieces (`pieces_bound`).

`walk_cost_bound`  : Q >= 2 * (segments) and L <= 4 * (segments) give L <= 2 Q   (entry lemma => Q >= L / 2).
`cell_747`         : 23 chain values <= 56, none equal to 55, with sum 1287 force 22 values equal to 56 ... and
                     22 chains of 158 pieces do not fit into 747 pieces.
-/

theorem sum_append_int (a b : List Int) : (a ++ b).sum = a.sum + b.sum := by
  induction a with
  | nil => simp
  | cons x t ih => simp [List.sum_cons, ih]; omega

/-- all nonempty prefixes of `s` have positive sum -/
def PosPrefixes (s : List Int) : Prop := ∀ a b : List Int, s = a ++ b → a ≠ [] → 0 < a.sum

theorem suffix_positive_aux : ∀ (n : Nat) (l : List Int), l.length = n → 0 < l.sum →
    ∃ p s : List Int, l = p ++ s ∧ s ≠ [] ∧ l.sum ≤ s.sum ∧ PosPrefixes s := by
  intro n
  induction n using Nat.strongRecOn with
  | _ n ih =>
    intro l hlen hpos
    by_cases hall : PosPrefixes l
    · refine ⟨[], l, by simp, ?_, Int.le_refl _, hall⟩
      intro hnil; subst hnil; simp at hpos
    · -- some nonempty prefix a has sum <= 0; the rest b is shorter and has sum >= l.sum
      have : ∃ a b : List Int, l = a ++ b ∧ a ≠ [] ∧ a.sum ≤ 0 := by
        apply Classical.byContradiction
        intro hno
        apply hall
        intro a b hab ha
        apply Classical.byContradiction
        intro hle
        exact hno ⟨a, b, hab, ha, by omega⟩
      obtain ⟨a, b, hab, ha, hsum⟩ := this
      have hl : l.sum = a.sum + b.sum := by rw [hab, sum_append_int]
      have hbpos : 0 < b.sum := by omega
      have halen : 0 < a.length := by
        cases a with
        | nil => exact absurd rfl ha
        | cons x t => simp
      have hblen : b.length < n := by
        have := congrArg List.length hab
        rw [List.length_append] at this
        omega
      obtain ⟨p, s, hbs, hs, hle, hpp⟩ := ih b.length hblen b rfl hbpos
      refine ⟨a ++ p, s, ?_, hs, ?_, hpp⟩
      · rw [hab, hbs, List.append_assoc]
      · omega

/-- **suffix argument** -/
theorem suffix_positive (l : List Int) (hpos : 0 < l.sum) :
    ∃ p s : List Int, l = p ++ s ∧ s ≠ [] ∧ l.sum ≤ s.sum ∧ PosPrefixes s :=
  suffix_positive_aux l.length l rfl hpos

/-- If every list in a class `Chain` that is closed under suffixes, has only positive nonempty prefixes and sum >= v,
has length >= m, then every list of `Chain` with sum >= v >= 1 has length >= m. -/
theorem pieces_bound (Chain : List Int → Prop) (v : Int) (m : Nat) (hv : 1 ≤ v)
    (hsuf : ∀ p s : List Int, Chain (p ++ s) → Chain s)
    (hvis : ∀ s : List Int, Chain s → PosPrefixes s → v ≤ s.sum → m ≤ s.length) :
    ∀ l : List Int, Chain l → v ≤ l.sum → m ≤ l.length := by
  intro l hl hlv
  obtain ⟨p, s, hps, _, hle, hpp⟩ := suffix_positive l (by omega)
  have hs : Chain s := hsuf p s (hps ▸ hl)
  have h1 := hvis s hs hpp (by omega)
  have h2 : l.length = p.length + s.length := by rw [hps, List.length_append]
  omega

theorem walk_cost_bound (Q L S : Nat) (h1 : 2 * S ≤ Q) (h2 : L ≤ 4 * S) : L ≤ 2 * Q := by omega

/-- cell R = 747, p = 22, F = 0: 23 chains, values <= 56 and never 55, sum 4 * 747 - 9 * 189 = 1287:
at least 22 chains have value 56, and 22 * 158 > 747 -/
theorem cell_747 (n56 nlow : Nat) (hn : n56 + nlow = 23) (S : Int)
    (hS : S ≤ 56 * (n56 : Int) + 54 * (nlow : Int)) (hsum : S = 4 * 747 - 9 * 189) :
    22 ≤ n56 ∧ 747 < 22 * 158 := by
  constructor
  · omega
  · decide

#print axioms suffix_positive
#print axioms pieces_bound
#print axioms walk_cost_bound
#print axioms cell_747
