/-
Round X -- Lean 4 core only (no Mathlib).

1. `exists_last_nonpos`, `exists_first_ge`, `twosided`: the combinatorial core of the two-sided piece-count lemma.
   A chain with prefix values `S 0 = 0, S 1, ..., S r = v > 0` has an index `j < r` with `S j ≤ 0` after which every
   prefix value is positive (so the part `(j, r]` is forward-primitive), and an index `0 < i ≤ r` with `S i ≥ v`
   before which every prefix value is `< v` (so the part `(0, i]` is backward-primitive: all its suffixes are
   positive).  Either `j < i` (case A: the core `(j, i]` is a prefix of `(j, r]`, its value `w = S i - S j` is at
   least the values `u' = S i` of `(0, i]` and `u = v - S j` of `(j, r]`, and `v = u' + u - w`), or `i ≤ j`
   (case B: the middle `(i, j]` has value `≤ -v`).
2. `exc_knapsack`: the deficit knapsack with at most one exceptional chain.  Chains are triples
   (pieces, deficit, exceptional?).  A non-exceptional chain has deficit `≥ f r`, the exceptional one `≥ g r`;
   tables `P` (no exceptional chain) and `Q` (at most one) with `P 0 0 = 0`, `Q 0 0 = 0`,
   `P (m+1) (x+r) ≤ P m x + f r`, `Q (m+1) (x+r) ≤ Q m x + f r`, `Q (m+1) (x+r) ≤ P m x + g r`
   bound the total deficit from below (the tables of `rX/src/frontier_exceptional.py` are such `P`, `Q`).
-/

/-! ### 1. Two-sided decomposition -/

theorem exists_last_nonpos (S : Nat → Int) (h0 : S 0 = 0) :
    ∀ r, 0 < r → ∃ j, j < r ∧ S j ≤ 0 ∧ ∀ k, j < k → k < r → 0 < S k := by
  intro r
  induction r with
  | zero => intro h; exact absurd h (Nat.lt_irrefl 0)
  | succ n ih =>
    intro _
    by_cases hn : n = 0
    · subst hn
      exact ⟨0, Nat.zero_lt_one, by rw [h0]; exact Int.le_refl 0, fun k h1 h2 => absurd h2 (by omega)⟩
    · if hs : S n ≤ 0 then
        exact ⟨n, Nat.lt_succ_self n, hs, fun k h1 h2 => absurd h2 (by omega)⟩
      else
        obtain ⟨j, hjn, hSj, hall⟩ := ih (by omega)
        refine ⟨j, by omega, hSj, ?_⟩
        intro k hk1 hk2
        by_cases hkn : k = n
        · subst hkn; omega
        · exact hall k hk1 (by omega)

theorem exists_first_ge_aux (S : Nat → Int) (v : Int) :
    ∀ n, (∃ i, i ≤ n ∧ v ≤ S i ∧ ∀ k, k < i → S k < v) ∨ (∀ k, k ≤ n → S k < v) := by
  intro n
  induction n with
  | zero =>
    if h : v ≤ S 0 then
      exact Or.inl ⟨0, Nat.le_refl 0, h, fun k hk => absurd hk (Nat.not_lt_zero k)⟩
    else
      exact Or.inr (fun k hk => by
        have hk0 : k = 0 := by omega
        rw [hk0]; omega)
  | succ n ih =>
    cases ih with
    | inl h => obtain ⟨i, hi, h1, h2⟩ := h; exact Or.inl ⟨i, by omega, h1, h2⟩
    | inr h =>
      if hs : v ≤ S (n + 1) then
        exact Or.inl ⟨n + 1, Nat.le_refl _, hs, fun k hk => h k (by omega)⟩
      else
        exact Or.inr (fun k hk => by
          by_cases hkn : k = n + 1
          · subst hkn; omega
          · exact h k (by omega))

theorem exists_first_ge (S : Nat → Int) (r : Nat) (v : Int) (hr : S r = v) :
    ∃ i, i ≤ r ∧ v ≤ S i ∧ ∀ k, k < i → S k < v := by
  cases exists_first_ge_aux S v r with
  | inl h => exact h
  | inr h => have := h r (Nat.le_refl r); omega

