/-
Round T -- load-bearing arithmetic, Lean 4 core only (no Mathlib).

* `ledger`            : the common length ledger of both families,  L = 46085 + Q + J
* `ledger_e`          : the same in the project's e-form,  J = (P - 1) + (3 - c1) + sum e
* `record_threshold`  : on the public selection (Q = 64) a word of at most 46172 letters needs J <= 23
* `ten_letters`       : 46183 - 46173 = 10 as  -16 (rows) + 10 (openings) + 15 (fewer joins) + 1 (join excess)
* `rephasing`         : 46174 -> 46173 : openings +3, joins -4
* `tree_bound`        : a path part >= a and a bracket part >= b give J >= a + b
* `d8_arith`          : the arithmetic cell of Halfar's Theorem D at n = 8 (re-proved; the three chain hypotheses
                        enter through `Tri`)
-/

theorem sum_three_sub (l : List Int) : (l.map (fun c => 3 - c)).sum = 3 * (l.length : Int) - l.sum := by
  induction l with
  | nil => simp
  | cons a t ih => simp [List.sum_cons, ih]; omega

theorem sum_sub_three (l : List Int) : (l.map (fun w => w - 3)).sum = l.sum - 3 * (l.length : Int) := by
  induction l with
  | nil => simp
  | cons a t ih => simp [List.sum_cons, ih]; omega

/-- Route with cuts of natural weights `cs` and joins of weights `ws` (one join fewer than cuts) on a family whose
natural links weigh `10800 + Q` in total: length `35288 + (10800 + Q) - sum cs + sum ws`. -/
theorem ledger (Q : Int) (cs ws : List Int) (h : (ws.length : Int) + 1 = cs.length) :
    35288 + (10800 + Q) - cs.sum + ws.sum
      = 46085 + Q + ((cs.map (fun c => 3 - c)).sum + (ws.map (fun w => w - 3)).sum) := by
  rw [sum_three_sub, sum_sub_three]; omega

/-- e-form: with `e_j = w_j - c_{j+1} - 1` summed to `E`, first cut `c1`, `P` pieces:
`J = (P - 1) + (3 - c1) + E`. -/
theorem ledger_e (P c1 sc sw E : Int) (hE : E = sw - (sc - c1) - (P - 1)) :
    (3 * P - sc) + (sw - 3 * (P - 1)) = (P - 1) + (3 - c1) + E := by omega

theorem record_threshold (J : Int) (h : 46085 + 64 + J ≤ 46172) : J ≤ 23 := by omega

theorem record_threshold_e (P c1 E : Int) (hP : 16 ≤ P) (hc : c1 ≤ 3)
    (h : 46085 + 64 + ((P - 1) + (3 - c1) + E) ≤ 46172) : E ≤ 8 := by omega

/-- old 46183: Q = 48, openings 13, 30 joins of total cost 37;  public 46173: Q = 64, openings 3, 15 joins of cost 21 -/
theorem ten_letters :
    (46085 + 48 + (13 + 37) = 46183) ∧ (46085 + 64 + (3 + 21) = 46173) ∧
    ((48 - 64) + (13 - 3) + (30 - 15) + ((37 - 30) - (21 - 15)) = (10 : Int)) := by
  refine ⟨by decide, by decide, by decide⟩

theorem rephasing : (46149 + 0 + 25 = 46174) ∧ (46149 + 3 + 21 = 46173) ∧ ((3 - 0) + (21 - 25) = (-1 : Int)) := by
  refine ⟨by decide, by decide, by decide⟩

theorem tree_bound (J path brackets a b : Int) (hJ : J = path + brackets) (ha : a ≤ path) (hb : b ≤ brackets) :
    a + b ≤ J := by omega

/-- no bracket tree with a bracket reaches 46173 once every such tree has J >= 26 -/
theorem bracket_tree_length (J : Int) (h : 26 ≤ J) : 46175 ≤ 46085 + 64 + J := by omega

def Tri (r d n : Nat) : Prop :=
  4 * r ≤ 9 * d + 56 * n ∧ 17 * r ≤ 38 * d + 264 * n ∧
    (4 * r = 9 * d + 56 * n ∨ 4 * r + 3 ≤ 9 * d + 56 * n ∨ 17 * r + 7 ≤ 38 * d + 264 * n)

theorem d8_arith (w R D X J F cc : Nat) (hw : w + 8 ≤ 46133)
    (hcov : 7 * 46085 + D + 7 * (X + J) ≤ 7 * (w + 8)) (hhol : D + 7 * 720 = 7 * R)
    (hl1 : 4 * R + 5 * F ≤ 9 * D + 56 * (1 + X + J))
    (hl2 : 17 * R + 6 * F ≤ 38 * D + 264 * (1 + X + J)) (hcard : cc = F + J + 1)
    (htri : Tri R D (X + cc)) : False := by
  unfold Tri at htri
  have hC : R + (X + J) ≤ 768 := by omega
  have hA : 2296 + 5 * F ≤ 3 * R := by omega
  have hB : 15 * R + 6 * F ≤ 11496 := by omega
  have hF : F = 0 := by omega
  have hR : R = 766 := by omega
  have hp : X + J = 2 := by omega
  subst hF
  subst hR
  have hD : D = 322 := by omega
  subst hD
  have hn : X + cc = 3 := by omega
  rw [hn] at htri
  omega

/-- without the zone statement (third clause of `Tri`) the cell R = 766, D = 322, X + J = 2, F = 0 survives at 46133 -/
theorem d8_lines_only_cell :
    7 * 46085 + 322 + 7 * 2 ≤ 7 * 46133 ∧ 322 + 7 * 720 = 7 * 766 ∧
    4 * 766 + 5 * 0 ≤ 9 * 322 + 56 * (1 + 2) ∧ 17 * 766 + 6 * 0 ≤ 38 * 322 + 264 * (1 + 2) ∧
    ¬ Tri 766 322 3 := by
  refine ⟨by decide, by decide, by decide, by decide, ?_⟩
  unfold Tri; omega

#print axioms ledger
#print axioms ledger_e
#print axioms record_threshold
#print axioms record_threshold_e
#print axioms ten_letters
#print axioms rephasing
#print axioms tree_bound
#print axioms d8_arith
#print axioms d8_lines_only_cell
