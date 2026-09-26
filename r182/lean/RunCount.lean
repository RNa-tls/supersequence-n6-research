/-
Round 182 -- the counting core of Lemma RUN (used by Theorem CS and Theorem F), core Lean 4 only.
A trail is abstracted to a list of Booleans: `true` = full row (charge 0), `false` = non-full row.
Hypothesis: every contiguous block of full rows has length <= c  (for trails, c = n-2 by C1 at g = 0,
which is NOT formalized here).  Conclusion: rows <= c * (nonfull + 1) + nonfull, and summed over a
list of trails: rows <= c * (nonfull + tau) + nonfull.
-/
namespace RunCount

theorem run_bound_aux (c : Nat) : ∀ (l : List Bool) (a : Nat),
    (∀ k, List.replicate k true <:+: (List.replicate a true ++ l) → k ≤ c) →
    a + l.length ≤ c * (l.count false + 1) + l.count false
  | [], a, h => by
      have ha : a ≤ c := h a (by rw [List.append_nil]; exact List.infix_refl _)
      simp only [List.length_nil, List.count_nil]
      omega
  | true :: l, a, h => by
      have e : List.replicate (a + 1) true ++ l = List.replicate a true ++ true :: l := by
        rw [List.replicate_succ', List.append_assoc]; rfl
      have ih := run_bound_aux c l (a + 1) (by rw [e]; exact h)
      have hc : (true :: l).count false = l.count false := by simp
      rw [hc, List.length_cons]
      omega
  | false :: l, a, h => by
      have ha : a ≤ c := h a (List.prefix_append _ _).isInfix
      have ih := run_bound_aux c l 0 (by
        intro k hk
        apply h k
        have hs : l <:+: List.replicate a true ++ false :: l := by
          have : List.replicate a true ++ false :: l = (List.replicate a true ++ [false]) ++ l := by
            simp
          rw [this]; exact (List.suffix_append _ _).isInfix
        exact hk.trans (by simpa using hs))
      have hc : (false :: l).count false = l.count false + 1 := by simp
      rw [hc, List.length_cons]
      have e1 : c * (l.count false + 1 + 1) = c * (l.count false + 1) + c := by
        rw [Nat.mul_add, Nat.mul_one]
      rw [e1]
      omega

/-- One trail. -/
theorem run_bound (c : Nat) (l : List Bool)
    (h : ∀ k, List.replicate k true <:+: l → k ≤ c) :
    l.length ≤ c * (l.count false + 1) + l.count false := by
  have := run_bound_aux c l 0 (by simpa using h)
  omega

/-- A family of trails (tau = number of trails): rows <= c * (nonfull + tau) + nonfull. -/
theorem run_bound_family (c : Nat) : ∀ (T : List (List Bool)),
    (∀ l ∈ T, ∀ k, List.replicate k true <:+: l → k ≤ c) →
    (T.map List.length).sum ≤ c * ((T.map (List.count false)).sum + T.length)
                                + (T.map (List.count false)).sum
  | [], _ => by simp
  | l :: T, h => by
      have h1 := run_bound c l (h l (List.mem_cons_self ..))
      have h2 := run_bound_family c T (fun l' hl' => h l' (List.mem_cons_of_mem _ hl'))
      simp only [List.map_cons, List.sum_cons, List.length_cons]
      have e : c * (l.count false + (T.map (List.count false)).sum + (T.length + 1))
          = c * (l.count false + 1) + c * ((T.map (List.count false)).sum + T.length) := by
        rw [← Nat.mul_add]; congr 1; omega
      rw [e]
      omega

end RunCount

#print axioms RunCount.run_bound
#print axioms RunCount.run_bound_family
