/-!
# Round M, section 25: small central statements of the joint opening / linking model (n = 8)

Core Lean 4 (4.22), no Mathlib, no `sorry`, no custom axioms.  The giant searches are NOT
formalized; the numerical certificate (`rM/certs/hk_46185_cert.npz`) is checked by
`rM/src/hk_check.py`, and this file proves that the inequality that checker evaluates is sound.

1. `family_cut`      : route steps = closed-trail edges − cuts + boundaries (any multiset split).
2. `chains_identity` : #chains of the route = Σ k_T + #(w2 cuts) − #(w2 boundaries)
                       (so an F-step cut costs exactly ΔE = +1, a cost-3 cut ΔE = 0, and a
                       w2 boundary repairs one unit).
3. `joint_J`         : J = E₀ + #(w2 cuts) + Σ_b (w_b − 3)
                       = E₀ + (P − 1) + [first cut is w2] + Σ_b (w_b − c_next − 1).
4. `dual_bound`      : weak duality with 0/1 variables and a safe correction for negative reduced
                       costs (the Held–Karp certificate inequality); `dual_bound_rhs` with
                       arbitrary right-hand sides (the single-opening LP certificate).
5. `hk_46185_final`  : the integer consequence of the checked certificate value.
-/

namespace OpeningJoint

/-! ## integer sums over lists -/

def isum : List Int → Int
  | [] => 0
  | a :: l => a + isum l

theorem isum_append (l₁ l₂ : List Int) : isum (l₁ ++ l₂) = isum l₁ + isum l₂ := by
  induction l₁ with
  | nil => simp [isum]
  | cons a l ih => simp only [List.cons_append, isum, ih]; omega

theorem isum_perm {l₁ l₂ : List Int} (h : l₁.Perm l₂) : isum l₁ = isum l₂ := by
  induction h with
  | nil => rfl
  | cons x _ ih => simp only [isum, ih]
  | swap x y l => simp only [isum]; omega
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

/-! ## 1. family-cut identity -/

/-- If the route's steps together with the cut edges are a rearrangement of the closed-trail
edges together with the boundary joins, then Σ route = Σ trails − Σ cuts + Σ boundaries.
With `L = 8 + Σ route` and `Σ trails = Σ_T (9|T| + k_T)` this is
`L = 8 + Σ_T (9|T| + k_T) + Σ_b w_b − Σ_c w_c` (46136 + … for the 46187 family). -/
theorem family_cut (cyc cuts route bnd : List Int) (h : (route ++ cuts).Perm (cyc ++ bnd)) :
    isum route = isum cyc - isum cuts + isum bnd := by
  have := isum_perm h
  rw [isum_append, isum_append] at this
  omega

/-! ## 2. chain count under openings (ΔE of an opening) -/

/-- number of entries `≠ 2` (the chain separators among inter-run steps) -/
def sep (l : List Int) : Nat := l.countP (fun w => w != 2)
/-- number of entries `= 2` -/
def two (l : List Int) : Nat := l.countP (fun w => w == 2)

theorem sep_two (l : List Int) : sep l + two l = l.length := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    simp only [sep, two, List.countP_cons, List.length_cons] at *
    by_cases h : a = 2 <;> simp [h] <;> omega

/-- `q = 1 + sep(route steps)`; the trails' cyclic inter-run edges have `sep = Σ k_T`
(one cost-3 edge per chain).  For `P` pieces (`P` cuts, `P − 1` boundaries):
`q = Σ k_T + #(w2 cuts) − #(w2 boundaries)`, i.e. `E = E₀ + #(w2 cuts) − #(w2 boundaries)`. -/
theorem chains_identity (cyc cuts route bnd : List Int)
    (h : (route ++ cuts).Perm (cyc ++ bnd)) (hP : cuts.length = bnd.length + 1) :
    (1 + sep route : Int) = sep cyc + two cuts - two bnd := by
  have h1 : sep (route ++ cuts) = sep (cyc ++ bnd) := List.Perm.countP_eq _ h
  simp only [sep, List.countP_append] at h1
  have a := sep_two cuts
  have b := sep_two bnd
  simp only [sep, two] at *
  omega

/-! ## 3. the joint objective of an opening pattern -/

