/-
Round I, part 2: kernel-checked validity of the closed n = 8 long trail (period^4): its 104 chains
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

theorem trail_closes : endState trail idp = idp := by decide
theorem trail_class_count : classes.length = 672 := by decide
/-- encode a canonical cyclic word (a list of 8 symbols) as a natural number in base 8 -/
def code : List Nat → Nat
  | [] => 0
  | x :: xs => x + 8 * code xs
def insertSorted (a : Nat) : List Nat → List Nat
  | [] => [a]
  | b :: bs => if a ≤ b then a :: b :: bs else b :: insertSorted a bs
def isort : List Nat → List Nat
  | [] => []
  | a :: as => insertSorted a (isort as)
def strictInc : List Nat → Bool
  | a :: b :: rest => a < b && strictInc (b :: rest)
  | _ => true
def codes : List Nat := classes.map code

/-- the 672 class codes are pairwise distinct (sorted list strictly increasing) -/
theorem trail_classes_distinct : strictInc (isort codes) = true := by decide

/-! From the computation to the formal statement `classes.Nodup`. -/

theorem insertSorted_perm (a : Nat) : ∀ l : List Nat, (insertSorted a l).Perm (a :: l)
  | [] => List.Perm.refl _
  | b :: bs => by
      unfold insertSorted
      split
      · exact List.Perm.refl _
      · exact ((insertSorted_perm a bs).cons b).trans (List.Perm.swap a b bs)

theorem isort_perm : ∀ l : List Nat, (isort l).Perm l
  | [] => List.Perm.refl _
  | a :: as => (insertSorted_perm a (isort as)).trans ((isort_perm as).cons a)

theorem strictInc_ge (b : Nat) (rest : List Nat) (h : strictInc (b :: rest) = true) :
    ∀ x ∈ b :: rest, b ≤ x := by
  induction rest generalizing b with
  | nil => intro x hx; simp at hx; omega
  | cons c rest ih =>
    intro x hx
    simp only [strictInc, Bool.and_eq_true, decide_eq_true_eq] at h
    rcases List.mem_cons.mp hx with hxb | hx'
    · omega
    · have := ih c h.2 x hx'; omega

theorem strictInc_nodup : ∀ l : List Nat, strictInc l = true → l.Nodup
  | [], _ => List.nodup_nil
  | [_], _ => by simp
  | a :: b :: rest, h => by
    simp only [strictInc, Bool.and_eq_true, decide_eq_true_eq] at h
    have hn := strictInc_nodup (b :: rest) h.2
    have hge := strictInc_ge b rest h.2
    refine List.nodup_cons.mpr ⟨?_, hn⟩
    intro hmem
    have := hge a hmem
    omega

theorem nodup_of_map {α β : Type} (f : α → β) : ∀ l : List α, (l.map f).Nodup → l.Nodup
  | [], _ => List.nodup_nil
  | a :: l, h => by
    rw [List.map_cons, List.nodup_cons] at h
    refine List.nodup_cons.mpr ⟨?_, nodup_of_map f l h.2⟩
    intro ha
    exact h.1 (List.mem_map.mpr ⟨a, ha, rfl⟩)

/-- Main formal statement: the closed long trail visits 672 pairwise distinct cyclic classes. -/
theorem trail_classes_nodup : classes.Nodup := by
  have h1 : (isort codes).Nodup := strictInc_nodup _ trail_classes_distinct
  have h2 : codes.Nodup := (isort_perm codes).nodup_iff.mp h1
  exact nodup_of_map code classes h2
