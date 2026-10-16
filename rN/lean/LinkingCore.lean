/-!
# Round N: trusted core of the opening–linking certificates (n = 8, r = 0)

Core Lean 4 (4.22), no Mathlib, no `sorry`, no `admit`, no custom axioms.
The searches (MIP, SAT, window re-optimisation) are NOT formalised.  This file proves the
small statements the certificates rely on:

1. `chain_form`        : Σ (w − 2) over run transitions = #(w ≥ 3) + Σ_{w ≥ 3} (w − 3);
                         with q = 1 + #(w ≥ 3) this is J = 48 + (q − 768) + Σ_{w≥3}(w − 3).
2. `segment_form`      : Σ_{w ≥ 3}(w − 3) = #(w ≥ 4) + Σ_{w ≥ 4}(w − 4)
                         (J − 48 = (S − 1) + splits + Σ_connections (w − 4)).
3. `charges_compose`   : if J − 48 = Σ_v cost v and cost v ≥ lb v for all v then J − 48 ≥ Σ lb.
4. `potential_bound`   : gap costs ≥ π_out + π_in  ⇒  Σ gaps ≥ Σ π_out + Σ π_in.
5. `pc_clause_sound`   : internal ≥ PC(r), PC antitone, r ≤ c  ⇒  internal ≥ PC(c)
                         (validity of the redundant path-cover clauses of the CNF).
6. `cap_relaxation`    : Σ min(e, 3) ≤ Σ e  (UNSAT of the capped CNF implies the uncapped claim).
7. `cut_charge`        : e_in ≥ IN, e_out ≥ OUT, IN + OUT ≥ 1  ⇒  e_in + e_out ≥ 1.
7b. `group_correction` : Σ x ≤ 1 over a column group, reduced costs ≥ g  ⇒  Σ min(d,0)·x ≥ min(g,0)
                         (the per-group term of the CC-LP certificate checkers).
8. `record_46185_*`    : the boundary data of the two 46185 words in every form give J = 100.
-/

namespace LinkingCore

def isum : List Int → Int
  | [] => 0
  | a :: l => a + isum l

theorem isum_append (l₁ l₂ : List Int) : isum (l₁ ++ l₂) = isum l₁ + isum l₂ := by
  induction l₁ with
  | nil => simp [isum]
  | cons a l ih => simp only [List.cons_append, isum, ih]; omega

/-- Σ f over a list -/
def fsum (f : Int → Int) : List Int → Int
  | [] => 0
  | a :: l => f a + fsum f l

/-- number of entries satisfying `p` -/
def cnt (p : Int → Bool) : List Int → Int
  | [] => 0
  | a :: l => (if p a then 1 else 0) + cnt p l

/-! ## 1. chain form of J -/

theorem chain_form (ws : List Int) (h : ∀ w ∈ ws, 2 ≤ w) :
    fsum (fun w => w - 2) ws
      = cnt (fun w => decide (3 ≤ w)) ws + fsum (fun w => if 3 ≤ w then w - 3 else 0) ws := by
  induction ws with
  | nil => rfl
  | cons a l ih =>
    have ha : 2 ≤ a := h a (List.mem_cons_self ..)
    have hl : ∀ w ∈ l, 2 ≤ w := fun w hw => h w (List.mem_cons_of_mem _ hw)
    simp only [fsum, cnt, ih hl]
    by_cases h3 : 3 ≤ a
    · simp [h3]; omega
    · have : a = 2 := by omega
      subst this; simp

/-- J = 48 + (q − 768) + Σ_{w ≥ 3}(w − 3) with q = 1 + #(w ≥ 3) and J = Σ (w − 2) − 719. -/
theorem J_chain (ws : List Int) (h : ∀ w ∈ ws, 2 ≤ w) (q : Int)
    (hq : q = 1 + cnt (fun w => decide (3 ≤ w)) ws) :
    fsum (fun w => w - 2) ws - 719 = 48 + (q - 768) + fsum (fun w => if 3 ≤ w then w - 3 else 0) ws := by
  rw [chain_form ws h]; omega

/-! ## 2. segment form -/