/-- `J`-contribution of the boundaries: `E`-repair (w2), nothing (w3), new trail + excess (w ≥ 4) -/
def bcost : List Int → Int
  | [] => 0
  | w :: l => (if w = 2 then -1 else if w = 3 then 0 else 1 + (w - 4)) + bcost l

theorem bcost_eq (l : List Int) (h : ∀ w ∈ l, 2 ≤ w) : bcost l = isum (l.map (fun w => w - 3)) := by
  induction l with
  | nil => rfl
  | cons w l ih =>
    have hw : 2 ≤ w := h w (List.Mem.head _)
    have ih' := ih (fun x hx => h x (List.Mem.tail _ hx))
    simp only [bcost, List.map_cons, isum, ih']
    by_cases h2 : w = 2
    · simp [h2]
    · by_cases h3 : w = 3
      · simp [h3]
      · simp [h2, h3]; omega

/-- `J = E + (τ − 1) + λ` written over the pieces: `E = E₀ + #(w2 cuts) − #(w2 boundaries)`,
`τ − 1 = #(boundaries ≥ 4)`, `λ = Σ (w − 4)` over them; equal to `E₀ + #(w2 cuts) + Σ (w_b − 3)`. -/
theorem joint_J (E0 : Int) (cuts bnd : List Int) (hb : ∀ w ∈ bnd, 2 ≤ w) :
    E0 + (two cuts : Int) + bcost bnd = E0 + (two cuts : Int) + isum (bnd.map (fun w => w - 3)) := by
  rw [bcost_eq bnd hb]

/-- second form: pieces `k = 1..P−1` carry (cut weight `c_k ∈ {2,3}`, boundary weight `w_k` into
piece `k`); the first piece has cut weight `c₀`.  Then
`E₀ + #(w2 cuts) + Σ (w_k − 3) = E₀ + (P − 1) + [c₀ = 2] + Σ (w_k − c_k − 1)`. -/
def twoP : List (Int × Int) → Int
  | [] => 0
  | p :: l => (if p.1 = 2 then 1 else 0) + twoP l
def bsum : List (Int × Int) → Int
  | [] => 0
  | p :: l => (p.2 - 3) + bsum l
def esum : List (Int × Int) → Int
  | [] => 0
  | p :: l => (p.2 - p.1 - 1) + esum l

theorem joint_J_pieces (E0 c0 : Int) (ps : List (Int × Int)) (hc : ∀ p ∈ ps, p.1 = 2 ∨ p.1 = 3) :
    E0 + ((if c0 = 2 then 1 else 0) + twoP ps) + bsum ps
      = E0 + (ps.length : Int) + (if c0 = 2 then 1 else 0) + esum ps := by
  induction ps with
  | nil => simp [twoP, bsum, esum]
  | cons p l ih =>
    have hp := hc p (List.Mem.head _)
    have ih' := ih (fun x hx => hc x (List.Mem.tail _ hx))
    simp only [twoP, bsum, esum, List.length_cons] at *
    rcases hp with h | h <;> simp [h] at * <;> omega

/-- the 46185 records: `E₀ = 48`, six w2 cuts, first cut cost-3, boundaries
`3, 4 ×15, 5 ×8, 6 ×5` (29 boundaries, 30 pieces) give `J = 100`. -/
theorem record_46185 :
    (48 : Int) + 6 + isum ((([3] ++ List.replicate 15 4 ++ List.replicate 8 5 ++ List.replicate 5 6) : List Int).map (fun w => w - 3))
      = 100 := by decide

/-! ## 4. weak duality with 0/1 variables (Held–Karp certificate soundness) -/

def sumOver {α : Type} : List α → (α → Int) → Int
  | [], _ => 0
  | a :: t, f => f a + sumOver t f

theorem sumOver_add {α : Type} (l : List α) (f g : α → Int) :
    sumOver l (fun a => f a + g a) = sumOver l f + sumOver l g := by
  induction l with
  | nil => simp [sumOver]
  | cons a t ih => simp only [sumOver, ih]; omega

theorem sumOver_sub {α : Type} (l : List α) (f g : α → Int) :
    sumOver l (fun a => f a - g a) = sumOver l f - sumOver l g := by
  induction l with
  | nil => simp [sumOver]
  | cons a t ih => simp only [sumOver, ih]; omega

theorem sumOver_mul {α : Type} (l : List α) (k : Int) (f : α → Int) :
    sumOver l (fun a => k * f a) = k * sumOver l f := by
  induction l with
  | nil => simp [sumOver]
  | cons a t ih => simp only [sumOver, ih, Int.mul_add]

theorem sumOver_zero {α : Type} (l : List α) : sumOver l (fun _ => (0 : Int)) = 0 := by
  induction l with
  | nil => rfl
  | cons a t ih => simp only [sumOver, ih]; omega

theorem sumOver_cons {α : Type} (a : α) (t : List α) (f : α → Int) :
    sumOver (a :: t) f = f a + sumOver t f := rfl

theorem sumOver_comm {α β : Type} (l₁ : List α) (l₂ : List β) (f : α → β → Int) :
    sumOver l₁ (fun a => sumOver l₂ (fun b => f a b)) = sumOver l₂ (fun b => sumOver l₁ (fun a => f a b)) := by
  induction l₁ with
  | nil =>
    show (0 : Int) = sumOver l₂ (fun _ => (0 : Int))
    rw [sumOver_zero]
  | cons a t ih =>
    simp only [sumOver_cons]
    rw [ih]
    exact (sumOver_add l₂ (fun b => f a b) (fun b => sumOver t (fun a => f a b))).symm

theorem sumOver_mul_right {α : Type} (l : List α) (f : α → Int) (k : Int) :
    sumOver l f * k = sumOver l (fun a => f a * k) := by
  induction l with
  | nil => simp [sumOver]
  | cons a t ih => simp only [sumOver, Int.add_mul, ih]

theorem sumOver_le {α : Type} (l : List α) (f g : α → Int) (h : ∀ a ∈ l, f a ≤ g a) :
    sumOver l f ≤ sumOver l g := by
  induction l with
  | nil => simp [sumOver]
  | cons a t ih =>
    have h1 := h a (List.Mem.head _)
    have h2 := ih (fun x hx => h x (List.Mem.tail _ hx))
    simp only [sumOver]; omega

theorem sumOver_congr {α : Type} (l : List α) (f g : α → Int) (h : ∀ a ∈ l, f a = g a) :
    sumOver l f = sumOver l g := by
  induction l with
  | nil => rfl
  | cons a t ih =>
    have h1 := h a (List.Mem.head _)
    have h2 := ih (fun x hx => h x (List.Mem.tail _ hx))
    simp only [sumOver, h1, h2]

/-- **Safe dual bound.**  Variables `x_a ∈ {0, 1}` (as integers `0 ≤ x ≤ 1`), equality rows
`Σ_a AE r a · x a = 1` with free duals `π r`, covering rows `Σ_a AG s a · x a ≥ 1` with duals
`y s ≥ 0`.  For every such `x`:
`Σ c·x ≥ Σ π + Σ y + Σ_a min(rc_a, 0)`,  `rc_a = c_a − Σ_r π_r AE_{r a} − Σ_s y_s AG_{s a}`.
(For the run-level ATSP: rows = out/in degrees of the depot-closed Hamiltonian cycle, covering
rows = subtour cuts `x(δ⁺(S)) ≥ 1`; `hk_check.py` evaluates the right-hand side exactly.) -/
theorem dual_bound {α β γ : Type} (arcs : List α) (rowsE : List β) (rowsG : List γ)
    (c x : α → Int) (AE : β → α → Int) (AG : γ → α → Int) (π : β → Int) (y : γ → Int)
    (hx0 : ∀ a ∈ arcs, 0 ≤ x a) (hx1 : ∀ a ∈ arcs, x a ≤ 1)
    (hE : ∀ r ∈ rowsE, sumOver arcs (fun a => AE r a * x a) = 1)
    (hG : ∀ s ∈ rowsG, sumOver arcs (fun a => AG s a * x a) ≥ 1)
    (hy : ∀ s ∈ rowsG, 0 ≤ y s) :
    sumOver arcs (fun a => c a * x a) ≥
      sumOver rowsE π + sumOver rowsG y +
      sumOver arcs (fun a => min (c a - sumOver rowsE (fun r => π r * AE r a)
                                     - sumOver rowsG (fun s => y s * AG s a)) 0) := by
  -- names
  let PE := fun a => sumOver rowsE (fun r => π r * AE r a)
  let PG := fun a => sumOver rowsG (fun s => y s * AG s a)
  show sumOver arcs (fun a => c a * x a) ≥
      sumOver rowsE π + sumOver rowsG y + sumOver arcs (fun a => min (c a - PE a - PG a) 0)
  -- c x = rc x + PE x + PG x
  have split : sumOver arcs (fun a => c a * x a)
      = sumOver arcs (fun a => (c a - PE a - PG a) * x a) + sumOver arcs (fun a => PE a * x a)
        + sumOver arcs (fun a => PG a * x a) := by
    rw [← sumOver_add, ← sumOver_add]
    apply sumOver_congr; intro a _
    simp only [Int.sub_mul]; omega
  -- rc x ≥ min(rc, 0) for x ∈ {0, 1}
  have hrc : sumOver arcs (fun a => min (c a - PE a - PG a) 0) ≤
      sumOver arcs (fun a => (c a - PE a - PG a) * x a) := by
    apply sumOver_le; intro a ha
    have h0 := hx0 a ha; have h1 := hx1 a ha
    have : x a = 0 ∨ x a = 1 := by omega
    rcases this with h | h <;> simp [h] <;> omega
  -- Σ_a PE_a x_a = Σ_r π_r (Σ_a AE_ra x_a) = Σ_r π_r
  have hPE : sumOver arcs (fun a => PE a * x a) = sumOver rowsE π := by
    have e1 : sumOver arcs (fun a => PE a * x a)
        = sumOver arcs (fun a => sumOver rowsE (fun r => π r * (AE r a * x a))) := by
      apply sumOver_congr; intro a _
      show sumOver rowsE (fun r => π r * AE r a) * x a = _
      rw [sumOver_mul_right]
      apply sumOver_congr; intro r _
      rw [Int.mul_assoc]
    rw [e1, sumOver_comm]
    apply sumOver_congr; intro r hr
    rw [sumOver_mul, hE r hr, Int.mul_one]
  -- Σ_a PG_a x_a = Σ_s y_s (Σ_a AG_sa x_a) ≥ Σ_s y_s
  have hPG : sumOver rowsG y ≤ sumOver arcs (fun a => PG a * x a) := by
    have e1 : sumOver arcs (fun a => PG a * x a)
        = sumOver arcs (fun a => sumOver rowsG (fun s => y s * (AG s a * x a))) := by
      apply sumOver_congr; intro a _
      show sumOver rowsG (fun s => y s * AG s a) * x a = _
      rw [sumOver_mul_right]
      apply sumOver_congr; intro s _
      rw [Int.mul_assoc]
    rw [e1, sumOver_comm]
    apply sumOver_le; intro s hs
    rw [sumOver_mul]
    have g := hG s hs; have ys := hy s hs
    have : y s * (sumOver arcs (fun a => AG s a * x a) - 1) ≥ 0 :=
      Int.mul_nonneg ys (by omega)
    rw [Int.mul_sub, Int.mul_one] at this
    omega
  rw [split]
  show _ ≤ _
  have := hrc
  omega

/-- **Safe dual bound, general right-hand sides** (used for the single-opening LP certificate:
flow-conservation rows have right-hand side 0, selection / start / end rows 1, subtour rows ≥ 1).
For `0 ≤ x ≤ 1` (integers), equality rows `Σ_a AE r a · x a = bE r` (free duals `π r`) and covering
rows `Σ_a AG s a · x a ≥ bG s` (duals `y s ≥ 0`):
`Σ c·x ≥ Σ π·bE + Σ y·bG + Σ_a min(rc_a, 0)`. -/
theorem dual_bound_rhs {α β γ : Type} (arcs : List α) (rowsE : List β) (rowsG : List γ)
    (c x : α → Int) (AE : β → α → Int) (AG : γ → α → Int) (bE : β → Int) (bG : γ → Int)
    (π : β → Int) (y : γ → Int)
    (hx0 : ∀ a ∈ arcs, 0 ≤ x a) (hx1 : ∀ a ∈ arcs, x a ≤ 1)
    (hE : ∀ r ∈ rowsE, sumOver arcs (fun a => AE r a * x a) = bE r)
    (hG : ∀ s ∈ rowsG, sumOver arcs (fun a => AG s a * x a) ≥ bG s)
    (hy : ∀ s ∈ rowsG, 0 ≤ y s) :
    sumOver arcs (fun a => c a * x a) ≥
      sumOver rowsE (fun r => π r * bE r) + sumOver rowsG (fun s => y s * bG s) +
      sumOver arcs (fun a => min (c a - sumOver rowsE (fun r => π r * AE r a)
                                     - sumOver rowsG (fun s => y s * AG s a)) 0) := by
  let PE := fun a => sumOver rowsE (fun r => π r * AE r a)
  let PG := fun a => sumOver rowsG (fun s => y s * AG s a)
  show sumOver arcs (fun a => c a * x a) ≥
      sumOver rowsE (fun r => π r * bE r) + sumOver rowsG (fun s => y s * bG s)
        + sumOver arcs (fun a => min (c a - PE a - PG a) 0)
  have split : sumOver arcs (fun a => c a * x a)
      = sumOver arcs (fun a => (c a - PE a - PG a) * x a) + sumOver arcs (fun a => PE a * x a)
        + sumOver arcs (fun a => PG a * x a) := by
    rw [← sumOver_add, ← sumOver_add]
    apply sumOver_congr; intro a _
    simp only [Int.sub_mul]; omega
  have hrc : sumOver arcs (fun a => min (c a - PE a - PG a) 0) ≤
      sumOver arcs (fun a => (c a - PE a - PG a) * x a) := by
    apply sumOver_le; intro a ha
    have h0 := hx0 a ha; have h1 := hx1 a ha
    have : x a = 0 ∨ x a = 1 := by omega
    rcases this with h | h <;> simp [h] <;> omega
  have hPE : sumOver arcs (fun a => PE a * x a) = sumOver rowsE (fun r => π r * bE r) := by
    have e1 : sumOver arcs (fun a => PE a * x a)
        = sumOver arcs (fun a => sumOver rowsE (fun r => π r * (AE r a * x a))) := by
      apply sumOver_congr; intro a _
      show sumOver rowsE (fun r => π r * AE r a) * x a = _
      rw [sumOver_mul_right]
      apply sumOver_congr; intro r _
      rw [Int.mul_assoc]
    rw [e1, sumOver_comm]
    apply sumOver_congr; intro r hr
    rw [sumOver_mul, hE r hr]
  have hPG : sumOver rowsG (fun s => y s * bG s) ≤ sumOver arcs (fun a => PG a * x a) := by
    have e1 : sumOver arcs (fun a => PG a * x a)
        = sumOver arcs (fun a => sumOver rowsG (fun s => y s * (AG s a * x a))) := by
      apply sumOver_congr; intro a _
      show sumOver rowsG (fun s => y s * AG s a) * x a = _
      rw [sumOver_mul_right]
      apply sumOver_congr; intro s _
      rw [Int.mul_assoc]
    rw [e1, sumOver_comm]
    apply sumOver_le; intro s hs
    rw [sumOver_mul]
    have g := hG s hs; have ys := hy s hs
    have : y s * (sumOver arcs (fun a => AG s a * x a) - bG s) ≥ 0 :=
      Int.mul_nonneg ys (by omega)
    rw [Int.mul_sub] at this
    omega
  rw [split]
  have := hrc
  omega

/-! ## 5. the checked Held–Karp certificate for the 46185 run starts -/

/-- `hk_check.py` (duals scaled by 2^20) evaluates the right-hand side of `dual_bound` for the
5040 runs of the 46185 word plus the depot: `2^20 · cost ≥ 11389508186` for every depot-closed
Hamiltonian cycle; since the cost is an integer, `cost ≥ 10862`, i.e. `L = 35288 + cost ≥ 46150`
and `J = L − 46085 ≥ 65`. -/
theorem hk_46185_final (cost : Int) (h : 1048576 * cost ≥ 11389508186) :
    cost ≥ 10862 ∧ 35288 + cost ≥ 46150 ∧ 35288 + cost - 46085 ≥ 65 := by
  omega

/-- run-level identity: `L = 8 + 7·5040 + Σ inter-run weights = 35288 + cost`, `J = cost − 10797` -/
theorem run_level (cost : Int) : 8 + 7 * 5040 + cost = 35288 + cost ∧ (35288 + cost) - 46085 = cost - 10797 := by
  omega

end OpeningJoint
