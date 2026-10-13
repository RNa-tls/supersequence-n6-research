/-!
# Round K: soundness of the potential certificate of the trail automaton

`macro_check.py` accepts integer potentials `π` on the automaton states with

  * `π root = 0`,
  * `π v ≤ π u + w e` for every edge `e : u → v`   (w e = b·cost − a·classes),
  * `π v ≥ -b` for every state.

Then every path from the root has total weight `≥ -b`, i.e. `b·(chains + 1) ≥ a·classes`:
every trail satisfies `k + 1 ≥ (a/b)·|T|`.  Summing over the trails of an r = 0 route
(`Σ |T| = (n-1)!`) gives the lower bound on `Σ (k_T + 1)` used in the length identity.

Core Lean 4, no Mathlib.  A path is a list of edges `(u, v, w)` that is consecutive
(each edge starts where the previous one ended).
-/

namespace PotentialPath

/-- a path from `s` along edges `(u, v, w)`: consecutive edges, first edge starts at `s` -/
def IsPath : Nat → List (Nat × Nat × Int) → Prop
  | _, [] => True
  | s, (u, v, _) :: rest => u = s ∧ IsPath v rest

def weight : List (Nat × Nat × Int) → Int
  | [] => 0
  | (_, _, w) :: rest => w + weight rest

def last : Nat → List (Nat × Nat × Int) → Nat
  | s, [] => s
  | _, (_, v, _) :: rest => last v rest

/-- telescoping: along a path, the weight is at least the potential difference -/
theorem weight_ge (π : Nat → Int) (E : List (Nat × Nat × Int))
    (hE : ∀ e ∈ E, π e.2.1 ≤ π e.1 + e.2.2) :
    ∀ (s : Nat) (P : List (Nat × Nat × Int)), IsPath s P → (∀ e ∈ P, e ∈ E) →
      weight P ≥ π (last s P) - π s
  | s, [], _, _ => by simp [weight, last]
  | s, (u, v, w) :: rest, hp, hin => by
      obtain ⟨hu, hrest⟩ := hp
      have he : π v ≤ π u + w := hE (u, v, w) (hin _ (by simp))
      have ih := weight_ge π E hE v rest hrest (fun e he' => hin e (by simp [he']))
      simp only [weight, last]
      subst hu
      omega

/-- **Certificate soundness.**  With `π root = 0`, edge feasibility and `π ≥ -b`, every path
from the root (using automaton edges) has weight `≥ -b`. -/
theorem path_weight_ge (π : Nat → Int) (E : List (Nat × Nat × Int)) (root : Nat) (b : Int)
    (h0 : π root = 0) (hE : ∀ e ∈ E, π e.2.1 ≤ π e.1 + e.2.2) (hlow : ∀ v, π v ≥ -b)
    (P : List (Nat × Nat × Int)) (hp : IsPath root P) (hin : ∀ e ∈ P, e ∈ E) :
    weight P ≥ -b := by
  have := weight_ge π E hE root P hp hin
  have hl := hlow (last root P)
  omega

/-- **From trails to the route.**  If every trail satisfies `b·(k+1) ≥ a·|T|` and the trails'
class counts add up to `HEX`, then `b · Σ (k+1) ≥ a · HEX`. -/
theorem sum_bound (a b : Int) : ∀ (ts : List (Int × Int)),
    (∀ t ∈ ts, b * t.1 ≥ a * t.2) →
    b * (ts.map Prod.fst).foldr (· + ·) 0 ≥ a * (ts.map Prod.snd).foldr (· + ·) 0
  | [], _ => by simp
  | (k, c) :: rest, h => by
      have h1 := h (k, c) (by simp)
      have ih := sum_bound a b rest (fun t ht => h t (by simp [ht]))
      simp only [List.map_cons, List.foldr_cons] at *
      rw [Int.mul_add, Int.mul_add]
      omega

end PotentialPath
