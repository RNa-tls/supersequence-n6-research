/-
Round R -- Lean 4 (core only, no Mathlib) formalisation of the combinatorial part of the bracket-tree reduction.

Options carry a trail label `tr`.  For the 6A+24phi family the option-level excess `e` satisfies the two detour
lemmas (checked by machine on all 90,599,040 ordered option pairs of distinct trails, rR/csrc/bmat.c and
rR/csrc/l2check.c, two independent loop orders):
  L1 : tr x, tr u, tr y pairwise distinct            ->  e x y ≤ 1 + e x u + e u y
  L2 : tr x = tr u2, tr u1 = tr y, tr x ≠ tr y        ->  e x y ≤ 2 + e x u1 + e u1 u2 + e u2 y
They are hypotheses here.  Main results:
  * `detour`            : along every path x, x_1, ..., x_n whose consecutive trails differ and whose end trails differ,
                          e x x_n ≤ (n - 1) + sum of e over the path  (removing the n - 1 inner cuts never pays);
  * `detour_start` / `detour_end` : the same for a run of removed cuts at the start / end of the word;
  * `bracket_cost`      : G = c + [cut first = 2] + sum e  for a bracket tree (bookkeeping identity);
  * `potential_bound`   : a feasible potential gives a lower bound for every path (sections 17-18);
  * `length_bound`      : G ≥ 21 implies length ≥ 46183 (length = 46162 + G).
-/

section Detour
variable {α : Type} (tr : α → Nat) (e : α → α → Int)

/-- sum of `e` over the consecutive pairs of the list `x :: l` -/
def pcost (x : α) : List α → Int
  | [] => 0
  | y :: l => e x y + pcost y l

/-- consecutive trails are distinct along `x :: l` -/
def cdist (x : α) : List α → Prop
  | [] => True
  | y :: l => tr x ≠ tr y ∧ cdist y l

/-- last element of `x :: l` -/
def lastOf (x : α) : List α → α
  | [] => x
  | y :: l => lastOf y l

theorem lastOf_cons2 (x y z : α) (l : List α) : lastOf x (y :: z :: l) = lastOf z l := rfl

