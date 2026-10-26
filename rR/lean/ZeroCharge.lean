/-
Round R -- Lean 4 (core only, no Mathlib): the zero-charge classification of visits (sections 3, 17-19, 22).

A visit of one trail-version is a first piece followed by jumps; every piece carries a flag `mid` (the piece starts
inside a chain, cut weight 2) or not (it starts at a chain start, cut weight 3).  A jump into a piece with flag `b`
costs `E` (E' = w(jump) - cut(target)).  The machine-checked jump facts (Round Q, rQ/certs/same_trail_jumps.json,
a_structure.json, rR/certs/chi0_building_blocks.json) are the hypotheses
  LocalOK  : every jump from a piece with flag a into a piece with flag b has  E ≥ [b] - [a]   (Lemma Q3, local form);
  IntoMidOK: every jump into a mid piece has E ≥ 1   (the only w = 2 arc into a mid run is the natural one, which
             merges the two pieces and is not a jump).
For a non-first visit with entry weight w_in (the w of the arc from the previous trail, w_in ≥ 3)
    chi = (w_in - 3) + [mid f_1] + sum E      (= e_in + 1 + sum E', e_in = w_in - cut(f_1) - 1).
Results:
  * `chi_eq`        : chi = (w_in - 3) + [mid f_last] + sum of jump excesses (telescoping);
  * `chi_nonneg`    : chi ≥ [mid f_last] ≥ 0;
  * `chi_zero`      : chi = 0  ->  w_in = 3, the last piece is not mid, every jump is tight;
  * `tight_grammar` : a tight visit obeys the grammar  mid -(E = -1, wrap)-> start,  start -(E = 0)-> start,
                      start -(E = 1)-> mid  (so chi = 0 visits are  ROT (J3m ROT | J3s START)*  when f_1 is mid);
  * `chi_zero_first_mid_wrap` : a chi = 0 visit whose first piece is mid starts with a wrap (E = -1);
  * `count_pos_le_sum`, `positive_visits_le` : the number of visits with chi ≥ 1 is at most sum chi = G + 29;
  * `zero_sum_all_zero` : a closed walk of total reduced cost 0 under a feasible potential uses only tight edges.
-/

structure Step where
  E : Int
  b : Bool

def bI (b : Bool) : Int := if b then 1 else 0

theorem bI_range (b : Bool) : 0 ≤ bI b ∧ bI b ≤ 1 := by cases b <;> simp [bI]

def jsum : List Step → Int
  | [] => 0
  | s :: l => s.E + jsum l

def lastFlag (a : Bool) : List Step → Bool
  | [] => a
  | s :: l => lastFlag s.b l

def LocalOK (a : Bool) : List Step → Prop
  | [] => True
  | s :: l => bI s.b - bI a ≤ s.E ∧ LocalOK s.b l

def IntoMidOK : List Step → Prop
  | [] => True
  | s :: l => (s.b = true → 1 ≤ s.E) ∧ IntoMidOK l

/-- sum over the jumps of the excess  E - ([b] - [a]) -/
def excess (a : Bool) : List Step → Int
  | [] => 0
  | s :: l => (s.E - (bI s.b - bI a)) + excess s.b l

def Tight (a : Bool) : List Step → Prop
  | [] => True
  | s :: l => s.E = bI s.b - bI a ∧ Tight s.b l

def Grammar (a : Bool) : List Step → Prop
  | [] => True
  | s :: l => ((a = true ∧ s.b = false ∧ s.E = -1) ∨ (a = false ∧ s.b = false ∧ s.E = 0) ∨
               (a = false ∧ s.b = true ∧ s.E = 1)) ∧ Grammar s.b l

theorem jsum_eq (a : Bool) : ∀ l : List Step, jsum l = excess a l + bI (lastFlag a l) - bI a
  | [] => by simp [jsum, excess, lastFlag]
  | s :: l => by
    have ih := jsum_eq s.b l
    simp only [jsum, excess, lastFlag] at ih ⊢
    omega

theorem excess_nonneg (a : Bool) : ∀ l : List Step, LocalOK a l → 0 ≤ excess a l
  | [] => fun _ => by simp [excess]
  | s :: l => fun h => by
    have ih := excess_nonneg s.b l h.2
    have h1 := h.1
    simp only [excess]
    omega

theorem excess_zero_tight (a : Bool) : ∀ l : List Step, LocalOK a l → excess a l = 0 → Tight a l
  | [] => fun _ _ => trivial
  | s :: l => fun h hz => by
    have hn := excess_nonneg s.b l h.2
    have h1 := h.1
    simp only [excess] at hz
    have hs : s.E = bI s.b - bI a := by omega
    have hr : excess s.b l = 0 := by omega
    exact ⟨hs, excess_zero_tight s.b l h.2 hr⟩

/-- the charge of a non-first visit -/
def chi (win : Int) (a : Bool) (l : List Step) : Int := (win - 3) + bI a + jsum l

theorem chi_eq (win : Int) (a : Bool) (l : List Step) :
    chi win a l = (win - 3) + bI (lastFlag a l) + excess a l := by
  have := jsum_eq a l
  simp only [chi]
  omega

theorem chi_nonneg (win : Int) (a : Bool) (l : List Step) (hw : 3 ≤ win) (h : LocalOK a l) :
    bI (lastFlag a l) ≤ chi win a l := by
  have := chi_eq win a l
  have := excess_nonneg a l h
  omega

theorem chi_zero (win : Int) (a : Bool) (l : List Step) (hw : 3 ≤ win) (h : LocalOK a l) (hz : chi win a l = 0) :
    win = 3 ∧ lastFlag a l = false ∧ Tight a l := by
  have he := chi_eq win a l
  have hn := excess_nonneg a l h
  have hb := bI_range (lastFlag a l)
  have hw3 : win = 3 := by omega
  have hl : bI (lastFlag a l) = 0 := by omega
  have hx : excess a l = 0 := by omega
  refine ⟨hw3, ?_, excess_zero_tight a l h hx⟩
  cases hc : lastFlag a l with
  | false => rfl
  | true => rw [hc] at hl; simp [bI] at hl

theorem tight_grammar (a : Bool) : ∀ l : List Step, Tight a l → IntoMidOK l → Grammar a l
  | [] => fun _ _ => trivial
  | s :: l => fun ht hm => by
    have ih := tight_grammar s.b l ht.2 hm.2
    refine ⟨?_, ih⟩
    have hE := ht.1
    have hmid := hm.1
    cases ha : a <;> cases hb : s.b
    · -- start -> start
      rw [ha, hb] at hE; simp [bI] at hE
      exact Or.inr (Or.inl ⟨rfl, rfl, hE⟩)
    · -- start -> mid
      rw [ha, hb] at hE; simp [bI] at hE
      exact Or.inr (Or.inr ⟨rfl, rfl, hE⟩)
    · -- mid -> start: the wrap
      rw [ha, hb] at hE; simp [bI] at hE
      exact Or.inl ⟨rfl, rfl, hE⟩
    · -- mid -> mid: tight means E = 0, but a jump into a mid piece costs ≥ 1
      rw [ha, hb] at hE; simp [bI] at hE
      have := hmid hb
      omega

/-- a chi = 0 visit whose first piece is mid (e_in = 0) begins with a wrap jump of cost -1 into a chain start -/
theorem chi_zero_first_mid_wrap (win : Int) (s : Step) (l : List Step) (hw : 3 ≤ win)
    (h : LocalOK true (s :: l)) (hm : IntoMidOK (s :: l)) (hz : chi win true (s :: l) = 0) :
    s.E = -1 ∧ s.b = false := by
  have ⟨_, _, ht⟩ := chi_zero win true (s :: l) hw h hz
  have g := tight_grammar true (s :: l) ht hm
  rcases g.1 with ⟨_, hb, hE⟩ | ⟨ha, _, _⟩ | ⟨ha, _, _⟩
  · exact ⟨hE, hb⟩
  · exact absurd ha (by decide)
  · exact absurd ha (by decide)

/-- a visit of one piece only (no jump) whose first piece is mid has chi ≥ 1: chi = 0 needs a jump -/
theorem chi_single_mid (win : Int) (hw : 3 ≤ win) : 1 ≤ chi win true [] := by
  simp [chi, bI, jsum]; omega

-- counting: visits of positive charge

def sumL : List Int → Int
  | [] => 0
  | x :: l => x + sumL l

def countPos : List Int → Nat
  | [] => 0
  | x :: l => (if 1 ≤ x then 1 else 0) + countPos l

def AllNonneg : List Int → Prop
  | [] => True
  | x :: l => 0 ≤ x ∧ AllNonneg l

theorem count_pos_le_sum : ∀ l : List Int, AllNonneg l → (countPos l : Int) ≤ sumL l
  | [] => fun _ => by simp [countPos, sumL]
  | x :: l => fun h => by
    have ih := count_pos_le_sum l h.2
    have hx := h.1
    simp only [countPos, sumL]
    by_cases hc : 1 ≤ x
    · simp [hc]; omega
    · simp [hc]; omega

/-- G = sum chi - 29 (charge theorem Q5): a route with G ≤ 20 has at most 49 visits of positive charge;
    every other visit has chi = 0, i.e. it is a rotational visit (chi_zero, tight_grammar) -/
theorem positive_visits_le (charges : List Int) (G : Int) (hG : G = sumL charges - 29) (h : AllNonneg charges)
    (h20 : G ≤ 20) : (countPos charges : Int) ≤ 49 := by
  have := count_pos_le_sum charges h
  omega

/-- zero cycles: if every reduced cost is ≥ 0 and the total is 0, every reduced cost is 0 (sections 17-19: a zero
    closed walk uses only tight edges, i.e. it lies inside one SCC of the tight subgraph) -/
theorem zero_sum_all_zero : ∀ l : List Int, AllNonneg l → sumL l = 0 → ∀ x ∈ l, x = 0
  | [] => fun _ _ x hx => absurd hx (by simp)
  | y :: l => fun h hs x hx => by
    have hy := h.1
    have hn : 0 ≤ sumL l := by
      have := count_pos_le_sum l h.2
      omega
    simp only [sumL] at hs
    have hy0 : y = 0 := by omega
    have hl0 : sumL l = 0 := by omega
    rcases List.mem_cons.mp hx with h1 | h1
    · rw [h1]; exact hy0
    · exact zero_sum_all_zero l h.2 hl0 x h1

/-- a bracket tree with c cycles has G = c + [cut first = 2] + sum e with every term ≥ 0, so G ≤ 20 forces c ≤ 20 -/
theorem brackets_le (c c1 S G : Int) (hG : G = c + c1 + S) (h1 : 0 ≤ c1) (hS : 0 ≤ S) (h20 : G ≤ 20) : c ≤ 20 := by
  omega

#print axioms chi_eq
#print axioms chi_nonneg
#print axioms chi_zero
#print axioms tight_grammar
#print axioms chi_zero_first_mid_wrap
#print axioms chi_single_mid
#print axioms count_pos_le_sum
#print axioms positive_visits_le
#print axioms zero_sum_all_zero
#print axioms brackets_le
