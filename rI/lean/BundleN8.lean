/-
Round I, part 2: kernel-checked BUNDLE property of the closed n = 8 long trail (period^4): its 104 chains
visit 672 pairwise distinct cyclic classes.  Shape validity does not depend on the start (S_8 acts
on the left), so the start is the identity.  `decide` only (kernel evaluation).
-/
set_option maxRecDepth 200000
set_option maxHeartbeats 0

def comp (p q : List Nat) : List Nat := q.map (fun i => p.getD i 0)
def pw (p : List Nat) : Nat → List Nat
  | 0 => [0, 1, 2, 3, 4, 5, 6, 7]
  | k + 1 => comp (pw p k) p
def idp : List Nat := [0, 1, 2, 3, 4, 5, 6, 7]
def F : List Nat := [1, 2, 3, 4, 5, 6, 0, 7]
def Tbac : List Nat := [2, 3, 4, 5, 6, 1, 0, 7]
def Tcba : List Nat := [2, 3, 4, 5, 6, 7, 1, 0]
def letter (x : Nat × Bool) : List Nat := comp (pw F (x.1 - 1)) (if x.2 then Tbac else Tcba)
def period : List (Nat × Bool) :=
  [(5, true), (7, true), (7, true), (7, true),
   (5, true), (7, true), (7, true), (7, true), (7, true),
   (5, false), (6, true), (7, false), (4, true), (7, true), (7, true), (7, true), (7, true),
   (5, true), (7, true), (7, true), (7, true),
   (5, true), (7, true), (7, true), (7, true), (7, true)]
def trail : List (Nat × Bool) := period ++ period ++ period ++ period
/-- rotate a cyclic word so that symbol 0 comes first -/
def canon (p : List Nat) : List Nat := p.drop (p.idxOf 0) ++ p.take (p.idxOf 0)
/-- classes of a chain of length l started at P -/
def chainClasses (P : List Nat) (l : Nat) : List (List Nat) :=
  (List.range l).map (fun j => canon (comp P (pw F j)))
def walk : List (Nat × Bool) → List Nat → List (List Nat)
  | [], _ => []
  | x :: xs, P => chainClasses P x.1 ++ walk xs (comp P (letter x))
def endState : List (Nat × Bool) → List Nat → List Nat
  | [], P => P
  | x :: xs, P => endState xs (comp P (letter x))
def classes : List (List Nat) := walk trail idp


def code : List Nat → Nat
  | [] => 0
  | x :: xs => x + 8 * code xs
def insertSorted (a : Nat) : List Nat → List Nat
  | [] => [a]
  | b :: bs => if a ≤ b then a :: b :: bs else b :: insertSorted a bs
def isort : List Nat → List Nat
  | [] => []
  | a :: as => insertSorted a (isort as)
/-- For the identity start the bundle pair is {3, 7}: delete 3 and 7 and rotate so that symbol 0
    comes first; this is the arrangement C of the remaining six symbols. -/
def arrangement (c : List Nat) : List Nat :=
  let d := c.filter (fun x => x != 3 && x != 7)
  d.drop (d.idxOf 0) ++ d.take (d.idxOf 0)
/-- run lengths of a list -/
def runsAux : List Nat → Nat → Nat → List Nat
  | [], _, k => [k]
  | x :: xs, cur, k => if x == cur then runsAux xs cur (k + 1) else k :: runsAux xs x 1
def runs : List Nat → List Nat
  | [] => []
  | x :: xs => runsAux xs x 1

/-- The 672 classes of the long trail lie in exactly 16 arrangements C (for the pair {3,7}), each
    hit exactly 42 = (n-2)(n-1) = |P({0,7},C)| times.  With `trail_classes_nodup` (TrailN8.lean) and
    |P(C)| = 42 this says: the trail's class set is the disjoint union of 16 whole sets P({3,7},C). -/
theorem bundle_profile : runs (isort (classes.map (fun c => code (arrangement c)))) = List.replicate 16 42 := by
  decide
