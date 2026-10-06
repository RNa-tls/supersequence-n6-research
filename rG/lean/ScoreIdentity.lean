/-
Final attack -- arithmetic of the trail-score identity (core Lean 4).
c = n - 2.  Bridge counts (B4): k + r = ORB + m + a, u + r = (c+1) m, u = G + uout,
D = m + a + b + eta.  With K := sum of trail rows = k and G := total charge, the score
V := K - G (sum of trail scores v_i = rows_i - charge_i) satisfies
    c * D + V = ORB + c * (b + eta) + uout + (c + 1) * a.
-/
namespace ScoreIdentity

theorem score_identity (c ORB m r a k u G uout b eta D : Nat)
    (hk : k + r = ORB + m + a) (hu : u + r = (c + 1) * m) (huo : u = G + uout)
    (hD : D = m + a + b + eta) (hGk : G ≤ k) :
    c * D + (k - G) = ORB + c * (b + eta) + uout + (c + 1) * a := by
  have e1 : (c + 1) * m = c * m + m := by rw [Nat.add_mul, Nat.one_mul]
  have e2 : c * D = c * m + c * a + c * b + c * eta := by
    rw [hD, Nat.mul_add, Nat.mul_add, Nat.mul_add]
  have e3 : c * (b + eta) = c * b + c * eta := Nat.mul_add _ _ _
  have e4 : (c + 1) * a = c * a + a := by rw [Nat.add_mul, Nat.one_mul]
  rw [e2, e3, e4]; rw [e1] at hu
  omega

end ScoreIdentity

#print axioms ScoreIdentity.score_identity
