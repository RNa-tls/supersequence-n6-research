/-!
# Round J: soundness of the exact dual bound used by the chain-set certificate checkers

Both checkers (`chainset_check.py`, `chainset_check2.py`) accept a leaf of the branch tree when

    LB = Σ_k y_k b_k + Σ_{j fixed to 1} r_j + Σ_{j free} min(0, r_j)  >  (T-1) * SCALE,
    r  = SCALE * w - Σ_k y_k a_k,

with y_k ≥ 0 on the `≥` rows.  This file proves, in core Lean 4 (no Mathlib), that every integer
point x with 0 ≤ x ≤ 1, consistent with the fixings and satisfying all rows, has
SCALE * (w·x) ≥ LB; hence LB > (T-1)*SCALE implies w·x ≥ T.  Fixing a free arc to 1 is the same
theorem with a different tag, which is what justifies reduced-cost fixing.

Vectors are integer lists of a common length A (one entry per arc).  A row is
`(a, b, isGe, y)`: coefficients, right-hand side, kind (`true` = `≥`, `false` = `=`), dual value.
Tags: 0 = fixed to 0, 1 = fixed to 1, anything else = free.
What is *not* formalised: that the Python checkers compute exactly these quantities from the
certificate, and that the rows (degree equations, subtour cuts) are valid for every route.
-/

namespace BoundSound

def dot : List Int → List Int → Int
  | a :: as, b :: bs => a * b + dot as bs
  | _, _ => 0

def vadd : List Int → List Int → List Int
  | a :: as, b :: bs => (a + b) :: vadd as bs
  | _, _ => []

def vsub : List Int → List Int → List Int
  | a :: as, b :: bs => (a - b) :: vsub as bs
  | _, _ => []

def smul (c : Int) : List Int → List Int
  | [] => []
  | a :: as => (c * a) :: smul c as

def zeros : Nat → List Int
  | 0 => []
  | n + 1 => 0 :: zeros n

abbrev Row := List Int × Int × Bool × Int

/-- A^T y = Σ_k y_k a_k -/
def aty (A : Nat) : List Row → List Int
  | [] => zeros A
  | (a, _, _, yk) :: rs => vadd (smul yk a) (aty A rs)

/-- Σ_k y_k b_k -/
def yb : List Row → Int
  | [] => 0
  | (_, b, _, yk) :: rs => yk * b + yb rs

/-- Σ_k y_k (a_k · x) -/
def yAx (x : List Int) : List Row → Int
  | [] => 0
  | (a, _, _, yk) :: rs => yk * dot a x + yAx x rs

/-- per-arc lower contributions: 0 (fixed 0), r (fixed 1), min 0 r (free) -/
def loSum : List Int → List Nat → Int
  | r :: rs, t :: ts => (if t = 0 then 0 else if t = 1 then r else min 0 r) + loSum rs ts
  | _, _ => 0

/-- x is a 0/1 vector consistent with the tags (and of the same length) -/
def xOK : List Int → List Nat → Prop
  | x :: xs, t :: ts => (0 ≤ x ∧ x ≤ 1) ∧ (t = 0 → x = 0) ∧ (t = 1 → x = 1) ∧ xOK xs ts
  | [], [] => True
  | _, _ => False

/-! ## linearity of `dot` -/

theorem length_vadd : ∀ (u v : List Int), u.length = v.length → (vadd u v).length = u.length
  | [], [], _ => rfl
  | _ :: us, _ :: vs, h => by
      simp only [vadd, List.length_cons] at *
      rw [length_vadd us vs (by omega)]
  | [], _ :: _, h => by simp at h
  | _ :: _, [], h => by simp at h

theorem length_vsub : ∀ (u v : List Int), u.length = v.length → (vsub u v).length = u.length
  | [], [], _ => rfl
  | _ :: us, _ :: vs, h => by
      simp only [vsub, List.length_cons] at *
      rw [length_vsub us vs (by omega)]
  | [], _ :: _, h => by simp at h
  | _ :: _, [], h => by simp at h

theorem length_smul (c : Int) : ∀ (u : List Int), (smul c u).length = u.length
  | [] => rfl
  | _ :: us => by simp only [smul, List.length_cons, length_smul c us]

