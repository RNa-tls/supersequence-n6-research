/-
Round S -- the Monge (four-point) inequality for overlaps of strings, and the bookkeeping of the cut deletion.
Lean 4.22.0 core only (no Mathlib); no sorry, no admit, no user axiom.

`Ov A U k` : the last `k` symbols of `A` are the first `k` symbols of `U`.

`monge` : if `B, U` overlap in `m`, `A, U` in `p <= m`, `B, Y` in `q <= m` and `m <= p + q`,
          then `A, Y` overlap in `p + q - m`.
For the runs of the family, w(x, y) = 8 - (largest overlap <= 7 of last(x) and first(y)), so with
m = 8 - w(b, u), p = 8 - w(a, u), q = 8 - w(b, y):

      w(b, u) <= min(w(a, u), w(b, y))   ==>   w(a, y) + w(b, u) <= w(a, u) + w(b, y)        (`monge_weight`).

The detour lemmas L1, L2, L1G of Round R are the cases "b -> u is a natural link of a trail" (`detour_L1`,
`detour_L2`); the wrap of a full chain (the only non-natural link of weight 2) is exactly where the hypothesis can fail.
-/

/-- the last `k` symbols of `A` are the first `k` symbols of `U` -/
def Ov {α : Type} (A U : List α) (k : Nat) : Prop :=
  ∃ X S Z : List α, A = X ++ S ∧ U = S ++ Z ∧ S.length = k

theorem ov_zero {α : Type} (A U : List α) : Ov A U 0 :=
  ⟨A, [], U, by simp, by simp, rfl⟩

/-- two decompositions of the same list: the shorter first part is a prefix of the longer one -/
theorem prefix_split {α : Type} {S₁ Z₁ S₂ Z₂ : List α} (h : S₁ ++ Z₁ = S₂ ++ Z₂)
    (hl : S₂.length ≤ S₁.length) : ∃ R, S₁ = S₂ ++ R ∧ Z₂ = R ++ Z₁ := by
  rcases List.append_eq_append_iff.mp h with ⟨a', h1, h2⟩ | ⟨c', h1, h2⟩
  · -- S₂ = S₁ ++ a', Z₁ = a' ++ Z₂ : the lengths force a' = []
    have hlen : S₂.length = S₁.length + a'.length := by rw [h1, List.length_append]
    have ha : a'.length = 0 := by omega
    have ha' : a' = [] := List.eq_nil_of_length_eq_zero ha
    subst ha'
    refine ⟨[], ?_, ?_⟩
    · simp at h1; simp [h1]
    · simp at h2; simp [h2]
  · exact ⟨c', h1, h2⟩

/-- two decompositions of the same list: the shorter last part is a suffix of the longer one -/
theorem suffix_split {α : Type} {X₁ S₁ X₃ S₃ : List α} (h : X₁ ++ S₁ = X₃ ++ S₃)
    (hl : S₃.length ≤ S₁.length) : ∃ R, S₁ = R ++ S₃ ∧ X₃ = X₁ ++ R := by
  rcases List.append_eq_append_iff.mp h with ⟨a', h1, h2⟩ | ⟨c', h1, h2⟩
  · exact ⟨a', h2, h1⟩
  · -- X₁ = X₃ ++ c', S₃ = c' ++ S₁ : the lengths force c' = []
    have hlen : S₃.length = c'.length + S₁.length := by rw [h2, List.length_append]
    have hc : c'.length = 0 := by omega
    have hc' : c' = [] := List.eq_nil_of_length_eq_zero hc
    subst hc'
    refine ⟨[], ?_, ?_⟩
    · simp at h2; simp [h2]
    · simp at h1; simp [h1]

