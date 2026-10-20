/-!
# Round Q: multi-opening words of the 6A+24φ family (n = 8, r = 0) — identities, visit lemma, split search logic

Core Lean 4 (4.22), no Mathlib, no `sorry`, no `admit`, no custom axioms.

What is formalised (the finite tables and searches are computed by the C checkers and are NOT formalised):

1. `J_identity`, `J_c2form`   : for any route of P ≥ 1 fragments with cut weights c_i ∈ {2,3} (the version join
                               removed at the start of fragment i) and P - 1 boundary join weights w_b,
                               L = 46136 + Σw - Σc, J = L - 46085 = 48 + [c_1 = 2] + Σ_b (w_b - c_{b+1})
                               = 48 + #(c = 2) + Σ_b (w_b - 3).
2. `visit_kappa_ge_last`       : wrap compensation — inside one visit (consecutive fragments of one trail),
                               with jumps of weight ≥ 3 into mid-chain fragments and ≥ 2 into chain-start
                               fragments, weight 2 only after a mid-chain fragment,
                               κ = [first mid] + Σ_jumps (w - c) ≥ [last mid] ≥ 0, and the jump part alone ≥ -1.
3. `zero_penalty_rotation`     : the rotated-chain excision (one extra visit, one wrap) changes J by exactly
                               the change of the cross-trail boundary terms (penalty +1 - 1 = 0).
4. `single_split_decomposition`: a single split (P = 31 fragments, virtual path + one cycle) has
                               J = 77 + G with G = 1 + F_J + β, F_J = [c_1 = 2] + Σ_{Σ-edges} e, β ≥ 0.
5. generic search soundness (copied from Round P `SearchSoundness`): `bellman_bound`, `bellman_of_cover`,
   `search_keeps`, `no_word_le`, used for the junction search with states (S, t, M, J).
6. `single_split_bound`        : no surviving junction pattern with G ≤ 21 ⇒ every single split has J ≥ 99,
                               length ≥ 46184.
-/

namespace MultiOpening

/-! ## 1. the multi-opening identity -/

def isum : List Int → Int
  | [] => 0
  | a :: l => a + isum l

/-- boundary terms w_b - c_{b+1}: the join into fragment b+1 minus that fragment's cut -/
def bterms : List Int → List Int → List Int
  | w :: ws, _ :: c :: cs => (w - c) :: bterms ws (c :: cs)
  | _, _ => []

theorem isum_bterms : ∀ (ws : List Int) (c1 : Int) (cs : List Int), ws.length = cs.length →
    isum (bterms ws (c1 :: cs)) = isum ws - isum cs := by
  intro ws
  induction ws with
  | nil => intro c1 cs h; cases cs with
    | nil => simp [bterms, isum]
    | cons _ _ => simp at h
  | cons w ws ih => intro c1 cs h; cases cs with
    | nil => simp at h
    | cons c cs => simp at h; simp only [bterms, isum]; rw [ih c cs h]; omega

/-- **Multi-opening identity.**  Base length: 5040 runs of 8 rotations, internal joins of all 30 closed version
    cycles weigh 10848 in total; a route removes the P cut joins and adds P - 1 boundary joins:
    L = 35288 + 10848 - Σc + Σw.  Then J = L - 46085 = 48 + (3 - c_1) + Σ_b (w_b - c_{b+1}). -/
theorem J_identity (c1 : Int) (cs ws : List Int) (L J : Int) (hlen : ws.length = cs.length)
    (hL : L = 35288 + 10848 - (c1 + isum cs) + isum ws) (hJ : J = L - 46085) :
    J = 48 + (3 - c1) + isum (bterms ws (c1 :: cs)) := by
  rw [isum_bterms ws c1 cs hlen]; omega

/-- number of cuts of weight 2 -/
def n2 : List Int → Int
  | [] => 0
  | c :: l => (if c = 2 then 1 else 0) + n2 l

theorem cut_sum (cs : List Int) (hc : ∀ c ∈ cs, c = 2 ∨ c = 3) : isum cs = 3 * cs.length - n2 cs := by
  induction cs with
  | nil => simp [isum, n2]
  | cons c l ih =>
    have h1 : c = 2 ∨ c = 3 := hc c (by simp)
    have h2 : ∀ x ∈ l, x = 2 ∨ x = 3 := fun x hx => hc x (by simp [hx])
    simp only [isum, n2, List.length_cons]; rw [ih h2]
    rcases h1 with h | h <;> subst h <;> simp <;> omega

