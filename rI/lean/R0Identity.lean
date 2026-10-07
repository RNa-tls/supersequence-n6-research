/-
Round I: arithmetic core of the r = 0 score-length identity.

An r = 0 route visits the HEX cyclic classes, each as one run of n permutations (n-1 cost-1 edges),
joined by HEX-1 class joins with costs c_i >= 2.  Chains are maximal cost-2 runs of joins, so
  q = 1 + #{i : c_i >= 3}.
The word length is n + (n-1)*HEX + sum c_i.  The lemma below is the purely arithmetic step:
  sum c = 2 * len + #{c >= 3} + sum_{c >= 3} (c - 3)       (all c >= 2)
from which  L = CONST - ORB + q + sum_{c>=4}(c-3)  follows by the definitions of CONST, ORB, HEX.
-/

def sumL : List Nat → Nat
  | [] => 0
  | c :: cs => c + sumL cs

def cnt3 : List Nat → Nat
  | [] => 0
  | c :: cs => (if 3 ≤ c then 1 else 0) + cnt3 cs

def ex3 : List Nat → Nat
  | [] => 0
  | c :: cs => (c - 3) + ex3 cs

def allGe2 : List Nat → Prop
  | [] => True
  | c :: cs => 2 ≤ c ∧ allGe2 cs

theorem join_decomposition (cs : List Nat) (h : allGe2 cs) :
    sumL cs = 2 * cs.length + cnt3 cs + ex3 cs := by
  induction cs with
  | nil => simp [sumL, cnt3, ex3]
  | cons c cs ih =>
    have h1 : 2 ≤ c := h.1
    have ih' := ih h.2
    simp only [sumL, cnt3, ex3, List.length_cons]
    split <;> omega

/-- Full r = 0 length identity in integers, with q = 1 + cnt3 and CONST, ORB, HEX abstract:
    if L = n + (n-1)*HEX + sum c, len = HEX - 1, and CONST = N + HEX + ORB + n - 3 with N = n*HEX,
    then L = CONST - ORB + q + ex3. -/
theorem r0_length_identity (n HEX ORB N L : Nat) (cs : List Nat) (h : allGe2 cs)
    (hlen : cs.length + 1 = HEX) (hN : N = n * HEX) (hn : 1 ≤ n)
    (hL : L = n + (n - 1) * HEX + sumL cs) :
    L + ORB = (N + HEX + ORB + n - 3) + (1 + cnt3 cs) + ex3 cs := by
  have hd := join_decomposition cs h
  subst hN
  have : (n - 1) * HEX + HEX = n * HEX := by
    cases n with
    | zero => omega
    | succ k => simp [Nat.succ_mul]
  omega
