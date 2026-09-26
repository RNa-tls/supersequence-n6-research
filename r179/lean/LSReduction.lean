/-
Round 179 -- arithmetic core of the reduction  Bridge(n) + LS(n; A, c/d)  =>  Delta bound.
Core Lean 4 only.  LS(n; A, c/d) is the (unproved) large-charge capacity hypothesis
  d * M_n(g) <= d * A + c * g   for all g      (slope c/d >= 1, intercept A per trail).
Summed over the tau = eta + 1 + b trails of a Bridge(n) instance with k = ORB + m - r + a rows
and total charge <= u = K m - r (K = n - 1), it gives the hypothesis `hinst` below.
Conclusion: d * ORB <= d * A + E * D  with  D = m + a + b + eta  and  E >= max(d A, c K - d),
i.e.  Delta(n) >= D >= (ORB - A) / (E / d).
-/
namespace LSReduction

theorem ls_core (ORB m a b eta r u A c d K E : Nat)
    (hcd : d ≤ c)                       -- slope c/d >= 1
    (hu : u + r = K * m)                -- u = (n-1) m - r
    (hE1 : d * A ≤ E) (hE2 : c * K ≤ E + d)
    (hinst : d * (ORB + m + a) ≤ d * r + (eta + b + 1) * (d * A) + c * u) :
    d * ORB ≤ d * A + E * (m + a + b + eta) := by
  -- c*u + c*r = c*K*m
  have hcu : c * u + c * r = c * K * m := by
    rw [← Nat.mul_add, hu, Nat.mul_assoc]
  have hcr : d * r ≤ c * r := Nat.mul_le_mul_right r hcd
  have hEb : (eta + b) * (d * A) ≤ (eta + b) * E := Nat.mul_le_mul_left (eta + b) hE1
  have hEm : c * K * m ≤ (E + d) * m := Nat.mul_le_mul_right m hE2
  have hexp : E * (m + a + b + eta) = E * m + E * a + (eta + b) * E := by
    rw [Nat.mul_add, Nat.mul_add, Nat.mul_add, Nat.mul_comm (eta + b) E, Nat.mul_add]
    omega
  have h1 : (eta + b + 1) * (d * A) = (eta + b) * (d * A) + d * A := by
    rw [Nat.add_mul, Nat.one_mul]
  have h2 : (E + d) * m = E * m + d * m := Nat.add_mul E d m
  have h3 : d * (ORB + m + a) = d * ORB + d * m + d * a := by
    rw [Nat.mul_add, Nat.mul_add]
  have ha : 0 ≤ E * a := Nat.zero_le _
  rw [hexp]
  omega

end LSReduction

#print axioms LSReduction.ls_core
