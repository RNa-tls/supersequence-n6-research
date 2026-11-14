/-
Round Y -- Lean 4 core only (no Mathlib).

1. `tailSum_eq_sum`, `tail_bound`: the integrated tail identity  Σ v = Σ_{t=1}^{M} #{v ≥ t}  for values ≤ M, and
   the integrated tail bound: if #{v ≥ t} ≤ κ t for every threshold t then Σ v ≤ Σ_t κ t.
2. `runs_le`, `segment_full_le`, `segments_full_le`: the counting behind the full-run lemma.  A segment is a list of
   pieces (`true` = full piece).  If every run of consecutive full pieces has at most 5 pieces, or the segment is one
   run of at most 6 full pieces, then #full ≤ 5 #partial + 6;  summed over S segments, #full ≤ 5 #partial + 6 S.
3. `single_label_excluded`: the arithmetic that excludes covers with one moving symbol from the 46134 frontier
   (run lemma + all holes parallel: partial pieces ≤ 2 M, M ≤ E; line 1 with free junctions bounds F).
4. `deficit_decomposition`: Δ = 7R − 5040 = W + 7M from R = U + M and 7U = 5040 + W.
5. `bridge_46135`: the logical shape of "no surviving frontier cell ⇒ L(8) ≥ 46135" (not usable: 40 cells survive).
-/

/-! ### 1. Integrated tail -/

/-- `cntGe t l` = number of entries of `l` that are `≥ t`. -/
def cntGe (t : Nat) : List Nat → Nat
  | [] => 0
  | v :: l => (if t ≤ v then 1 else 0) + cntGe t l

/-- `tailSum M l = Σ_{t=1}^{M} cntGe t l`. -/
def tailSum : Nat → List Nat → Nat
  | 0, _ => 0
  | M + 1, l => cntGe (M + 1) l + tailSum M l

theorem tailSum_cons (M v : Nat) (l : List Nat) :
    tailSum M (v :: l) = Nat.min v M + tailSum M l := by
  induction M with
  | zero => simp [tailSum]
  | succ M ih =>
    simp only [tailSum, cntGe, ih]
    by_cases h : M + 1 ≤ v
    · rw [if_pos h]
      have e1 : Nat.min v (M + 1) = M + 1 := Nat.min_eq_right h
      have e2 : Nat.min v M = M := Nat.min_eq_right (by omega)
      rw [e1, e2]; omega
    · rw [if_neg h]
      have e1 : Nat.min v (M + 1) = v := Nat.min_eq_left (by omega)
      have e2 : Nat.min v M = v := Nat.min_eq_left (by omega)
      rw [e1, e2]; omega

theorem tailSum_nil (M : Nat) : tailSum M [] = 0 := by
  induction M with
  | zero => rfl
  | succ M ih => simp [tailSum, cntGe, ih]

/-- **Integrated tail identity.** -/
theorem tailSum_eq_sum (M : Nat) : ∀ l : List Nat, (∀ v ∈ l, v ≤ M) → tailSum M l = l.sum
  | [], _ => by rw [tailSum_nil]; rfl
  | v :: l, h => by
    rw [tailSum_cons, tailSum_eq_sum M l (fun w hw => h w (List.mem_cons_of_mem v hw))]
    have hv : v ≤ M := h v (List.mem_cons_self)
    have e : Nat.min v M = v := by simp [hv]
    rw [e, List.sum_cons]

/-- `kSum κ M = Σ_{t=1}^{M} κ t`. -/
def kSum (κ : Nat → Nat) : Nat → Nat
  | 0 => 0
  | M + 1 => κ (M + 1) + kSum κ M

theorem tailSum_le_kSum (κ : Nat → Nat) (l : List Nat) :
    ∀ M, (∀ t, 1 ≤ t → t ≤ M → cntGe t l ≤ κ t) → tailSum M l ≤ kSum κ M
  | 0, _ => by simp [tailSum, kSum]
  | M + 1, h => by
    simp only [tailSum, kSum]
    have h1 := h (M + 1) (by omega) (Nat.le_refl _)
    have h2 := tailSum_le_kSum κ l M (fun t ht1 ht2 => h t ht1 (by omega))
    omega

/-- **Integrated tail bound**: values bounded by `M`, at most `κ t` of them reach `t`, then the sum is at most
`Σ_{t ≤ M} κ t`. -/
theorem tail_bound (κ : Nat → Nat) (M : Nat) (l : List Nat) (hM : ∀ v ∈ l, v ≤ M)
    (hk : ∀ t, 1 ≤ t → t ≤ M → cntGe t l ≤ κ t) : l.sum ≤ kSum κ M := by
  rw [← tailSum_eq_sum M l hM]
  exact tailSum_le_kSum κ l M hk

theorem cntGe_le_length (t : Nat) : ∀ l : List Nat, cntGe t l ≤ l.length
  | [] => by simp [cntGe]
  | v :: l => by
    simp only [cntGe, List.length_cons]
    have := cntGe_le_length t l
    split <;> omega

/-! ### 2. Counting full pieces in segments -/

/-- `RunsLe k c l`: reading `l` from the left with a current run of `c` full pieces, no run exceeds `k`. -/
def RunsLe (k : Nat) : Nat → List Bool → Prop
  | c, [] => c ≤ k
  | c, true :: l => c + 1 ≤ k ∧ RunsLe k (c + 1) l
  | _, false :: l => RunsLe k 0 l

def cntT : List Bool → Nat
  | [] => 0
  | true :: l => cntT l + 1
  | false :: l => cntT l

