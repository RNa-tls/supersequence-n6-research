/-!
# Round P: soundness of the threshold search behind `min F = 22` (n = 8, 6A + 24φ, single-opening words)

Core Lean 4 (4.22), no Mathlib, no `sorry`, no `admit`, no custom axioms.

The finite computations (option tables, chain tables, the backward table H, the forward search) are done
by the two C/Python checkers and are NOT formalised here.  What is proved is the logic that turns their
output into the bound, for an arbitrary state type:

1. `bellman_bound`   : a potential h with h s ≤ c + h s' at every step of a path and h(last) ≤ end cost
                       is a lower bound of the remaining cost of the path.
2. `bellman_of_cover`: if h satisfies the Bellman inequality for every RELAXED transition, and every true
                       step is covered by a relaxed transition of smaller or equal cost (chain minimum K_a,
                       A identities free), then h satisfies the Bellman inequalities along every true path.
3. `bellman_sym`     : symmetry reduction — a potential that is invariant under a cost-preserving map σ and
                       satisfies the Bellman inequality at the representative σ s satisfies it at s.
4. `search_keeps`    : a layered search closed under its (lower-bound) transitions with the pruning test
                       value + cost + h ≤ THR keeps every true path of total cost ≤ THR at every layer,
                       with a value ≤ the true prefix cost.
5. `no_word_le`      : hence, if no final entry passes value + end bound ≤ THR, every word costs > THR.
6. `single_opening_bound` : F ≥ 22 ⇒ J = 77 + F ≥ 99 ⇒ length = 46085 + J ≥ 46184, and with the
                       explicit F = 22 word this is the exact optimum of the family.
-/

namespace SearchSoundness

/-- the steps of a word after its first state: (true cost of the step, state reached) -/
abbrev Steps (St : Type) := List (Nat × St)

def sumc {St : Type} : Steps St → Nat
  | [] => 0
  | (c, _) :: l => c + sumc l

def lastSt {St : Type} : St → Steps St → St
  | s, [] => s
  | _, (_, s') :: l => lastSt s' l

/-! ## 1. Bellman inequalities along a path -/

/-- Bellman inequalities of the potential h along the path from s with end cost fin -/
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

/-! ## 2. relaxed transitions cover the true steps -/

/-- every step of the path is covered by a transition of `Rel` whose cost is ≤ the true cost -/
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

/-- minimum of a nonempty list of costs (chain tables are such minima) -/
def lmin : List Nat → Nat
  | [] => 0
  | [a] => a
  | a :: b :: l => Nat.min a (lmin (b :: l))

theorem lmin_le : ∀ (l : List Nat) (x : Nat), x ∈ l → lmin l ≤ x := by
  intro l
  induction l with
  | nil => intro x hx; simp at hx
  | cons a l ih =>
    intro x hx
    cases l with
    | nil => simp at hx; simp [lmin, hx]
    | cons b l' =>
      simp only [lmin]
      rcases List.mem_cons.mp hx with h | h
      · subst h; exact Nat.min_le_left _ _
      · exact Nat.le_trans (Nat.min_le_right _ _) (ih x h)

/-! ## 3. symmetry reduction -/

theorem bellman_sym {St : Type} (Rel : St → Nat → St → Prop) (h : St → Nat) (σ : St → St)
    (hinv : ∀ x, h (σ x) = h x) (hpres : ∀ x c y, Rel x c y → Rel (σ x) c (σ y)) (s : St)
    (hrep : ∀ c y, Rel (σ s) c y → h (σ s) ≤ c + h y) :
    ∀ c s', Rel s c s' → h s ≤ c + h s' := by
  intro c s' hr
  have h1 := hrep c (σ s') (hpres s c s' hr)
  rw [hinv, hinv] at h1
  exact h1

/-! ## 4–5. the pruned layered search -/

/-- `Lay k s v`: state s is kept at layer k with value v.  Closure: a kept state, a search transition of
    cost ℓ and a passed pruning test give a kept successor with value ≤ v + ℓ. -/
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

/-- **Main lemma.**  A word = first state s1 with start cost c0, further steps l, end cost fin.
    If the start is generated whenever it passes the pruning test, the search is closed, every step of
    the word is covered by a search transition, the potential satisfies the Bellman inequalities along
    the word, the end bound finlb ≤ fin, and no final entry passes the final test, then the word costs
    more than THR. -/
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

/-! ## 6. the family bound -/

/-- J identity of the single-opening model (Round O): J = 48 + 29 + F; length identity: 46085 + J. -/
theorem single_opening_bound (F J len : Nat) (hJ : J = 48 + (30 - 1) + F) (hlen : len = 46085 + J)
    (hF : 21 < F) : 99 ≤ J ∧ 46184 ≤ len := by
  omega

/-- with an explicit word of F = 22 the bound is attained: the optimum of the family is J = 99. -/
theorem single_opening_optimum (Fw Jw lenw : Nat) (hJ : Jw = 48 + (30 - 1) + Fw) (hlen : lenw = 46085 + Jw)
    (hw : Fw = 22) : Jw = 99 ∧ lenw = 46184 := by
  omega

end SearchSoundness
