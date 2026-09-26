/-
Round 181 -- arithmetic core of Theorem CS (common-special inequality).  Core Lean 4 only.
Variables (all Nat), c = n - 2 so that n - 1 = c + 1:
  k   rows, ks rows of special s, ko rows of special != s, nu = ORB - ks,
  P   payload blocks (= r - a), m, eta, b Bridge parameters, tau trails,
  gs  total charge of the s-rows (= |Hid_s|), w = omega_s, nnf non-full rows.
Hypotheses are the combinatorial facts proved on paper in the r181 report:
  hk   : k = ks + ko                    (rows split by special)
  hks  : ks + nu = ORB                  (definition of nu; s-rows use distinct s-blocks)
  hM   : ko + P = m + nu                (k - ks + (M - k) = M - ks, M = ORB + m)
  hg   : gs <= w * (ko + P)             (covering of Hid_s, UPL + disjointness + s-partition)
  hnnf : nnf <= gs + ko                 (non-full s-rows have charge >= 1)
  hrun : k <= c * tau + (c+1) * nnf     (C1 at g = 0 on full segments)
  htau : tau <= eta + 1 + b             (Bridge trail budget)
-/
namespace CSCore

theorem cs_core (c ORB m nu ks ko gs w tau eta b nnf k P : Nat)
    (hk : k = ks + ko) (hks : ks + nu = ORB) (hM : ko + P = m + nu)
    (hg : gs ≤ w * (ko + P)) (hnnf : nnf ≤ gs + ko)
    (hrun : k ≤ c * tau + (c + 1) * nnf) (htau : tau ≤ eta + 1 + b) :
    ORB ≤ c * (eta + 1 + b) + (c + (c + 1) * w) * m + ((c + 1) + (c + 1) * w) * nu := by
  have h1 : c * tau ≤ c * (eta + 1 + b) := Nat.mul_le_mul_left c htau
  have h2 : (c + 1) * nnf ≤ (c + 1) * (gs + ko) := Nat.mul_le_mul_left (c + 1) hnnf
  have hg' : gs ≤ w * (m + nu) := by rw [← hM]; exact hg
  have h3 : (c + 1) * gs ≤ (c + 1) * (w * (m + nu)) := Nat.mul_le_mul_left (c + 1) hg'
  have hko : ko ≤ m + nu := by omega
  have h4 : c * ko ≤ c * (m + nu) := Nat.mul_le_mul_left c hko
  have e1 : (c + 1) * (gs + ko) = (c + 1) * gs + c * ko + ko := by
    rw [Nat.mul_add, Nat.add_mul c 1 ko, Nat.one_mul, Nat.add_assoc]
  have e2 : (c + 1) * (w * (m + nu)) = (c + 1) * w * m + (c + 1) * w * nu := by
    rw [← Nat.mul_assoc, Nat.mul_add]
  have e3 : (c + (c + 1) * w) * m + ((c + 1) + (c + 1) * w) * nu
      = c * m + (c + 1) * w * m + (c * nu + nu) + (c + 1) * w * nu := by
    rw [Nat.add_mul c ((c + 1) * w) m, Nat.add_mul (c + 1) ((c + 1) * w) nu,
      Nat.add_mul c 1 nu, Nat.one_mul]
    omega
  have e4 : c * (m + nu) = c * m + c * nu := Nat.mul_add c m nu
  rw [Nat.add_assoc _ ((c + (c + 1) * w) * m), e3]
  rw [e1] at h2
  rw [e2] at h3
  rw [e4] at h4
  omega

/-- Corollary form: with D0 := eta + b + m (<= D since a >= 0),
    ORB <= c + (c+1)(1+w) (D0 + nu). -/
theorem cs_corollary (c ORB m nu eta b w : Nat)
    (h : ORB ≤ c * (eta + 1 + b) + (c + (c + 1) * w) * m + ((c + 1) + (c + 1) * w) * nu) :
    ORB ≤ c + ((c + 1) + (c + 1) * w) * (eta + b + m + nu) := by
  have ha : c * (eta + 1 + b) = c + c * (eta + b) := by
    rw [show eta + 1 + b = 1 + (eta + b) by omega, Nat.mul_add, Nat.mul_one]
  have hb : c * (eta + b) ≤ ((c + 1) + (c + 1) * w) * (eta + b) :=
    Nat.mul_le_mul_right _ (by omega)
  have hc : (c + (c + 1) * w) * m ≤ ((c + 1) + (c + 1) * w) * m :=
    Nat.mul_le_mul_right _ (by omega)
  have hd : ((c + 1) + (c + 1) * w) * (eta + b + m + nu)
      = ((c + 1) + (c + 1) * w) * (eta + b) + ((c + 1) + (c + 1) * w) * m
        + ((c + 1) + (c + 1) * w) * nu := by
    rw [Nat.mul_add, Nat.mul_add]
  rw [hd]
  omega

end CSCore

#print axioms CSCore.cs_core
#print axioms CSCore.cs_corollary
