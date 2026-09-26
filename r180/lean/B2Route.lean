/-
Round 180 -- Bridge lemma B2 (run structure of a route), route-theoretic content.
Core Lean 4 only (no Mathlib).  Nothing about the alphabet size is assumed.

Setting.  `α` = the vertex set (permutations), `R : α → α` an injective map (the cyclic
rotation), `route : List α` (the Hamiltonian path).  Consecutive route vertices x, y form a
cost-1 edge iff y = R x (`cost_one_succ_is_rot` shows that for words an (n-1)-overlap
between two permutations of the same letters forces y = R x).
A *run start* is a route vertex not entered by a cost-1 edge.

Proved:
  * `cost_one_succ_is_rot` : if (a :: t) is a permutation of (t ++ [b]) then b = a,
                              i.e. an overlap of length |x|-1 between x and y forces y = R x;
  * `runStart_rot_iff`     : R e is a run start  <->  the route does not step e -> R e
                              (the unique cost-1 predecessor of R e is e, by injectivity);
  * `run_interior_not_start` : along a run s, R s, ..., R^k s (route steps), the vertices
                              R^i s (1 <= i <= k) are not run starts;
  * `run_end_next_is_start`  : if the run stops at R^k s, then R^(k+1) s is a run start.
Together: A(s), the first run start after s in R-order, is R^(k+1) s, and the run from s
ends at R^k s = R^{-1} A(s)  (Bridge B2).
-/

namespace B2Route

variable {α : Type}

/-- x and y are consecutive in the route. -/
def consec (route : List α) (x y : α) : Prop :=
  ∃ i : Nat, route[i]? = some x ∧ route[i + 1]? = some y

/-- y is a run start: a route vertex not entered by a cost-1 (R-)edge. -/
def runStart (route : List α) (R : α → α) (y : α) : Prop :=
  y ∈ route ∧ ¬ ∃ x, consec route x y ∧ y = R x

def iterR (R : α → α) : Nat → α → α
  | 0, x => x
  | k + 1, x => R (iterR R k x)

theorem runStart_rot_iff (route : List α) (R : α → α) (hR : ∀ a b, R a = R b → a = b)
    (e : α) (he : R e ∈ route) :
    runStart route R (R e) ↔ ¬ consec route e (R e) := by
  constructor
  · intro ⟨_, hno⟩ hc
    exact hno ⟨e, hc, rfl⟩
  · intro hnot
    refine ⟨he, ?_⟩
    intro ⟨x, hc, hx⟩
    have : x = e := (hR e x hx).symm
    subst this
    exact hnot hc

theorem run_interior_not_start (route : List α) (R : α → α) (s : α) (k : Nat)
    (hsteps : ∀ i, i < k → consec route (iterR R i s) (iterR R (i + 1) s)) :
    ∀ i, 1 ≤ i → i ≤ k → ¬ runStart route R (iterR R i s) := by
  intro i hi1 hik ⟨_, hno⟩
  obtain ⟨j, rfl⟩ : ∃ j, i = j + 1 := ⟨i - 1, by omega⟩
  exact hno ⟨iterR R j s, hsteps j (by omega), rfl⟩

theorem run_end_next_is_start (route : List α) (R : α → α)
    (hR : ∀ a b, R a = R b → a = b) (s : α) (k : Nat)
    (hstop : ¬ consec route (iterR R k s) (iterR R (k + 1) s))
    (hin : iterR R (k + 1) s ∈ route) :
    runStart route R (iterR R (k + 1) s) :=
  (runStart_rot_iff route R hR (iterR R k s) hin).2 hstop

/-- An overlap of length |x| - 1 between permutations x = a :: t and y = t ++ [b]
forces b = a, i.e. y = R x (cost one means rotation). -/
theorem cost_one_succ_is_rot [DecidableEq α] (a b : α) (t : List α)
    (hperm : (a :: t).Perm (t ++ [b])) : b = a := by
  have h := hperm.count_eq a
  simp [List.count_cons, List.count_append] at h
  exact h

end B2Route

#print axioms B2Route.runStart_rot_iff
#print axioms B2Route.run_interior_not_start
#print axioms B2Route.run_end_next_is_start
#print axioms B2Route.cost_one_succ_is_rot