/-- second form: J = 48 + #(c = 2) + Σ_b (w_b - 3) -/
theorem J_c2form (cs ws : List Int) (L J : Int) (hlen : ws.length + 1 = cs.length)
    (hc : ∀ c ∈ cs, c = 2 ∨ c = 3)
    (hL : L = 35288 + 10848 - isum cs + isum ws) (hJ : J = L - 46085) :
    J = 48 + n2 cs + (isum ws - 3 * ws.length) := by
  have := cut_sum cs hc; omega

/-! ## 2. wrap compensation inside a visit -/

/-- a fragment of a visit: `mid` = it starts inside a chain (cut weight 2), else at a chain start (cut 3);
    `w` = weight of the jump INTO it from the previous fragment of the same visit (unused for the first). -/
structure Frag where
  mid : Bool
  w : Int

def cutOf (f : Frag) : Int := if f.mid then 2 else 3
def ind (b : Bool) : Int := if b then 1 else 0

/-- jumps of a visit: Σ over fragments after the first of (w - cut) -/
def jumps : Frag → List Frag → Int
  | _, [] => 0
  | _, f :: l => (f.w - cutOf f) + jumps f l

/-- admissible jumps: into a mid-chain fragment w ≥ 3 (w = 2 there is the natural re-glue, excluded);
    into a chain start w ≥ 2, and w = 2 (the wrap C_end → C_start) only if the previous fragment starts
    inside that chain, i.e. is mid-chain. -/
def admissible : Frag → List Frag → Prop
  | _, [] => True
  | p, f :: l => (if f.mid then 3 ≤ f.w else (2 ≤ f.w ∧ (f.w = 2 → p.mid = true))) ∧ admissible f l

def lastF : Frag → List Frag → Frag
  | p, [] => p
  | _, f :: l => lastF f l

/-- telescoping: jumps ≥ [last mid] - [first mid] -/
theorem jumps_ge (p : Frag) (l : List Frag) (h : admissible p l) :
    ind (lastF p l).mid - ind p.mid ≤ jumps p l := by
  induction l generalizing p with
  | nil => simp [lastF, jumps]
  | cons f l ih =>
    simp only [admissible] at h
    obtain ⟨hf, hl⟩ := h
    have h2 := ih f hl
    simp only [lastF, jumps]
    cases hm : f.mid <;> cases hp : p.mid <;> simp only [hm, hp, cutOf, ind] at hf h2 ⊢ <;> simp at hf h2 ⊢ <;> omega

/-- **Visit lemma.**  κ(v) = [first fragment mid] + jumps ≥ [last fragment mid] ≥ 0. -/
theorem visit_kappa_ge_last (p : Frag) (l : List Frag) (h : admissible p l) :
    ind (lastF p l).mid ≤ ind p.mid + jumps p l := by
  have := jumps_ge p l h; omega

theorem visit_kappa_nonneg (p : Frag) (l : List Frag) (h : admissible p l) : 0 ≤ ind p.mid + jumps p l := by
  have h1 := visit_kappa_ge_last p l h
  have h0 : 0 ≤ ind (lastF p l).mid := by unfold ind; split <;> omega
  omega

/-- the jump part alone is ≥ -1 (so a non-first visit contributes ε = e_in + jumps ≥ -1, e_in ≥ 0) -/
theorem visit_jumps_ge_neg_one (p : Frag) (l : List Frag) (h : admissible p l) : -1 ≤ jumps p l := by
  have h1 := jumps_ge p l h
  have h0 : 0 ≤ ind (lastF p l).mid := by unfold ind; split <;> omega
  have h2 : ind p.mid ≤ 1 := by unfold ind; split <;> omega
  omega

/-! ## 3. zero-penalty rotated-chain excision -/

/-- visit form of J: J = 48 + κ_1 + Σ_{v ≥ 2} (w_in(v) - 3 + κ(v)); with V visits and the G-normalisation
    G = J - 77.  Splitting one visit into "chain C rotated" (κ = [mid] + wrap term = 1 + (2 - 3) = 0) and
    "the rest" (κ = 0, one new entering join) changes J exactly by the change of the entering join terms. -/
theorem zero_penalty_rotation (wA wB : Int) :
    (1 + (2 - 3 : Int)) + 0 + (wB - 3) - (wA - 3) = wB - wA := by omega

