/-
Round I, part 2: kernel-checked period facts for the n = 8 long trail (46188 / 46187 bundles).
Permutations of positions are lists in one-line notation; (comp p q)[i] = p[q[i]] (right action
s -> s o pi).  Everything is decided by kernel evaluation (`decide`), no native code, no axioms.
-/

def comp (p q : List Nat) : List Nat := q.map (fun i => p.getD i 0)

def pw (p : List Nat) : Nat → List Nat
  | 0 => [0, 1, 2, 3, 4, 5, 6, 7]
  | k + 1 => comp (pw p k) p

def idp : List Nat := [0, 1, 2, 3, 4, 5, 6, 7]
/-- F: rotate positions 0..6 (position 7 = special, fixed). -/
def F : List Nat := [1, 2, 3, 4, 5, 6, 0, 7]
/-- phi: rotate positions 0..5. -/
def phi : List Nat := [1, 2, 3, 4, 5, 0, 6, 7]
/-- kappa = F^-1 o T_cba: the 8-cycle (0 1 2 3 4 5 7 6). -/
def kap : List Nat := [1, 2, 3, 4, 5, 7, 0, 6]
def Tbac : List Nat := [2, 3, 4, 5, 6, 1, 0, 7]
def Tcba : List Nat := [2, 3, 4, 5, 6, 7, 1, 0]

/-- the cost-3 step after a chain of length l: F^(l-1) o T_sigma -/
def stepB (l : Nat) : List Nat := comp (pw F (l - 1)) Tbac
def stepC (l : Nat) : List Nat := comp (pw F (l - 1)) Tcba

theorem phi_eq : comp (pw F 6) Tbac = phi := by decide
theorem kap_eq : comp (pw F 6) Tcba = kap := by decide
theorem stepB_eq : ∀ l ∈ [1, 2, 3, 4, 5, 6, 7], stepB l = comp (pw F l) phi := by decide
theorem stepC_eq : ∀ l ∈ [1, 2, 3, 4, 5, 6, 7], stepC l = comp (pw F l) kap := by decide

/-- the 26-letter period S3 S4 X4 S3 S4 of the long trail: (length, true = bac / false = cba) -/
def period : List (Nat × Bool) :=
  [(5, true), (7, true), (7, true), (7, true),
   (5, true), (7, true), (7, true), (7, true), (7, true),
   (5, false), (6, true), (7, false), (4, true), (7, true), (7, true), (7, true), (7, true),
   (5, true), (7, true), (7, true), (7, true),
   (5, true), (7, true), (7, true), (7, true), (7, true)]

def letter (x : Nat × Bool) : List Nat := if x.2 then stepB x.1 else stepC x.1

def Pi : List Nat := period.foldl (fun acc x => comp acc (letter x)) idp

theorem period_length : period.length = 26 := by decide
theorem Pi_value : Pi = [2, 5, 6, 3, 0, 1, 4, 7] := by decide
theorem Pi_order_four : pw Pi 4 = idp ∧ pw Pi 2 ≠ idp ∧ Pi ≠ idp := by decide
/-- total chain length per period (classes visited per period) -/
theorem classes_per_period : (period.map Prod.fst).foldl (· + ·) 0 = 168 := by decide
