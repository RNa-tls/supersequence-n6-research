/-
Final round -- core Lean 4 only.
(1) `conservation` : arithmetic of the exact conservation law (Theorem C of the report), c = n - 2:
      c (D + 1) + V_nf = ORB + u_out + (c+1) a + c (dS + dtau) + dseg
    from the Bridge definitions and the segment / trail bookkeeping (all as hypotheses).
(2) `tm_*` : word facts behind Theorem Q (the NF counterexample family): for a start
      p = A ++ [x, y, z] ++ [s],  tm p = [z] ++ A ++ [y, x] ++ [s];
    tm keeps y in the hidden position |A|+1, its word is a rotation of p's word with x, y swapped,
    and deleting y gives the same word (the frame (F, y) is invariant).
-/
namespace ConsTm

theorem conservation (c ORB m r a k u b eta D Frows Nnf Vnf G uout Sf tau dseg dS dtau : Nat)
    (hk : k + r = ORB + m + a)            -- Bridge: k = ORB + m - r + a
    (hu : u + r = (c + 1) * m)            -- Bridge: u = (n-1) m - r
    (hD : D = m + a + b + eta)
    (hkF : k = Frows + Nnf)
    (hG : G + Vnf = (c + 1) * Nnf)        -- total charge + visible states of non-full rows
    (huo : u = G + uout)
    (hseg : Frows + dseg = c * Sf)
    (hS : Sf + dS = tau + Nnf)
    (htau : tau + dtau = 1 + b + eta) :
    c * (D + 1) + Vnf = ORB + uout + (c + 1) * a + c * (dS + dtau) + dseg := by
  have hu' : u + r = c * m + m := by rw [hu, Nat.add_mul, Nat.one_mul]
  have hD' : c * D = c * m + c * a + c * b + c * eta := by
    rw [hD, Nat.mul_add, Nat.mul_add, Nat.mul_add]
  have hS' : c * Sf + c * dS = c * tau + c * Nnf := by
    rw [← Nat.mul_add, ← Nat.mul_add, hS]
  have ht' : c * tau + c * dtau = c + c * b + c * eta := by
    rw [← Nat.mul_add, htau, Nat.mul_add, Nat.mul_add, Nat.mul_one]
  have hG' : G + Vnf = c * Nnf + Nnf := by rw [hG, Nat.add_mul, Nat.one_mul]
  have e1 : c * (D + 1) = c * D + c := by rw [Nat.mul_add, Nat.mul_one]
  have e2 : (c + 1) * a = c * a + a := by rw [Nat.add_mul, Nat.one_mul]
  have e3 : c * (dS + dtau) = c * dS + c * dtau := Nat.mul_add _ _ _
  rw [e1, e2, e3]
  omega

variable {α : Type}

def rot : List α → List α
  | [] => []
  | a :: l => l ++ [a]

/-- tm on starts written as A ++ [x, y, z] ++ [s]  (R180 / r181 auditW181: tm(p)). -/
def tm (A : List α) (x y z s : α) : List α := [z] ++ A ++ [y, x] ++ [s]

/-- the hidden letter (index |A|+1 = n-3) is still y after one tm step. -/
theorem tm_hidden (A : List α) (x y z s : α) :
    (tm A x y z s)[A.length + 1]? = some y := by
  simp [tm]

/-- the word of tm p (first n-1 letters), rotated once, is p's word with x and y swapped. -/
theorem tm_word_swap (A : List α) (x y z : α) :
    rot ([z] ++ A ++ [y, x]) = A ++ [y, x, z] := by
  simp [rot]

/-- frame invariance: deleting the moving letter y from both words gives the same list. -/
theorem tm_frame [DecidableEq α] (A : List α) (x y z : α) (hx : x ≠ y) (hz : z ≠ y) :
    (A ++ [y, x, z]).filter (fun t => t ≠ y) = (A ++ [x, y, z]).filter (fun t => t ≠ y) := by
  simp [List.filter_append, hx, hz]

end ConsTm

#print axioms ConsTm.conservation
#print axioms ConsTm.tm_hidden
#print axioms ConsTm.tm_word_swap
#print axioms ConsTm.tm_frame