/-! ## 4. single-split decomposition -/

/-- A single split: 31 fragments, 30 boundaries (all cross-trail).  With e_b = w_b - c_{b+1} - 1 and the cover
    split into the path edges, the cycle edges other than the two at the anchor S(b), and those two:
    J = 48 + [c_1 = 2] + Σ (e_b + 1) = 77 + G, G = 1 + F_J + β. -/
theorem single_split_decomposition (c1 : Int) (eP eZ : List Int) (eb1 eb2 J : Int)
    (hcount : eP.length + eZ.length + 2 = 30)
    (hJ : J = 48 + (3 - c1) + (isum eP + eP.length) + (isum eZ + eZ.length) + (eb1 + 1) + (eb2 + 1)) :
    J = 77 + (1 + ((3 - c1) + isum eP + isum eZ) + (eb1 + eb2)) := by omega

/-- A single rotated-chain excision with the remainder R between SIGMA_j and SIGMA_{j+1} (neither is T): 32 fragments,
    31 boundaries = the 28 kept SIGMA edges eS (E' = e + 1), the two edges of R (E' = r + 1) and the wrap inside the
    rotated chain (E' = 2 - 3).  With J = 48 + [c1 = 2] + Σ E' (I2):  J = 77 + G,  G = F_J + (r1 + r2),
    F_J = (3 - c1) + Σ eS (the junction pattern value). -/
theorem excision_decomposition (c1 : Int) (eS : List Int) (r1 r2 J : Int) (hcount : eS.length = 28)
    (hJ : J = 48 + (3 - c1) + (isum eS + eS.length) + (r1 + 1) + (r2 + 1) + (2 - 3)) :
    J = 77 + (((3 - c1) + isum eS) + (r1 + r2)) := by omega

/-- the remainder at the very start: G = e(R_out -> o_1) + Σ e over the 29 SIGMA edges; with F = [c1 = 2] + Σ e ≥ 22
    this is ≥ 21, and = 21 forces F = 22, c1 = 2 and e(R_out -> o_1) = 0. -/
theorem excision_at_start (c1 sumE r G : Int) (hc : c1 = 2 ∨ c1 = 3) (hF : 22 ≤ (3 - c1) + sumE) (hr : 0 ≤ r)
    (hG : G = r + sumE) : 21 ≤ G ∧ (G = 21 → c1 = 2 ∧ r = 0 ∧ (3 - c1) + sumE = 22) := by
  rcases hc with h | h <;> subst h <;> omega

/-! ## 5. generic layered-search soundness (as in Round P `SearchSoundness`) -/

abbrev Steps (St : Type) := List (Nat × St)

def sumc {St : Type} : Steps St → Nat
  | [] => 0
  | (c, _) :: l => c + sumc l

def lastSt {St : Type} : St → Steps St → St
  | s, [] => s
  | _, (_, s') :: l => lastSt s' l

def bellman {St : Type} (h : St → Nat) : St → Steps St → Nat → Prop
  | s, [], fin => h s ≤ fin
  | s, (c, s') :: l, fin => h s ≤ c + h s' ∧ bellman h s' l fin

theorem bellman_bound {St : Type} (h : St → Nat) :
    ∀ (l : Steps St) (s : St) (fin : Nat), bellman h s l fin → h s ≤ sumc l + fin := by
  intro l
  induction l with
  | nil => intro s fin hb; simp only [bellman] at hb; simp only [sumc]; omega
  | cons p l ih =>
    intro s fin hb
    obtain ⟨c, s'⟩ := p
    simp only [bellman] at hb
    have h2 := ih s' fin hb.2
    simp only [sumc]
    omega

def covered {St : Type} (Rel : St → Nat → St → Prop) : St → Steps St → Prop
  | _, [] => True
  | s, (c, s') :: l => (∃ ℓ, ℓ ≤ c ∧ Rel s ℓ s') ∧ covered Rel s' l

theorem bellman_of_cover {St : Type} (Rel : St → Nat → St → Prop) (h : St → Nat)
    (hR : ∀ s ℓ s', Rel s ℓ s' → h s ≤ ℓ + h s') :
    ∀ (l : Steps St) (s : St) (fin : Nat), covered Rel s l → h (lastSt s l) ≤ fin → bellman h s l fin := by
  intro l
  induction l with
  | nil => intro s fin _ hf; simp only [lastSt] at hf; simp only [bellman]; exact hf
  | cons p l ih =>
    intro s fin hc hf
    obtain ⟨c, s'⟩ := p
    simp only [covered] at hc
    simp only [lastSt] at hf
    obtain ⟨⟨ℓ, hℓ, hr⟩, hc2⟩ := hc
    have h1 := hR s ℓ s' hr
    simp only [bellman]
    exact ⟨by omega, ih s' fin hc2 hf⟩

def closedUnder {St : Type} (RelS : St → Nat → St → Prop) (Lay : Nat → St → Nat → Prop) (h : St → Nat)
    (THR : Nat) : Prop :=
  ∀ k s v ℓ s', Lay k s v → RelS s ℓ s' → v + ℓ + h s' ≤ THR → ∃ v', v' ≤ v + ℓ ∧ Lay (k + 1) s' v'

theorem search_keeps {St : Type} (RelS : St → Nat → St → Prop) (Lay : Nat → St → Nat → Prop)
    (h : St → Nat) (THR : Nat) (hcl : closedUnder RelS Lay h THR) :
    ∀ (l : Steps St) (k : Nat) (s : St) (v g fin : Nat),
      Lay k s v → v ≤ g → covered RelS s l → bellman h s l fin → g + sumc l + fin ≤ THR →
      ∃ v', v' ≤ g + sumc l ∧ Lay (k + l.length) (lastSt s l) v' := by
  intro l
  induction l with
  | nil =>
    intro k s v g fin hL hv _ _ _
    exact ⟨v, by simp only [sumc]; omega, by simpa [lastSt] using hL⟩
  | cons p l ih =>
    intro k s v g fin hL hv hc hb hT
    obtain ⟨c, s'⟩ := p
    simp only [covered] at hc
    simp only [bellman] at hb
    obtain ⟨⟨ℓ, hℓ, hr⟩, hc2⟩ := hc
    have hrest := bellman_bound h l s' fin hb.2
    simp only [sumc] at hT
    have htest : v + ℓ + h s' ≤ THR := by omega
    obtain ⟨v1, hv1, hL1⟩ := hcl k s v ℓ s' hL hr htest
    have hT2 : (g + c) + sumc l + fin ≤ THR := by omega
    obtain ⟨v', hv', hL'⟩ := ih (k + 1) s' v1 (g + c) fin hL1 (by omega) hc2 hb.2 hT2
    refine ⟨v', ?_, ?_⟩
    · simp only [sumc]; omega
    · have hk : k + 1 + l.length = k + (l.length + 1) := by omega
      simp only [List.length_cons, lastSt]
      rw [← hk]; exact hL'

theorem no_word_le {St : Type} (RelS : St → Nat → St → Prop) (Lay : Nat → St → Nat → Prop)
    (h : St → Nat) (THR : Nat) (hcl : closedUnder RelS Lay h THR)
    (s1 : St) (c0 : Nat) (l : Steps St) (fin finlb : Nat)
    (hstart : c0 + h s1 ≤ THR → ∃ v, v ≤ c0 ∧ Lay 1 s1 v)
    (hcov : covered RelS s1 l) (hb : bellman h s1 l fin) (hfin : finlb ≤ fin)
    (hempty : ∀ v, Lay (1 + l.length) (lastSt s1 l) v → THR < v + finlb) :
    THR < c0 + sumc l + fin := by
  apply Classical.byContradiction
  intro hneg
  have hle : c0 + sumc l + fin ≤ THR := by omega
  have hh := bellman_bound h l s1 fin hb
  obtain ⟨v, hv, hL⟩ := hstart (by omega)
  obtain ⟨v', hv', hL'⟩ := search_keeps RelS Lay h THR hcl l 1 s1 v c0 fin hL hv hcov hb hle
  have := hempty v' hL'
  omega

/-! ## 6. the single-split bound -/

/-- if the junction search (THR = 20 on F_J) leaves no pattern whose exact value has G ≤ 21, then every single
    split satisfies G ≥ 22, so J = 77 + G ≥ 99 and the length 46085 + J ≥ 46184. -/
theorem single_split_bound (G J len : Int) (hJ : J = 77 + G) (hlen : len = 46085 + J) (hG : 22 ≤ G) :
    99 ≤ J ∧ 46184 ≤ len := by omega

end MultiOpening