theorem detour
    (hL1 : ∀ x u y, tr x ≠ tr u → tr u ≠ tr y → tr x ≠ tr y → e x y ≤ 1 + e x u + e u y)
    (hL2 : ∀ x u1 u2 y, tr x = tr u2 → tr u1 = tr y → tr x ≠ tr y → e x y ≤ 2 + e x u1 + e u1 u2 + e u2 y) :
    ∀ (x : α) (l : List α), l ≠ [] → cdist tr x l → tr x ≠ tr (lastOf x l) →
      e x (lastOf x l) ≤ (l.length : Int) - 1 + pcost e x l
  | x, [], h, _, _ => absurd rfl h
  | x, [y], _, _, _ => by simp [lastOf, pcost]
  | x, y :: z :: l, _, hc, hend => by
    have hxy : tr x ≠ tr y := hc.1
    have hyz : tr y ≠ tr z := hc.2.1
    have hzl : cdist tr z l := hc.2.2
    by_cases hxz : tr x = tr z
    · -- the first inner cut cannot be removed alone; look one cut further
      cases l with
      | nil => exact absurd hxz (by simpa [lastOf] using hend)
      | cons w l' =>
        have hzw : tr z ≠ tr w := hzl.1
        have hwl : cdist tr w l' := hzl.2
        by_cases hyw : tr y = tr w
        · -- alternating x y z w with tr x = tr z, tr y = tr w : remove y and z by L2
          have hxw : tr x ≠ tr w := by rw [← hyw]; exact hxy
          have h2 := hL2 x y z w hxz hyw hxw
          have ih := detour hL1 hL2 x (w :: l') (by simp) ⟨hxw, hwl⟩ (by simpa [lastOf] using hend)
          simp only [pcost, lastOf, List.length_cons] at ih ⊢
          have : ((l'.length + 1 + 1 + 1 : Nat) : Int) = (l'.length : Int) + 3 := by omega
          rw [this]
          have : ((l'.length + 1 : Nat) : Int) = (l'.length : Int) + 1 := by omega
          rw [this] at ih
          omega
        · -- remove z by L1 on (y, z, w)
          have h1 := hL1 y z w hyz hzw hyw
          have ih := detour hL1 hL2 x (y :: w :: l') (by simp) ⟨hxy, hyw, hwl⟩ (by simpa [lastOf] using hend)
          simp only [pcost, lastOf, List.length_cons] at ih ⊢
          have : ((l'.length + 1 + 1 + 1 : Nat) : Int) = (l'.length : Int) + 3 := by omega
          rw [this]
          have : ((l'.length + 1 + 1 : Nat) : Int) = (l'.length : Int) + 2 := by omega
          rw [this] at ih
          omega
    · -- remove y by L1 on (x, y, z)
      have h1 := hL1 x y z hxy hyz hxz
      have ih := detour hL1 hL2 x (z :: l) (by simp) ⟨hxz, hzl⟩ (by simpa [lastOf] using hend)
      simp only [pcost, lastOf, List.length_cons] at ih ⊢
      have : ((l.length + 1 + 1 : Nat) : Int) = (l.length : Int) + 2 := by omega
      rw [this]
      have : ((l.length + 1 : Nat) : Int) = (l.length : Int) + 1 := by omega
      rw [this] at ih
      omega
termination_by _ l => l.length

/-- removing a run of cuts at the start of the word: the new first piece pays [cut = 2] (a value in {0, 1}) instead of
    1 + [cut = 2] + e for every removed cut -/
theorem detour_start (c2 : α → Int) (hc2 : ∀ x, 0 ≤ c2 x ∧ c2 x ≤ 1) (he : ∀ x y, tr x ≠ tr y → 0 ≤ e x y) :
    ∀ (u y : α), tr u ≠ tr y → c2 y ≤ 1 + c2 u + e u y := by
  intro u y h
  have := hc2 u; have := hc2 y; have := he u y h
  omega

/-- removing the last cut of the word never pays: 0 ≤ 1 + e x u -/
theorem detour_end (he : ∀ x y, tr x ≠ tr y → 0 ≤ e x y) : ∀ (x u : α), tr x ≠ tr u → (0 : Int) ≤ 1 + e x u := by
  intro x u h
  have := he x u h
  omega

end Detour

section Bookkeeping

/-- Bracket tree with `c` cycles: cover = path P plus c cycles, 30 + c cuts; the identity
    G = (P - 30) + [cut first = 2] + sum_{cover edges} e  becomes  G = c + c1 + S. -/
theorem bracket_cost (P c c1 S G : Int) (hP : P = 30 + c) (hG : G = (P - 30) + c1 + S) : G = c + c1 + S := by
  omega

/-- length = 46162 + G for the family; a lower bound G ≥ 21 gives length ≥ 46183 -/
theorem length_bound (L G : Int) (hL : L = 46162 + G) (h : 21 ≤ G) : 46183 ≤ L := by
  omega

/-- single split (c = 1) at G = 21 is the record 46183; any family member with G ≤ 20 would have length ≤ 46182 -/
theorem record_threshold (L G : Int) (hL : L = 46162 + G) : L ≤ 46182 ↔ G ≤ 20 := by
  omega

end Bookkeeping

section Potential
variable {β : Type} (w : β → β → Int) (p : β → Int)

def wcost (x : β) : List β → Int
  | [] => 0
  | y :: l => w x y + wcost y l

def lastB (x : β) : List β → β
  | [] => x
  | y :: l => lastB y l

/-- sections 17-18: if every edge satisfies w u v + p u - p v ≥ 0 (a feasible integer potential), then every path
    costs at least p(end) - p(start); in particular there is no negative cycle, and the zero-reduced-cost edges
    are exactly those that can lie on a tight path. -/
theorem potential_bound (hp : ∀ u v, 0 ≤ w u v + p u - p v) :
    ∀ (x : β) (l : List β), p (lastB x l) - p x ≤ wcost w x l
  | x, [] => by simp [lastB, wcost]
  | x, y :: l => by
    have ih := potential_bound hp y l
    have h := hp x y
    simp only [lastB, wcost] at ih ⊢
    omega

/-- a closed walk (end = start) has nonnegative cost under a feasible potential -/
theorem no_negative_cycle (hp : ∀ u v, 0 ≤ w u v + p u - p v) (x : β) (l : List β) (hc : lastB x l = x) :
    0 ≤ wcost w x l := by
  have := potential_bound w p hp x l
  rw [hc] at this
  omega

end Potential

#print axioms detour
#print axioms detour_start
#print axioms detour_end
#print axioms bracket_cost
#print axioms length_bound
#print axioms record_threshold
#print axioms potential_bound
#print axioms no_negative_cycle