def cntF : List Bool → Nat
  | [] => 0
  | true :: l => cntF l
  | false :: l => cntF l + 1

theorem runs_le (k : Nat) : ∀ (l : List Bool) (c : Nat), c ≤ k → RunsLe k c l → cntT l + c ≤ k * (cntF l + 1)
  | [], c, hc, _ => by simp [cntT, cntF]; omega
  | true :: l, c, _, h => by
    obtain ⟨h1, h2⟩ := h
    have ih := runs_le k l (c + 1) h1 h2
    simp only [cntT, cntF]
    omega
  | false :: l, c, hc, h => by
    have ih := runs_le k l 0 (Nat.zero_le _) h
    simp only [cntT, cntF]
    have : k * (cntF l + 1 + 1) = k * (cntF l + 1) + k := by rw [Nat.mul_succ]
    omega

theorem cnt_length : ∀ l : List Bool, cntT l + cntF l = l.length
  | [] => rfl
  | true :: l => by simp only [cntT, cntF, List.length_cons]; have := cnt_length l; omega
  | false :: l => by simp only [cntT, cntF, List.length_cons]; have := cnt_length l; omega

/-- **One segment.**  Either all runs have at most 5 full pieces, or the segment is a single run of at most 6 full
pieces (no partial piece).  Then #full ≤ 5 #partial + 6. -/
theorem segment_full_le (l : List Bool)
    (h : RunsLe 5 0 l ∨ (cntF l = 0 ∧ l.length ≤ 6)) : cntT l ≤ 5 * cntF l + 6 := by
  cases h with
  | inl h5 =>
    have := runs_le 5 l 0 (Nat.zero_le _) h5
    omega
  | inr h6 =>
    obtain ⟨hf, hlen⟩ := h6
    have hT := cnt_length l
    omega

def sumT : List (List Bool) → Nat
  | [] => 0
  | s :: ss => cntT s + sumT ss

def sumF : List (List Bool) → Nat
  | [] => 0
  | s :: ss => cntF s + sumF ss

/-- **All segments.**  #full ≤ 5 #partial + 6 S. -/
theorem segments_full_le : ∀ ss : List (List Bool),
    (∀ s ∈ ss, RunsLe 5 0 s ∨ (cntF s = 0 ∧ s.length ≤ 6)) → sumT ss ≤ 5 * sumF ss + 6 * ss.length
  | [], _ => by simp [sumT, sumF]
  | s :: ss, h => by
    have h1 := segment_full_le s (h s List.mem_cons_self)
    have h2 := segments_full_le ss (fun t ht => h t (List.mem_cons_of_mem s ht))
    simp only [sumT, sumF, List.length_cons]
    rw [Nat.mul_add, Nat.mul_add] at *
    omega

/-! ### 3. Covers with one moving symbol are not at the 46134 frontier -/

/-- Rows `R = 720 + E`, full rows `F7`, partial rows `P`, `n = 1 + p + F` chains (all segments are chains when the
moving symbol never changes), extra rows of split 2-cycles `M`.  Run lemma: `F7 ≤ 5 P + 6 n`.  One moving symbol:
every hole is parallel, so `P ≤ 2 M` and `M ≤ E`.  Frontier: `R + p = 769`.  Line 1 with free junctions (Halfar's
`lineD_reduced_holes`, γ = 5): `4 R + 5 F ≤ 9 Δ + 56 (1 + p)`, `Δ + 7·720 = 7 R`. -/
theorem single_label_excluded (R E F7 P M n p F Δ : Nat) (hR : R = 720 + E) (hrows : R = F7 + P)
    (hrun : F7 ≤ 5 * P + 6 * n) (hsplit : P ≤ 2 * M) (hM : M ≤ E) (hcov : R + p = 769) (hn : n = 1 + p + F)
    (hhol : Δ + 7 * 720 = 7 * R) (hl1 : 4 * R + 5 * F ≤ 9 * Δ + 56 * (1 + p)) : False := by
  omega

/-! ### 4. Deficit decomposition -/

/-- `R = U + M` (rows = used 2-cycles + extra rows of split 2-cycles), `7 U = 5040 + W` (the used 2-cycles cover the
5040 classes with total overlap `W`).  Then the holes `Δ = 7 R - 5040` split as `W + 7 M`. -/
theorem deficit_decomposition (R U M W : Nat) (h1 : R = U + M) (h2 : 7 * U = 5040 + W) :
    7 * R - 5040 = W + 7 * M := by
  omega

/-! ### 5. The bridge (logical skeleton) -/

/-- If a superpermutation of length 46134 determines a frontier cell `(R, p, F)` with `R + p = 769` (Halfar's
coverage bound and Theorem D give `R + p ≤ 769` and `≥ 769`), and every frontier cell is excluded, then the length
is at least 46135.  With 40 cells not excluded, `hexcl` is not available; this is only the shape of the final step. -/
theorem bridge_46135 (len : Nat) (hge : 46134 ≤ len) (cell : Nat → Nat → Nat → Prop)
    (hcell : len = 46134 → ∃ R p F, R + p = 769 ∧ cell R p F)
    (hexcl : ∀ R p F, R + p = 769 → cell R p F → False) : 46135 ≤ len := by
  by_cases h : len = 46134
  · obtain ⟨R, p, F, h1, h2⟩ := hcell h
    exact (hexcl R p F h1 h2).elim
  · omega

#print axioms tailSum_eq_sum
#print axioms tail_bound
#print axioms runs_le
#print axioms segment_full_le
#print axioms segments_full_le
#print axioms single_label_excluded
#print axioms deficit_decomposition
#print axioms bridge_46135