/-- **Two-sided decomposition.**  For prefix values `S` of a chain with `r` pieces and value `v > 0`, there are
`j < r` and `0 < i ≤ r` such that `(j, r]` is forward-primitive, `(0, i]` is backward-primitive, and either case A
(`j < i`, the core `(j, i]` forward-primitive, `u' ≤ w`, `u ≤ w`, `v = u' + u - w`) or case B (`i ≤ j`, middle
value `≤ -v`). -/
theorem twosided (S : Nat → Int) (r : Nat) (v : Int) (h0 : S 0 = 0) (hr : S r = v) (hv : 0 < v) (hpos : 0 < r) :
    ∃ j i, j < r ∧ 0 < i ∧ i ≤ r ∧ S j ≤ 0 ∧ v ≤ S i ∧
      (∀ k, j < k → k ≤ r → S j < S k) ∧
      (∀ k, k < i → S k < S i) ∧
      ((j < i ∧ S i ≤ S i - S j ∧ v - S j ≤ S i - S j ∧ v = S i + (v - S j) - (S i - S j) ∧
          ∀ k, j < k → k ≤ i → S j < S k) ∨
       (i ≤ j ∧ S j - S i ≤ -v)) := by
  obtain ⟨j, hjr, hSj, hj⟩ := exists_last_nonpos S h0 r hpos
  obtain ⟨i, hir, hSi, hi⟩ := exists_first_ge S r v hr
  have hi0 : 0 < i := by
    cases Nat.eq_zero_or_pos i with
    | inl h => subst h; omega
    | inr h => exact h
  have fwd : ∀ k, j < k → k ≤ r → S j < S k := by
    intro k h1 h2
    by_cases hk : k = r
    · subst hk; omega
    · have := hj k h1 (by omega); omega
  have bwd : ∀ k, k < i → S k < S i := by
    intro k hk; have := hi k hk; omega
  refine ⟨j, i, hjr, hi0, hir, hSj, hSi, fwd, bwd, ?_⟩
  by_cases hji : j < i
  · exact Or.inl ⟨hji, by omega, by omega, by omega, fun k h1 h2 => fwd k h1 (by omega)⟩
  · exact Or.inr ⟨by omega, by omega⟩

/-! ### 2. The knapsack with at most one exceptional chain -/

def sumP : List (Nat × Nat × Bool) → Nat
  | [] => 0
  | c :: l => c.1 + sumP l

def sumD : List (Nat × Nat × Bool) → Nat
  | [] => 0
  | c :: l => c.2.1 + sumD l

def bnat : Bool → Nat
  | true => 1
  | false => 0

def nExc : List (Nat × Nat × Bool) → Nat
  | [] => 0
  | c :: l => bnat c.2.2 + nExc l

theorem plain_knapsack (f : Nat → Nat) (P : Nat → Nat → Nat) (hP0 : P 0 0 = 0)
    (hP : ∀ m x r, P (m + 1) (x + r) ≤ P m x + f r) :
    ∀ L : List (Nat × Nat × Bool), (∀ c ∈ L, f c.1 ≤ c.2.1) → P L.length (sumP L) ≤ sumD L := by
  intro L
  induction L with
  | nil => intro _; simp [sumP, sumD, hP0]
  | cons c l ih =>
    intro hd
    have h1 : f c.1 ≤ c.2.1 := hd c (List.mem_cons_self ..)
    have h2 := ih (fun c' hc' => hd c' (List.mem_cons_of_mem _ hc'))
    have h3 := hP l.length (sumP l) c.1
    simp only [List.length_cons, sumP, sumD]
    rw [Nat.add_comm c.1 (sumP l)]
    omega

theorem nExc_zero : ∀ l : List (Nat × Nat × Bool), nExc l = 0 → ∀ x ∈ l, x.2.2 = false := by
  intro l
  induction l with
  | nil => intro _ x hx; cases hx
  | cons a t iht =>
    intro h x hx
    cases ha : a.2.2 with
    | true => rw [nExc, ha] at h; simp only [bnat] at h; omega
    | false =>
      have ht : nExc t = 0 := by rw [nExc, ha] at h; simp only [bnat] at h; omega
      cases hx with
      | head => exact ha
      | tail _ hxt => exact iht ht x hxt

