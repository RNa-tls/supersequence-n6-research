/-
Round U -- soundness of an endpoint dynamic programme, Lean 4 core only.

A route is a list of moves from a start state; `step` says which moves are allowed and where they lead, `cost` is
the price of a move.  A table `h` on states is *consistent* if
    h s <= cost s a + h s'   for every allowed move  s --a--> s',      and   h s <= 0  on final states.
`dp_sound`: then every route from `s` to a final state costs at least `h s`.

The Held-Karp tables of Round T/U are such tables: state = (set of trails already written, last arc),
move = the next arc, cost = arc cost + (5 - overlap), final = all trails written.  The finite table is computed and
checked outside Lean; this file is the theorem that a consistent table is a lower bound.
`dp_sound_start` adds the choice of the first arc, `bound_of_min` turns it into the statement about the optimum.
-/

def runCost {S A : Type} (step : S → A → Option S) (cost : S → A → Int) : S → List A → Option (S × Int)
  | s, [] => some (s, 0)
  | s, a :: as =>
    match step s a with
    | none => none
    | some s' =>
      match runCost step cost s' as with
      | none => none
      | some (sf, c) => some (sf, cost s a + c)

theorem dp_sound {S A : Type} (step : S → A → Option S) (cost : S → A → Int) (final : S → Prop) (h : S → Int)
    (hfin : ∀ s, final s → h s ≤ 0)
    (hstep : ∀ s a s', step s a = some s' → h s ≤ cost s a + h s') :
    ∀ (as : List A) (s sf : S) (c : Int), runCost step cost s as = some (sf, c) → final sf → h s ≤ c := by
  intro as
  induction as with
  | nil =>
    intro s sf c hr hf
    simp [runCost] at hr
    obtain ⟨h1, h2⟩ := hr
    subst h1; subst h2
    exact hfin s hf
  | cons a as ih =>
    intro s sf c hr hf
    simp only [runCost] at hr
    cases hs : step s a with
    | none => simp [hs] at hr
    | some s' =>
      simp only [hs] at hr
      cases hrun : runCost step cost s' as with
      | none => simp [hrun] at hr
      | some p =>
        obtain ⟨sf', c'⟩ := p
        simp only [hrun] at hr
        have hr' : sf' = sf ∧ cost s a + c' = c := by simpa using hr
        obtain ⟨h1, h2⟩ := hr'
        subst h1
        have h3 := ih s' sf' c' hrun hf
        have h4 := hstep s a s' hs
        omega

/-- with a first move chosen from the start: every complete route costs at least `B` if `B <= init a + h (first a)` -/
theorem dp_sound_start {S A : Type} (step : S → A → Option S) (cost : S → A → Int) (final : S → Prop) (h : S → Int)
    (init : A → Int) (first : A → S) (B : Int)
    (hfin : ∀ s, final s → h s ≤ 0)
    (hstep : ∀ s a s', step s a = some s' → h s ≤ cost s a + h s')
    (hB : ∀ a, B ≤ init a + h (first a)) :
    ∀ (a : A) (as : List A) (sf : S) (c : Int), runCost step cost (first a) as = some (sf, c) → final sf →
      B ≤ init a + c := by
  intro a as sf c hr hf
  have h1 := dp_sound step cost final h hfin hstep as (first a) sf c hr hf
  have h2 := hB a
  omega

/-- decomposition used for bracket trees: a cost that splits into a path part and bracket parts, each bounded below -/
theorem sum_bound (l : List (Int × Int)) (h : ∀ p, p ∈ l → p.1 ≤ p.2) :
    (l.map Prod.fst).sum ≤ (l.map Prod.snd).sum := by
  induction l with
  | nil => simp
  | cons x t ih =>
    have h1 := h x (List.mem_cons_self ..)
    have h2 := ih (fun p hp => h p (List.mem_cons_of_mem _ hp))
    simp only [List.map_cons, List.sum_cons]
    omega

/-- the threshold form: if every represented route has J >= 24 then none has length <= 46172 on the public selection -/
theorem no_shorter (J : Int) (hJ : 24 ≤ J) : ¬ (46085 + 64 + J ≤ 46172) := by omega

#print axioms dp_sound
#print axioms dp_sound_start
#print axioms sum_bound
#print axioms no_shorter