/-- **Monge inequality for overlaps** (arbitrary strings over an arbitrary alphabet). -/
theorem monge {α : Type} (A B U Y : List α) (m p q : Nat)
    (hBU : Ov B U m) (hAU : Ov A U p) (hBY : Ov B Y q)
    (hp : p ≤ m) (hq : q ≤ m) (hpq : m ≤ p + q) : Ov A Y (p + q - m) := by
  obtain ⟨X₁, S₁, Z₁, hB1, hU1, hS1⟩ := hBU
  obtain ⟨X₂, S₂, Z₂, hA2, hU2, hS2⟩ := hAU
  obtain ⟨X₃, S₃, Z₃, hB3, hY3, hS3⟩ := hBY
  -- S₂ is a prefix of S₁ (both are prefixes of U)
  have hU : S₁ ++ Z₁ = S₂ ++ Z₂ := by rw [← hU1, ← hU2]
  obtain ⟨R₁, hR1, _⟩ := prefix_split hU (by omega)
  -- S₃ is a suffix of S₁ (both are suffixes of B)
  have hB : X₁ ++ S₁ = X₃ ++ S₃ := by rw [← hB1, ← hB3]
  obtain ⟨R₂, hR2, _⟩ := suffix_split hB (by omega)
  -- S₁ = S₂ ++ R₁ = R₂ ++ S₃ and |R₂| = m - q <= p = |S₂|
  have hR2len : R₂.length + S₃.length = S₁.length := by
    have := congrArg List.length hR2; rw [List.length_append] at this; omega
  have hmid : S₂ ++ R₁ = R₂ ++ S₃ := by rw [← hR1, ← hR2]
  obtain ⟨M, hM1, hM2⟩ := prefix_split hmid (by omega)
  -- S₂ = R₂ ++ M, S₃ = M ++ R₁
  refine ⟨X₂ ++ R₂, M, R₁ ++ Z₃, ?_, ?_, ?_⟩
  · rw [hA2, hM1, List.append_assoc]
  · rw [hY3, hM2, List.append_assoc]
  · have h1 := congrArg List.length hM1
    rw [List.length_append] at h1
    omega

/-- weight form: `Wt n A U s` says that the shift `s <= n` works, i.e. the two length-`n` strings overlap in `n - s`.
    The weight w is the least such shift, so every `Wt n A U s` gives w <= s. -/
def Wt {α : Type} (n : Nat) (A U : List α) (s : Nat) : Prop := s ≤ n ∧ Ov A U (n - s)

/-- **Monge in weight form.**  If the link `b -> u` (shift `c`) is at least as tight as `a -> u` (shift `s₁`) and
    `b -> y` (shift `s₂`), then `a -> y` admits the shift `s₁ + s₂ - c` (whenever that is at most `n`). -/
theorem monge_weight {α : Type} (n : Nat) (A B U Y : List α) (c s₁ s₂ : Nat)
    (hBU : Wt n B U c) (hAU : Wt n A U s₁) (hBY : Wt n B Y s₂)
    (h1 : c ≤ s₁) (h2 : c ≤ s₂) (hsum : s₁ + s₂ ≤ n + c) : Wt n A Y (s₁ + s₂ - c) := by
  obtain ⟨hc, hBU⟩ := hBU
  obtain ⟨hs1, hAU⟩ := hAU
  obtain ⟨hs2, hBY⟩ := hBY
  refine ⟨by omega, ?_⟩
  have h := monge A B U Y (n - c) (n - s₁) (n - s₂) hBU hAU hBY (by omega) (by omega) (by omega)
  have e : n - s₁ + (n - s₂) - (n - c) = n - (s₁ + s₂ - c) := by omega
  rw [e] at h
  exact h

/-- the least-shift weight: `IsW n A U w` : `w` is a working shift and no smaller shift in `1 .. w - 1` works
    (shift `n` always works: the empty overlap). -/
def IsW {α : Type} (n : Nat) (A U : List α) (w : Nat) : Prop :=
  Wt n A U w ∧ ∀ s, Wt n A U s → w ≤ s

/-- **Four-point inequality for the weights** (the form used for the routes):
    w(b,u) <= min(w(a,u), w(b,y))  ==>  w(a,y) + w(b,u) <= w(a,u) + w(b,y). -/
theorem monge_four_point {α : Type} (n : Nat) (A B U Y : List α) (wbu wau wby way : Nat)
    (hbu : IsW n B U wbu) (hau : IsW n A U wau) (hby : IsW n B Y wby) (hay : IsW n A Y way)
    (h1 : wbu ≤ wau) (h2 : wbu ≤ wby) : way + wbu ≤ wau + wby := by
  have hayn : way ≤ n := hay.1.1
  by_cases hs : wau + wby ≤ n + wbu
  · have h := monge_weight n A B U Y wbu wau wby hbu.1 hau.1 hby.1 h1 h2 hs
    have := hay.2 _ h
    omega
  · omega

/-! ### Bookkeeping of a cut deletion

A route is a set of links; its length is 35288 + (sum of the link weights).  Deleting the cut at `u` replaces the
junctions `a -> u` (weight `wau`) and `b -> y` (weight `wby`) by `a -> y` (weight `way`) and the natural link `b -> u`
(weight `c`); `rest` is the weight of all other links. -/

theorem cut_deletion (rest wau wby way c : Nat) (hM : way + c ≤ wau + wby) :
    rest + way + c ≤ rest + wau + wby := by omega