theorem segment_form (ws : List Int) :
    fsum (fun w => if 3 ≤ w then w - 3 else 0) ws
      = cnt (fun w => decide (4 ≤ w)) ws + fsum (fun w => if 4 ≤ w then w - 4 else 0) ws := by
  induction ws with
  | nil => rfl
  | cons a l ih =>
    simp only [fsum, cnt, ih]
    by_cases h4 : 4 ≤ a
    · have h3 : 3 ≤ a := by omega
      simp [h3, h4]; omega
    · by_cases h3 : 3 ≤ a
      · have : a = 3 := by omega
        subst this; simp
      · simp [h3, h4]

/-! ## 3. charge composition -/

def lsum {α : Type} (f : α → Int) : List α → Int
  | [] => 0
  | a :: l => f a + lsum f l

theorem lsum_le {α : Type} (f g : α → Int) (l : List α) (h : ∀ x ∈ l, g x ≤ f x) :
    lsum g l ≤ lsum f l := by
  induction l with
  | nil => simp [lsum]
  | cons a l ih =>
    simp only [lsum]
    have h1 := h a (List.mem_cons_self ..)
    have h2 := ih (fun x hx => h x (List.mem_cons_of_mem _ hx))
    omega

theorem charges_compose {α : Type} (J : Int) (cost lb : α → Int) (vs : List α)
    (hJ : J - 48 = lsum cost vs) (h : ∀ v ∈ vs, lb v ≤ cost v) : lsum lb vs ≤ J - 48 := by
  rw [hJ]; exact lsum_le cost lb vs h

/-! ## 4. potential (cut-weighting) soundness -/

theorem lsum_add {α : Type} (f g : α → Int) (l : List α) :
    lsum (fun x => f x + g x) l = lsum f l + lsum g l := by
  induction l with
  | nil => simp [lsum]
  | cons a l ih => simp only [lsum, ih]; omega

theorem potential_bound {α : Type} (gap pout pin : α → Int) (gs : List α)
    (h : ∀ g ∈ gs, pout g + pin g ≤ gap g) : lsum pout gs + lsum pin gs ≤ lsum gap gs := by
  rw [← lsum_add]; exact lsum_le gap (fun x => pout x + pin x) gs h

theorem lsum_mul {α : Type} (k : Int) (f : α → Int) (l : List α) :
    lsum (fun x => k * f x) l = k * lsum f l := by
  induction l with
  | nil => simp [lsum]
  | cons a l ih => simp only [lsum]; rw [ih, Int.mul_add]

/-- rational potentials (half charges) are handled by scaling: k·gap ≥ π_out + π_in. -/
theorem potential_bound_scaled {α : Type} (k : Int) (gap pout pin : α → Int) (gs : List α)
    (h : ∀ g ∈ gs, pout g + pin g ≤ k * gap g) : lsum pout gs + lsum pin gs ≤ k * lsum gap gs := by
  rw [← lsum_mul, ← lsum_add]; exact lsum_le _ (fun x => pout x + pin x) gs h

/-! ## 5. redundant path-cover clause -/

theorem pc_clause_sound (PC : Int → Int) (anti : ∀ a b, a ≤ b → PC b ≤ PC a)
    (internal r c : Int) (hint : PC r ≤ internal) (hrc : r ≤ c) : PC c ≤ internal :=
  Int.le_trans (anti r c hrc) hint

/-! ## 6. capping the excess at 3 is a relaxation -/

theorem cap_relaxation (es : List Int) :
    fsum (fun e => if e ≤ 3 then e else 3) es ≤ fsum (fun e => e) es := by
  induction es with
  | nil => simp [fsum]
  | cons a l ih =>
    simp only [fsum]
    by_cases h : a ≤ 3 <;> simp [h] <;> omega

theorem cap_unsat_transfer (es : List Int) (B : Int)
    (hcap : B < fsum (fun e => if e ≤ 3 then e else 3) es) : B < fsum (fun e => e) es :=
  Int.lt_of_lt_of_le hcap (cap_relaxation es)

/-! ## 7. cut charge of an A-bundle cut -/

theorem cut_charge (ein eout IN OUT : Int) (h1 : IN ≤ ein) (h2 : OUT ≤ eout) (h : 1 ≤ IN + OUT) :
    1 ≤ ein + eout := by omega

