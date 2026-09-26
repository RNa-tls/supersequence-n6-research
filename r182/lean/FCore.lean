/-
Round 182 -- arithmetic of Theorem F (forced non-full rows) and of the NF => Delta step.
Core Lean 4 only.  c = n - 2 (so n - 1 = c + 1).  Hypotheses are the Bridge / RUN facts:
  hk   : k + r = ORB + m + a          (Bridge: k = ORB + m - r + a, stated without subtraction)
  hr   : r <= (c+1) * m               (Bridge (0))
  hrun : k <= c * tau + (c+1) * nnf   (Lemma RUN; counting core in RunCount.lean)
  htau : tau <= eta + 1 + b           (Bridge trail budget)
-/
namespace FCore

theorem f_core (c ORB m r a k tau nnf eta b : Nat)
    (hk : k + r = ORB + m + a) (hr : r ≤ (c + 1) * m)
    (hrun : k ≤ c * tau + (c + 1) * nnf) (htau : tau ≤ eta + 1 + b) :
    ORB ≤ (c + 1) * nnf + c * (1 + (m + b + eta)) := by
  have h1 : c * tau ≤ c * (eta + 1 + b) := Nat.mul_le_mul_left c htau
  have e1 : (c + 1) * m = c * m + m := by rw [Nat.add_mul, Nat.one_mul]
  have e2 : c * (eta + 1 + b) = c * eta + c + c * b := by rw [Nat.mul_add, Nat.mul_add, Nat.mul_one]
  have e3 : c * (1 + (m + b + eta)) = c + c * m + c * b + c * eta := by
    rw [Nat.mul_add, Nat.mul_add, Nat.mul_add, Nat.mul_one]; omega
  rw [e1] at hr; rw [e2] at h1; rw [e3]
  omega

/-- NF(theta) with X = m + b + eta, theta a natural number: X >= (ORB - c) / (c + (c+1) theta). -/
theorem nf_delta (c ORB nnf X θ : Nat)
    (hF : ORB ≤ (c + 1) * nnf + c * (1 + X)) (hnf : nnf ≤ θ * X) :
    ORB ≤ c + (c + (c + 1) * θ) * X := by
  have h1 : (c + 1) * nnf ≤ (c + 1) * (θ * X) := Nat.mul_le_mul_left _ hnf
  have e1 : (c + 1) * (θ * X) = (c + 1) * θ * X := (Nat.mul_assoc _ _ _).symm
  have e2 : c * (1 + X) = c + c * X := by rw [Nat.mul_add, Nat.mul_one]
  have e3 : (c + (c + 1) * θ) * X = c * X + (c + 1) * θ * X := Nat.add_mul _ _ _
  rw [e1] at h1; rw [e2] at hF; rw [e3]
  omega

/-- Amortized NF: nnf <= theta X + E  gives  ORB <= c + (c+1) E + (c + (c+1) theta) X. -/
theorem nf_amort (c ORB nnf X θ E : Nat)
    (hF : ORB ≤ (c + 1) * nnf + c * (1 + X)) (hnf : nnf ≤ θ * X + E) :
    ORB ≤ c + (c + 1) * E + (c + (c + 1) * θ) * X := by
  have h1 : (c + 1) * nnf ≤ (c + 1) * (θ * X + E) := Nat.mul_le_mul_left _ hnf
  have e1 : (c + 1) * (θ * X + E) = (c + 1) * θ * X + (c + 1) * E := by
    rw [Nat.mul_add, ← Nat.mul_assoc]
  have e2 : c * (1 + X) = c + c * X := by rw [Nat.mul_add, Nat.mul_one]
  have e3 : (c + (c + 1) * θ) * X = c * X + (c + 1) * θ * X := Nat.add_mul _ _ _
  rw [e1] at h1; rw [e2] at hF; rw [e3]
  omega

end FCore

#print axioms FCore.f_core
#print axioms FCore.nf_delta
#print axioms FCore.nf_amort