/-- detour lemma L1 of Round R in the e-form: e(x,y) <= 1 + e(x,u) + e(u,y), with
    e(x,u) = wau - cu - 1, e(u,y) = wby - cy - 1, e(x,y) = way - cy - 1 (all e's are natural numbers here:
    wau >= cu + 1, wby >= cy + 1, way >= cy + 1 for links between different trails). -/
theorem detour_L1 (wau wby way cu cy : Nat) (hM : way + cu ≤ wau + wby)
    (h1 : cu + 1 ≤ wau) (h2 : cy + 1 ≤ wby) (h3 : cy + 1 ≤ way) :
    way - cy - 1 ≤ 1 + (wau - cu - 1) + (wby - cy - 1) := by omega

/-- detour lemma L2 (two cuts u₁, u₂ deleted one after the other): two Monge steps. -/
theorem detour_L2 (w01 w12 w2y w0y w1y c1 c2 : Nat)
    (hM2 : w1y + c2 ≤ w12 + w2y)          -- delete u₂ : junctions (b₁ -> u₂), (b₂ -> y) become (b₁ -> y)
    (hM1 : w0y + c1 ≤ w01 + w1y)          -- delete u₁ : junctions (a -> u₁), (b₁ -> y) become (a -> y)
    : w0y + c1 + c2 ≤ w01 + w12 + w2y := by omega

/-- a chain of Monge steps: deleting the cuts one after the other never increases the weight
    (`d i` is the weight change of step `i`, each `<= 0` written as `gain i >= 0`). -/
theorem chain_deletion (W0 : Nat) (gains : List Nat) (Wfinal : Nat)
    (h : Wfinal + gains.sum = W0) : Wfinal ≤ W0 := by omega

/-! ### Chain re-attachment (generalization of Theorem R8)

`k` consecutive full chains between the runs `Q_end` and `N_0`:
natural passage  : (k + 1) links of weight 3 and 6 k links of weight 2;
detached         : the skip link `Q_end -> N_0` of weight `3 + k` (machine fact, all 60 trail versions) and `k` closed
                   7-cycles of weight 14.
Both have the same weight, and by `monge` (links of weight 2 are at least as tight as everything) the route with the
`k` chains removed weighs at most (route weight) - 14 k.  Hence putting the chains back never increases the weight. -/

theorem reattach_weight (k : Nat) : 3 * (k + 1) + 12 * k = (3 + k) + 14 * k := by omega

theorem reattach (Wroute Wreduced k skip : Nat)
    (hskip : skip = 3 + k)                       -- weight of the skip link over k consecutive full chains
    (hmonge : Wreduced + 14 * k ≤ Wroute)        -- 7 k Monge steps with links of weight 2
    (hin : skip ≤ Wreduced)                      -- the skip link is a link of the reduced route
    : (Wreduced - skip) + (3 * (k + 1) + 12 * k) ≤ Wroute := by omega

/-- wrap removal with gap neighbours: deleting the two cuts at a wrapped full chain (junctions `a -> N_0` of weight
    `s`, wrap of weight 2, `P_end -> y` of weight `r`) gives `a -> y` and two natural links of weight 3.  By Monge on
    the skip link `P_end -> N_0` (weight 4) the change is `<= 0` when `s, r >= 4`. -/
theorem wrap_bypass (way s r : Nat) (hM : way + 4 ≤ s + r) : way + 3 + 3 ≤ s + 2 + r := by omega

/-- a ladder of `m >= 4` chain-start cuts between two kept cuts: all `m + 1` junctions join different trails and enter
    chain starts (weight `>= 4`), the new junction weighs at most 8, the `m` restored natural links weigh 3. -/
theorem ladder_long (m wnew wold : Nat) (hm : 4 ≤ m) (hnew : wnew ≤ 8) (hold : 4 * (m + 1) ≤ wold) :
    wnew + 3 * m ≤ wold := by omega

/-- length threshold: G = (sum of link weights) - 10874 and length = 46162 + G. -/
theorem length_of_weight (W G : Nat) (hW : W = 10874 + G) : 35288 + W = 46162 + G := by omega

#print axioms monge
#print axioms monge_weight
#print axioms monge_four_point
#print axioms prefix_split
#print axioms suffix_split
#print axioms cut_deletion
#print axioms detour_L1
#print axioms detour_L2
#print axioms chain_deletion
#print axioms reattach_weight
#print axioms reattach
#print axioms wrap_bypass
#print axioms ladder_long
#print axioms length_of_weight