theorem exc_knapsack (f g : Nat → Nat) (P Q : Nat → Nat → Nat) (hP0 : P 0 0 = 0) (hQ0 : Q 0 0 = 0)
    (hP : ∀ m x r, P (m + 1) (x + r) ≤ P m x + f r)
    (hQf : ∀ m x r, Q (m + 1) (x + r) ≤ Q m x + f r)
    (hQg : ∀ m x r, Q (m + 1) (x + r) ≤ P m x + g r) :
    ∀ L : List (Nat × Nat × Bool),
      (∀ c ∈ L, (c.2.2 = false → f c.1 ≤ c.2.1) ∧ (c.2.2 = true → g c.1 ≤ c.2.1)) →
      nExc L ≤ 1 → Q L.length (sumP L) ≤ sumD L := by
  intro L
  induction L with
  | nil => intro _ _; simp [sumP, sumD, hQ0]
  | cons c l ih =>
    intro hd hn
    have hc := hd c (List.mem_cons_self ..)
    have hdl : ∀ c' ∈ l, (c'.2.2 = false → f c'.1 ≤ c'.2.1) ∧ (c'.2.2 = true → g c'.1 ≤ c'.2.1) :=
      fun c' hc' => hd c' (List.mem_cons_of_mem _ hc')
    simp only [List.length_cons, sumP, sumD]
    rw [Nat.add_comm c.1 (sumP l)]
    cases hb : c.2.2 with
    | true =>
      -- the head is the exceptional chain: no exceptional chain in the tail
      have hnl : nExc l = 0 := by rw [nExc, hb] at hn; simp only [bnat] at hn; omega
      have hnone : ∀ c' ∈ l, f c'.1 ≤ c'.2.1 := by
        intro c' hc'
        exact (hdl c' hc').1 (nExc_zero l hnl c' hc')
      have h1 := plain_knapsack f P hP0 hP l hnone
      have h2 := hQg l.length (sumP l) c.1
      have h3 := hc.2 hb
      omega
    | false =>
      have hnl : nExc l ≤ 1 := by rw [nExc, hb] at hn; simp only [bnat] at hn; omega
      have h1 := ih hdl hnl
      have h2 := hQf l.length (sumP l) c.1
      have h3 := hc.1 hb
      omega

#print axioms twosided
#print axioms plain_knapsack
#print axioms exc_knapsack

/-! ### 3. The knapsack with typed chains and resources (the packing knapsack of `frontier_packing.py`)

Chains are triples (type, pieces, deficit).  A chain of type `t` with `r` pieces has deficit `≥ f t r`; adding it
moves the resource state `s` to `use s t`.  A table `P s m x` with `P s0 0 0 = 0` and
`P (use s t) (m+1) (x+r) ≤ P s m x + f t r` bounds the total deficit from below at the final state of the list.
In `frontier_packing.py` the state is (Σ nu, number of chains with parts of value ≥ 50, number of line-2 exceptional
chains), the packing lemmas say that the final state of every Hamiltonian path is within the caps (2, 1, 1), and the
script minimises `P` over the capped states. -/

def stTyped {τ σ : Type} (use : σ → τ → σ) (s0 : σ) : List (τ × Nat × Nat) → σ
  | [] => s0
  | c :: l => use (stTyped use s0 l) c.1

def sumPt {τ : Type} : List (τ × Nat × Nat) → Nat
  | [] => 0
  | c :: l => c.2.1 + sumPt l

def sumDt {τ : Type} : List (τ × Nat × Nat) → Nat
  | [] => 0
  | c :: l => c.2.2 + sumDt l

theorem typed_knapsack {τ σ : Type} (f : τ → Nat → Nat) (use : σ → τ → σ) (s0 : σ) (P : σ → Nat → Nat → Nat)
    (hP0 : P s0 0 0 = 0) (hP : ∀ s m x t r, P (use s t) (m + 1) (x + r) ≤ P s m x + f t r) :
    ∀ L : List (τ × Nat × Nat), (∀ c ∈ L, f c.1 c.2.1 ≤ c.2.2) →
      P (stTyped use s0 L) L.length (sumPt L) ≤ sumDt L := by
  intro L
  induction L with
  | nil => intro _; simp [stTyped, sumPt, sumDt, hP0]
  | cons c l ih =>
    intro hd
    have h1 : f c.1 c.2.1 ≤ c.2.2 := hd c (List.mem_cons_self ..)
    have h2 := ih (fun c' hc' => hd c' (List.mem_cons_of_mem _ hc'))
    have h3 := hP (stTyped use s0 l) l.length (sumPt l) c.1 c.2.1
    simp only [List.length_cons, stTyped, sumPt, sumDt]
    rw [Nat.add_comm c.2.1 (sumPt l)]
    omega

#print axioms typed_knapsack