theorem length_zeros : ∀ n, (zeros n).length = n
  | 0 => rfl
  | n + 1 => by simp only [zeros, List.length_cons, length_zeros n]

theorem dot_vadd : ∀ (u v x : List Int), u.length = x.length → v.length = x.length →
    dot (vadd u v) x = dot u x + dot v x
  | [], [], [], _, _ => by simp [vadd, dot]
  | a :: us, b :: vs, c :: xs, hu, hv => by
      simp only [List.length_cons] at hu hv
      simp only [vadd, dot]
      rw [dot_vadd us vs xs (by omega) (by omega), Int.add_mul]
      omega
  | [], _ :: _, _, hu, hv => by simp at hu hv; omega
  | _ :: _, [], _, hu, hv => by simp at hu hv; omega
  | [], [], _ :: _, hu, _ => by simp at hu
  | _ :: _, _ :: _, [], hu, _ => by simp at hu

theorem dot_vsub : ∀ (u v x : List Int), u.length = x.length → v.length = x.length →
    dot (vsub u v) x = dot u x - dot v x
  | [], [], [], _, _ => by simp [vsub, dot]
  | a :: us, b :: vs, c :: xs, hu, hv => by
      simp only [List.length_cons] at hu hv
      simp only [vsub, dot]
      rw [dot_vsub us vs xs (by omega) (by omega), Int.sub_mul]
      omega
  | [], _ :: _, _, hu, hv => by simp at hu hv; omega
  | _ :: _, [], _, hu, hv => by simp at hu hv; omega
  | [], [], _ :: _, hu, _ => by simp at hu
  | _ :: _, _ :: _, [], hu, _ => by simp at hu

theorem dot_smul (c : Int) : ∀ (u x : List Int), dot (smul c u) x = c * dot u x
  | [], _ => by simp [smul, dot]
  | _ :: _, [] => by simp [smul, dot]
  | a :: us, b :: xs => by
      simp only [smul, dot]
      rw [dot_smul c us xs, Int.mul_add, Int.mul_assoc]

theorem dot_zeros : ∀ (n : Nat) (x : List Int), dot (zeros n) x = 0
  | 0, _ => by simp [zeros, dot]
  | _ + 1, [] => by simp [zeros, dot]
  | n + 1, _ :: xs => by simp only [zeros, dot, dot_zeros n xs]; omega

theorem length_aty (A : Nat) : ∀ (R : List Row), (∀ r ∈ R, r.1.length = A) → (aty A R).length = A
  | [], _ => by simp [aty, length_zeros]
  | (a, b, g, yk) :: rs, h => by
      have ha : a.length = A := h (a, b, g, yk) (by simp)
      have hr : ∀ r ∈ rs, r.1.length = A := fun r hr => h r (by simp [hr])
      simp only [aty]
      rw [length_vadd _ _ (by rw [length_smul, length_aty A rs hr, ha]), length_smul, ha]

theorem dot_aty (A : Nat) (x : List Int) (hx : x.length = A) :
    ∀ (R : List Row), (∀ r ∈ R, r.1.length = A) → dot (aty A R) x = yAx x R
  | [], _ => by simp [aty, yAx, dot_zeros]
  | (a, b, g, yk) :: rs, h => by
      have ha : a.length = A := h (a, b, g, yk) (by simp)
      have hr : ∀ r ∈ rs, r.1.length = A := fun r hr => h r (by simp [hr])
      simp only [aty, yAx]
      rw [dot_vadd _ _ _ (by rw [length_smul, ha, hx]) (by rw [length_aty A rs hr, hx]),
          dot_smul, dot_aty A x hx rs hr]

/-! ## the two inequalities -/

/-- feasibility of the rows at x, and the sign condition on the duals of `≥` rows -/
def rowsOK (x : List Int) (R : List Row) : Prop :=
  ∀ r ∈ R, (r.2.2.1 = true → dot r.1 x ≥ r.2.1 ∧ r.2.2.2 ≥ 0) ∧ (r.2.2.1 = false → dot r.1 x = r.2.1)

