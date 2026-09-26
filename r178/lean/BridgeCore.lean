/-
Round 178 -- n-generic arithmetic and combinatorial cores of the coarsening bridge.
Core Lean 4 only (no Mathlib).  These are the parts of the Bridge(n) proof that are
pure counting; the geometric lemmas (complementary rows, visible-class disjointness)
are proved on paper in r178/BRIDGE_REPORT.md and are NOT formalized here.

Parameters: N = n!, HEX = (n-1)!, ORB = (n-2)!, K = n - 1 (so HEX = K * ORB).
-/

namespace BridgeCore

/-- Surgery lemma, existence part (paper Lemma 5.2): along a cycle of arcs that all sit
on one trail, the trail positions cannot strictly decrease at every cyclic step.
`f i` is the trail position of the i-th arc of the cycle, `c` the cycle length. -/
theorem cyclic_not_all_decreasing (c : Nat) (hc : 0 < c) (f : Nat → Nat)
    (hdec : ∀ i, i < c → f ((i + 1) % c) < f i) : False := by
  -- by induction along the cycle: f i + i ≤ f 0 for i < c
  have key : ∀ i, i < c → f i + i ≤ f 0 := by
    intro i
    induction i with
    | zero => intro _; simp
    | succ j ih =>
      intro hj
      have hj' : j < c := Nat.lt_of_succ_lt hj
      have h1 := hdec j hj'
      have hmod : (j + 1) % c = j + 1 := Nat.mod_eq_of_lt hj
      rw [hmod] at h1
      have h2 := ih hj'
      omega
  have hlast : c - 1 < c := Nat.sub_lt hc (by decide)
  have h1 := hdec (c - 1) hlast
  have hwrap : (c - 1 + 1) % c = 0 := by
    have : c - 1 + 1 = c := Nat.sub_add_cancel hc
    rw [this, Nat.mod_self]
  rw [hwrap] at h1
  have h2 := key (c - 1) hlast
  omega

/-- Capped length identity (general n).  With x1 = N - |S|, x2 = |S| - q, x3 = q - p,
|S| = HEX + r, M = ORB + m, k = ORB + m - r + a (with M - k <= r), q = k + b,
p = eta + 1:
  n + x1 + 2 x2 + 3 x3 + 4 (p - 1) = N + HEX + ORB + n - 3 + (m + a + b + eta). -/
theorem capped_length_identity (n N HEX ORB r q p k m a b eta : Nat)
    (hS : HEX + r ≤ N) (hq : q ≤ HEX + r) (hp : p ≤ q) (hp1 : 1 ≤ p)
    (hk : k + r = ORB + m + a) (hq' : q = k + b) (hp' : p = eta + 1) (hn : 3 ≤ n) :
    n + (N - (HEX + r)) + 2 * (HEX + r - q) + 3 * (q - p) + 4 * (p - 1)
      = N + HEX + ORB + n - 3 + (m + a + b + eta) := by
  omega

/-- Hole count: u = (n-1) M - |S| = (n-1) m - r, using HEX = (n-1) * ORB. -/
theorem holes_identity (K ORB HEX m r : Nat) (hHEX : HEX = K * ORB)
    (hfit : HEX + r ≤ K * (ORB + m)) :
    K * (ORB + m) - (HEX + r) = K * m - r := by
  rw [Nat.mul_add] at hfit ⊢
  omega

/-- Trail budget after surgery and deletion:
p + (q - cT) + (cT - k) = eta + 1 + b when k <= cT <= q, q = k + b, p = eta + 1. -/
theorem trail_budget (p q k b eta cT tfinal : Nat) (hkc : k ≤ cT) (hcq : cT ≤ q)
    (hq : q = k + b) (hp : p = eta + 1) (hfinal : tfinal ≤ p + (q - cT) + (cT - k)) :
    tfinal ≤ eta + 1 + b := by
  omega

/-- The cleared-denominator core of the Delta bound.  Write c1 = n - 2 and
c2 = (n-1)(n-3) - 2, assume 2 c1 <= c2 (true for n >= 5), and the instance inequality
(from Bridge(n) + C1, multiplied by 2):
  2 (ORB + m + a) <= 2 r + 2 (eta + 1 + b) c1 + c3 u,  with c3 = n - 3, u + r = (n-1) m,
and c3 >= 2 (n >= 5).  Then 2 (ORB - c1) <= c2 * (m + a + b + eta). -/
theorem delta_core (ORB m a b eta r u c1 c2 c3 K : Nat)
    (hc2 : c2 + 2 = K * c3) (h12 : 2 * c1 ≤ c2) (hc3 : 2 ≤ c3)
    (hu : u + r = K * m)
    (hinst : 2 * (ORB + m + a) ≤ 2 * r + 2 * ((eta + b) * c1 + c1) + c3 * u) :
    2 * ORB ≤ 2 * c1 + c2 * (m + a + b + eta) := by
  -- c3 * u + c3 * r = c3 * K * m = (c2 + 2) * m
  have hcu : c3 * u + c3 * r = (c2 + 2) * m := by
    rw [← Nat.mul_add, hu, hc2, Nat.mul_comm K c3, Nat.mul_assoc]
  -- 2 r <= c3 r
  have hr : 2 * r ≤ c3 * r := Nat.mul_le_mul_right r hc3
  -- 2 c1 (eta + b) <= c2 (eta + b)
  have heb : 2 * ((eta + b) * c1) ≤ c2 * (eta + b) := by
    have := Nat.mul_le_mul_right (eta + b) h12
    rw [Nat.mul_comm (eta + b) c1, ← Nat.mul_assoc]
    exact this
  -- expand c2 * (m + a + b + eta)
  have hexp : c2 * (m + a + b + eta) = c2 * m + c2 * a + c2 * (eta + b) := by
    rw [Nat.mul_add, Nat.mul_add, Nat.mul_add, Nat.mul_add]
    omega
  have hm2 : (c2 + 2) * m = c2 * m + 2 * m := Nat.add_mul c2 2 m
  rw [hexp]
  have ha : 0 ≤ c2 * a := Nat.zero_le _
  omega

/-- 2 c1 <= c2 for n >= 5, i.e. 2 (n-2) <= (n-1)(n-3) - 2, written with n = t + 5. -/
theorem two_c1_le_c2 (t : Nat) : 2 * (t + 3) + 2 ≤ (t + 4) * (t + 2) := by
  have h : (t + 4) * (t + 2) = t * t + 6 * t + 8 := by
    rw [Nat.add_mul, Nat.mul_add, Nat.mul_add]
    omega
  rw [h]
  omega

end BridgeCore

#print axioms BridgeCore.cyclic_not_all_decreasing
#print axioms BridgeCore.capped_length_identity
#print axioms BridgeCore.holes_identity
#print axioms BridgeCore.trail_budget
#print axioms BridgeCore.delta_core
#print axioms BridgeCore.two_c1_le_c2
