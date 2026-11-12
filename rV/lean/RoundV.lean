/-
Round V -- Lean 4 core only (no Mathlib); no sorry, no admit, no user axiom.

* `ov_triangle`      : overlaps compose (triangle inequality of the overlap distance): if the last `a` symbols of `A`
                       are the first `a` of `P` and the last `b` of `P` are the first `b` of `D`, and `|P| <= a + b`,
                       then the last `a + b - |P|` symbols of `A` are the first of `D`.
* `shortcut_weight`  : in weights (w = n - overlap for words of length n): w(A, D) <= w(A, P) + w(P, D).
                       Hence a repeated visit of a permutation can be left out of a route without making it longer:
                       a shortest superpermutation may be taken to visit every permutation exactly once.
* `shortcut_total`   : the bookkeeping of that deletion.
* `wrap_identity`    : exact accounting of a wrap: a route R that uses the wrap of a chain C (gap cut with junctions
                       x' -> N0 and Q_end -> y', the detached chain inserted between x and y in rotation a) and the
                       route R'' in which C is put back after Q_end satisfy
                           J(R) = J(R'') + ins - 1 - delta,   ins = w(x, C_a) + w(C_(a-1), y) - w(x, y) - 2,
                           delta = w(C_6, y') - w(Q_end, y').
* `wrap_no_gain`     : so J(R) >= B whenever J(R'') >= B and ins >= 1 + delta.
* `trails_bound`     : J >= T - 1 for a route with P >= T pieces, first cut of weight <= 3 and all e >= 0.
* `frontier_46135`   : the two lines of Halfar's Theorem D do not exclude p = 0 .. 22 paid links at m = 50 (46135),
                       and the first line excludes every p >= 23 (p < 50).
-/

def Ov {α : Type} (A U : List α) (k : Nat) : Prop :=
  ∃ X S Z : List α, A = X ++ S ∧ U = S ++ Z ∧ S.length = k

theorem prefix_split {α : Type} {S₁ Z₁ S₂ Z₂ : List α} (h : S₁ ++ Z₁ = S₂ ++ Z₂)
    (hl : S₂.length ≤ S₁.length) : ∃ R, S₁ = S₂ ++ R ∧ Z₂ = R ++ Z₁ := by
  rcases List.append_eq_append_iff.mp h with ⟨a', h1, h2⟩ | ⟨c', h1, h2⟩
  · have hlen : S₂.length = S₁.length + a'.length := by rw [h1, List.length_append]
    have ha : a'.length = 0 := by omega
    have ha' : a' = [] := List.eq_nil_of_length_eq_zero ha
    subst ha'
    refine ⟨[], ?_, ?_⟩
    · simp at h1; simp [h1]
    · simp at h2; simp [h2]
  · exact ⟨c', h1, h2⟩

/-- **overlaps compose** -/
theorem ov_triangle {α : Type} (A P D : List α) (a b : Nat)
    (hAP : Ov A P a) (hPD : Ov P D b) (hlen : P.length ≤ a + b) : Ov A D (a + b - P.length) := by
  obtain ⟨X₁, S₁, Z₁, hA, hP1, hS1⟩ := hAP
  obtain ⟨X₂, S₂, Z₂, hP2, hD, hS2⟩ := hPD
  have hP : S₁ ++ Z₁ = X₂ ++ S₂ := by rw [← hP1, ← hP2]
  have hPlen : P.length = X₂.length + S₂.length := by rw [hP2, List.length_append]
  obtain ⟨R, hR1, hR2⟩ := prefix_split hP (by omega)
  refine ⟨X₁ ++ X₂, R, Z₁ ++ Z₂, ?_, ?_, ?_⟩
  · rw [hA, hR1, List.append_assoc]
  · rw [hD, hR2, List.append_assoc]
  · have h1 := congrArg List.length hR1
    rw [List.length_append] at h1
    omega

/-- weights: if `A -> P` can be made with a shift of `u` and `P -> D` with a shift of `v` (`u + v <= n`),
then `A -> D` can be made with a shift of `u + v`. -/
theorem shortcut_weight {α : Type} (A P D : List α) (n u v : Nat) (hn : P.length = n)
    (hu : u ≤ n) (hv : v ≤ n) (huv : u + v ≤ n)
    (hAP : Ov A P (n - u)) (hPD : Ov P D (n - v)) : Ov A D (n - (u + v)) := by
  have h := ov_triangle A P D (n - u) (n - v) hAP hPD (by omega)
  have e : n - u + (n - v) - P.length = n - (u + v) := by omega
  rw [e] at h
  exact h

/-- deleting a repeated visit: the two links `c -> p -> d` (weights `u`, `v`) are replaced by `c -> d` (weight `<= u + v`) -/
theorem shortcut_total (total u v wcd : Int) (h : wcd ≤ u + v) : total - u - v + wcd ≤ total := by omega

/-- **exact accounting of a wrap** -/
theorem wrap_identity (base w1 w2 wxy wq w6 JR JR2 : Int)
    (hR : JR = base + (-1) + 1 + (w1 - 3) + (w2 - 3) + (wq - 3))
    (hR2 : JR2 = base + 0 + (wxy - 3) + (w6 - 3)) :
    JR = JR2 + (w1 + w2 - wxy - 2) - 1 - (w6 - wq) := by omega

theorem wrap_no_gain (B JR JR2 ins delta : Int) (hid : JR = JR2 + ins - 1 - delta) (hB : B ≤ JR2)
    (hins : 1 + delta ≤ ins) : B ≤ JR := by omega

/-- `J = (P - 1) + (3 - c1) + E` with `E >= 0`, `c1 <= 3`, `P >= T`  gives  `J >= T - 1` -/
theorem trails_bound (J P T c1 E : Int) (hJ : J = (P - 1) + (3 - c1) + E) (hP : T ≤ P) (hc : c1 ≤ 3) (hE : 0 ≤ E) :
    T - 1 ≤ J := by omega

/-- the test of Theorem D for one number `p` of paid links (Halfar, `lineExcludes`) -/
def lineExcludes (k m p a b c : Nat) : Prop :=
  b * (k - 1) * (m - 1 - p) + c * (1 + p) < a * (720 + (m - 1 - p))

instance (k m p a b c : Nat) : Decidable (lineExcludes k m p a b c) := by
  unfold lineExcludes; infer_instance

theorem frontier_46135 :
    (∀ p, p ≤ 22 → ¬ lineExcludes 8 50 p 4 9 56 ∧ ¬ lineExcludes 8 50 p 17 38 264) ∧
    (∀ p, 23 ≤ p → p < 50 → lineExcludes 8 50 p 4 9 56) := by
  constructor
  · intro p hp
    unfold lineExcludes
    constructor <;> omega
  · intro p h1 h2
    unfold lineExcludes
    omega

/-- at 46134 (m = 49) the two lines leave exactly p = 2 -/
theorem frontier_46134 :
    (∀ p, p < 49 → p ≠ 2 → lineExcludes 8 49 p 4 9 56 ∨ lineExcludes 8 49 p 17 38 264) ∧
    ¬ lineExcludes 8 49 2 4 9 56 ∧ ¬ lineExcludes 8 49 2 17 38 264 := by
  refine ⟨?_, ?_, ?_⟩
  · intro p h1 h2
    unfold lineExcludes
    omega
  · unfold lineExcludes; omega
  · unfold lineExcludes; omega

#print axioms ov_triangle
#print axioms shortcut_weight
#print axioms shortcut_total
#print axioms wrap_identity
#print axioms wrap_no_gain
#print axioms trails_bound
#print axioms frontier_46135
#print axioms frontier_46134