/-- a bridge φ → A → φ through one A piece costs β_in + β_out = 2 + e_in + e_out ≥ 3 -/
theorem bridge_three (ein eout : Int) (h : 1 ≤ ein + eout) : 3 ≤ (1 + ein) + (1 + eout) := by omega

/-! ## 7b. group correction of a dual certificate (CC-LP checkers `cc_cert.py`, `cc_cert_b.py`) -/

theorem lsum_nonneg {α : Type} (f : α → Int) (l : List α) (h : ∀ x ∈ l, 0 ≤ f x) : 0 ≤ lsum f l := by
  induction l with
  | nil => simp [lsum]
  | cons a l ih =>
    simp only [lsum]
    have h1 := h a (List.mem_cons_self ..)
    have h2 := ih (fun x hx => h x (List.mem_cons_of_mem _ hx))
    omega

/-- A group of columns whose 0/1 (or nonnegative) values sum to at most 1 and whose reduced costs
are all ≥ g contributes at least min(g, 0) to the safe correction Σ min(d, 0)·x of `dual_bound_rhs`
(Round M, `OpeningJoint.lean`).  This is the per-group term the CC-LP checkers add
(arcs by tail option, else arcs by tail trail, s, t, z, covers by component). -/
theorem group_correction {α : Type} (d x : α → Int) (g : Int) (cols : List α)
    (hg : ∀ j ∈ cols, g ≤ d j) (hx0 : ∀ j ∈ cols, 0 ≤ x j) (hsum : lsum x cols ≤ 1) :
    min g 0 ≤ lsum (fun j => min (d j) 0 * x j) cols := by
  have h1 : lsum (fun j => min g 0 * x j) cols ≤ lsum (fun j => min (d j) 0 * x j) cols :=
    lsum_le _ _ cols (fun j hj => Int.mul_le_mul_of_nonneg_right (by have := hg j hj; omega) (hx0 j hj))
  have h2 : lsum (fun j => min g 0 * x j) cols = min g 0 * lsum x cols := lsum_mul _ _ _
  have h4 : min g 0 * 1 ≤ min g 0 * lsum x cols := Int.mul_le_mul_of_nonpos_left (by omega) hsum
  rw [Int.mul_one] at h4
  rw [h2] at h1
  exact Int.le_trans h4 h1

/-- the integer consequence used in the report: a checked scaled total T with T > 16·2^30
gives Σe + [c0 = 2] ≥ 17 (the cost is an integer), i.e. J ≥ 77 + 17 = 94 -/
theorem cc_lp_integer (cost T : Int) (h : T ≤ 1073741824 * cost) (hT : 16 * 1073741824 < T) : 17 ≤ cost := by
  omega

/-! ## 8. the two 46185 words -/

/-- boundary weights of 46185 (both words have the same multiset) -/
def bw46185 : List Int := [4, 4, 4, 3, 4, 5, 4, 5, 4, 4, 5, 5, 4, 4, 5, 4, 5, 5, 4, 4, 6, 6, 6, 5, 4, 6, 4, 6, 4]
def bw46185b : List Int := [4, 4, 4, 3, 4, 5, 4, 5, 4, 4, 5, 5, 4, 4, 5, 5, 4, 5, 4, 4, 6, 6, 6, 5, 4, 6, 4, 6, 4]

/-- segment form: S − 1 = #(w ≥ 4) = 28, splits = 6 (F-step cuts), Σ (w − 4) = 18; 48 + 28 + 6 + 18 = 100 -/
theorem record_46185_segments :
    48 + cnt (fun w => decide (4 ≤ w)) bw46185 + 6 + fsum (fun w => if 4 ≤ w then w - 4 else 0) bw46185 = 100 ∧
    48 + cnt (fun w => decide (4 ≤ w)) bw46185b + 6 + fsum (fun w => if 4 ≤ w then w - 4 else 0) bw46185b = 100 := by
  decide

/-- excess form: e-histogram 12 × 0, 11 × 1, 6 × 2, P = 30, c₀ = 3: J = 48 + 29 + 0 + 23 = 100 -/
theorem record_46185_excess : 48 + 29 + 0 + (12 * 0 + 11 * 1 + 6 * 2) = (100 : Int) := by decide

end LinkingCore
