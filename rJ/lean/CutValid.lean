/-!
# Round J: validity of the subtour cuts used in the chain-ordering model

A route is a walk `D, v₁, …, v_m, D` (chains, possibly hub visits) that starts and ends at the
depot D.  The certificates use only cuts  x(δ⁺(S)) ≥ 1  with  D ∉ S  and  S containing a chain.
Every chain is visited by every route, so the walk visits S; since it ends at D ∉ S, some step of
the walk leaves S.  That step is an arc of δ⁺(S) used by the route, hence x(δ⁺(S)) ≥ 1.

The cut that broke an earlier round was S = {H} (hub only): a route that never visits H violates
it — `hub_only_cut_invalid` below records the counterexample, and it is excluded because the
hypothesis "S contains a visited node" fails.  Core Lean 4, no Mathlib.
-/

namespace CutValid

/-- consecutive steps of a walk -/
def steps {α : Type} : List α → List (α × α)
  | a :: b :: rest => (a, b) :: steps (b :: rest)
  | _ => []

/-- If a walk visits S and its last vertex lies outside S, some step leaves S. -/
theorem exists_exit {α : Type} (S : α → Bool) :
    ∀ (w : List α), (∃ v ∈ w, S v = true) → (∀ d, w.getLast? = some d → S d = false) →
      ∃ p ∈ steps w, S p.1 = true ∧ S p.2 = false
  | [], ⟨v, hv, _⟩, _ => by simp at hv
  | [a], ⟨v, hv, hs⟩, hl => by
      simp at hv; subst hv
      have := hl v (by simp); rw [this] at hs; exact absurd hs (by simp)
  | a :: b :: rest, ⟨v, hv, hs⟩, hl => by
      have hl' : ∀ d, (b :: rest).getLast? = some d → S d = false := by
        intro d hd; apply hl d; simp [List.getLast?_cons_cons] at hd ⊢; exact hd
      by_cases ha : S a = true
      · by_cases hb : S b = true
        · obtain ⟨p, hp, h1, h2⟩ := exists_exit S (b :: rest) ⟨b, by simp, hb⟩ hl'
          exact ⟨p, by simp [steps, hp], h1, h2⟩
        · exact ⟨(a, b), by simp [steps], ha, by simpa using hb⟩
      · have hv' : v ∈ b :: rest := by
          rcases List.mem_cons.mp hv with h | h
          · subst h; exact absurd hs ha
          · exact h
        obtain ⟨p, hp, h1, h2⟩ := exists_exit S (b :: rest) ⟨v, hv', hs⟩ hl'
        exact ⟨p, by simp [steps, hp], h1, h2⟩

/-- Cut validity for routes: a walk from D to D that visits some node of S, with D ∉ S,
uses at least one arc leaving S. -/
theorem route_crosses_cut {α : Type} (S : α → Bool) (D : α) (mid : List α)
    (hD : S D = false) (hvisit : ∃ v ∈ mid, S v = true) :
    ∃ p ∈ steps (D :: (mid ++ [D])), S p.1 = true ∧ S p.2 = false := by
  apply exists_exit S
  · obtain ⟨v, hv, hs⟩ := hvisit
    exact ⟨v, by simp [hv], hs⟩
  · intro d hd
    have : (D :: (mid ++ [D])).getLast? = some D := by
      rw [show D :: (mid ++ [D]) = (D :: mid) ++ [D] from rfl, List.getLast?_concat]
    rw [this] at hd; cases hd; exact hD

/-- The hub-only "cut" is not valid: the route D → c → D (chain c, no hub visit) has no step
leaving S = {H}.  (Nodes: D = 0, c = 1, H = 2.) -/
theorem hub_only_cut_invalid :
    ¬ ∃ p ∈ steps [0, 1, 0], (p.1 == 2) = true ∧ (p.2 == 2) = false := by
  decide

end CutValid
