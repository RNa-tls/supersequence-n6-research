/-!
# Round L, sections 2 and 5: the fragmentation identity

An r = 0 route partitions the 5040 classes into chains; a chain is a segment of one world-orbit
(7 classes).  With chain lengths `l ∈ [1, 7]`:

  * `7 * q - 5040 = Σ (7 - l)`  (so `E = q - 720 = Σ (7 - l) / 7 ≥ 0`, exact);
  * per active world-orbit with `j ≥ 1` special classes covered by `s ≥ 1` segments,
    `7 s - j = (7 - j) + 7 (s - 1)`: a partial orbit costs `(7 - j)/7`, each extra segment
    costs exactly one unit (`E = Σ_{a,O} (seg - j/7)`, the "fragmentation conservation" law);
  * hence `q ≥ (number of active world-orbits)`, i.e. `E ≥ #active - 720`.

Core Lean 4, no Mathlib.
-/

namespace Fragmentation

def sumL : List Nat → Nat
  | [] => 0
  | l :: ls => l + sumL ls

def defic : List Nat → Nat
  | [] => 0
  | l :: ls => (7 - l) + defic ls

/-- `7 q = Σ l + Σ (7 - l)` for chain lengths `≤ 7` -/
theorem seven_q (ls : List Nat) (h : ∀ l ∈ ls, l ≤ 7) :
    7 * ls.length = sumL ls + defic ls := by
  induction ls with
  | nil => rfl
  | cons l ls ih =>
    have hl : l ≤ 7 := h l (List.Mem.head _)
    have ih' := ih (fun x hx => h x (List.Mem.tail _ hx))
    simp only [List.length_cons, sumL, defic]
    omega

/-- exact identity behind `E = q - 720 = Σ (7 - l)/7` -/
theorem frag_identity (ls : List Nat) (h : ∀ l ∈ ls, l ≤ 7) (hsum : sumL ls = 5040) :
    7 * ls.length - 5040 = defic ls ∧ ls.length ≥ 720 := by
  have := seven_q ls h
  omega

/-- per orbit: `s` segments covering the `j` special classes of a 7-class orbit -/
theorem orbit_cost (s j : Nat) (hs : s ≥ 1) (hj : j ≤ 7) :
    7 * s - j = (7 - j) + 7 * (s - 1) := by
  omega

/-- a partial orbit (`1 ≤ j ≤ 6`) costs at least `1/7`; an extra segment costs a full unit -/
theorem partial_orbit (s j : Nat) (hs : s ≥ 1) (hj1 : 1 ≤ j) (hj : j ≤ 6) : 7 * s - j ≥ 1 := by
  omega

theorem extra_segment (s j : Nat) (hs : s ≥ 2) (hj : j ≤ 7) : 7 * s - j ≥ 7 := by
  omega

end Fragmentation