theorem yAx_ge_yb (x : List Int) : ∀ (R : List Row), rowsOK x R → yAx x R ≥ yb R
  | [], _ => by simp [yAx, yb]
  | (a, b, g, yk) :: rs, h => by
      have h0 := h (a, b, g, yk) (by simp)
      have hr : rowsOK x rs := fun r hr => h r (by simp [hr])
      have ih := yAx_ge_yb x rs hr
      simp only [yAx, yb]
      cases g with
      | true =>
          have ⟨hd, hy⟩ := h0.1 rfl
          have : yk * dot a x ≥ yk * b := Int.mul_le_mul_of_nonneg_left hd hy
          omega
      | false =>
          have hd : dot a x = b := h0.2 rfl
          rw [hd]; omega

theorem dot_ge_loSum : ∀ (r x : List Int) (t : List Nat), r.length = x.length → xOK x t →
    dot r x ≥ loSum r t
  | [], [], [], _, _ => by simp [dot, loSum]
  | rj :: rs, xj :: xs, tj :: ts, hl, h => by
      simp only [List.length_cons] at hl
      obtain ⟨⟨h0, h1⟩, ht0, ht1, hrest⟩ := h
      have ih := dot_ge_loSum rs xs ts (by omega) hrest
      simp only [dot, loSum]
      have hx01 : xj = 0 ∨ xj = 1 := by omega
      rcases hx01 with hx | hx
      · subst hx
        by_cases a0 : tj = 0
        · simp [a0]; omega
        · by_cases a1 : tj = 1
          · exact absurd (ht1 a1) (by omega)
          · simp [a0, a1]; omega
      · subst hx
        by_cases a0 : tj = 0
        · exact absurd (ht0 a0) (by omega)
        · by_cases a1 : tj = 1
          · simp [a1]; omega
          · simp [a0, a1]; omega
  | [], _ :: _, _, hl, _ => by simp at hl
  | _ :: _, [], _, hl, _ => by simp at hl
  | [], [], _ :: _, _, h => by simp [xOK] at h
  | _ :: _, _ :: _, [], _, h => by simp [xOK] at h

/-! ## main theorem -/

/-- **Soundness of the checkers' bound.**  For every 0/1 point x consistent with the tags and
satisfying all rows:  SCALE * (w·x) ≥ Σ y_k b_k + loSum(r, tags),  r = SCALE*w − A^T y. -/
theorem bound_sound (A : Nat) (SC : Int) (w x : List Int) (tag : List Nat) (R : List Row)
    (hw : w.length = A) (hx : x.length = A)
    (hR : ∀ r ∈ R, r.1.length = A) (hrows : rowsOK x R) (hxok : xOK x tag) :
    SC * dot w x ≥ yb R + loSum (vsub (smul SC w) (aty A R)) tag := by
  have hlen : (vsub (smul SC w) (aty A R)).length = x.length := by
    have h1 : (smul SC w).length = A := by rw [length_smul, hw]
    have h2 : (aty A R).length = A := length_aty A R hR
    rw [length_vsub _ _ (by rw [h1, h2]), h1, hx]
  have hr := dot_ge_loSum (vsub (smul SC w) (aty A R)) x tag hlen hxok
  have hsplit : dot (vsub (smul SC w) (aty A R)) x = SC * dot w x - yAx x R := by
    rw [dot_vsub _ _ _ (by rw [length_smul, hw, hx]) (by rw [length_aty A R hR, hx]),
        dot_smul, dot_aty A x hx R hR]
  have hy := yAx_ge_yb x R hrows
  omega

/-- **Pruning.**  If the checkers' bound exceeds (T-1)*SCALE with SCALE > 0, every such x has
w·x ≥ T, i.e. the node contains no route of weight ≤ T-1. -/
theorem prune_sound (A : Nat) (SC T : Int) (w x : List Int) (tag : List Nat) (R : List Row)
    (hSC : 0 < SC) (hw : w.length = A) (hx : x.length = A)
    (hR : ∀ r ∈ R, r.1.length = A) (hrows : rowsOK x R) (hxok : xOK x tag)
    (hlb : yb R + loSum (vsub (smul SC w) (aty A R)) tag > (T - 1) * SC) :
    dot w x ≥ T := by
  have hb := bound_sound A SC w x tag R hw hx hR hrows hxok
  have h1 : SC * (T - 1) < SC * dot w x := by rw [Int.mul_comm SC (T - 1)]; omega
  have h2 : T - 1 < dot w x := Int.lt_of_mul_lt_mul_left h1 (Int.le_of_lt hSC)
  omega

end BoundSound
