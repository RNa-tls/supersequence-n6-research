/-!
# Round O: order–option coupling (n = 8, 6A + 24φ, single-opening words)

Core Lean 4 (4.22), no Mathlib, no `sorry`, no `admit`, no custom axioms.
The searches (LP column generation, QTSP MIP, window MIPs) are NOT formalised.  Proved here:

1. `J_identity_SO`     : with P = 30 pieces, J = 48 + (P − 1) + c0 + Σe = 77 + cost  (cost = c0 + Σe).
2. `family_from_minF`  : (every word has cost ≥ 23) ⇒ (every word has J ≥ 100).
3. `triple_split_bound`: if every link satisfies e_i ≥ R_i + L_{i+1}, the last right charge is 0 and
                         U_i ≤ L_i + R_i for every position, then L_1 + Σ e ≥ Σ U.  This is the
                         soundness of the triple-potential certificate F(π) ≥ Σ_i U(π_{i−1}, π_i, π_{i+1})
                         (L_1 = start cost [cut = 2]).
4. `hull_cut_useless`  : an inequality a·z ≥ β valid for every order's incidence vector z^k is valid
                         for every nonnegative combination Σ λ_k z^k (with weights summing to D):
                         order cuts cannot separate a point of the order hull (here the 16.111 LP
                         optimum, which was shown to lie in the hull).
-/

namespace OrderCoupling

def lsum : List Int → Int
  | [] => 0
  | a :: l => a + lsum l

/-! ## 1–2. the constant 77 -/

theorem J_identity_SO (J c0 sumE : Int) (h : J = 48 + (30 - 1) + c0 + sumE) : J = 77 + (c0 + sumE) := by
  omega

theorem family_from_minF (J c0 sumE : Int) (h : J = 48 + (30 - 1) + c0 + sumE) (hmin : 23 ≤ c0 + sumE) :
    100 ≤ J := by
  omega

/-! ## 3. link splitting (triple potential soundness)

Positions are given as a list of records (L_i, R_i, U_i) and the list of link excesses e_i between
consecutive positions.  `splitOK` states e_i ≥ R_i + L_{i+1}; the last position has R = 0. -/

structure Pos where
  L : Int
  R : Int
  U : Int

/-- the link conditions along the list, and R = 0 at the last position -/
def chainOK : List Pos → List Int → Prop
  | [], [] => True
  | [p], [] => p.R = 0
  | p :: q :: rest, e :: es => (p.R + q.L ≤ e) ∧ chainOK (q :: rest) es
  | _, _ => False

def sumU : List Pos → Int
  | [] => 0
  | p :: l => p.U + sumU l

def sumLR : List Pos → Int
  | [] => 0
  | p :: l => p.L + p.R + sumLR l

/-- Σ e ≥ Σ (L_i + R_i) − L_1 under the chain conditions -/
theorem chain_links (ps : List Pos) (es : List Int) (h : chainOK ps es) :
    sumLR ps ≤ (match ps with | [] => 0 | p :: _ => p.L) + lsum es := by
  induction ps generalizing es with
  | nil =>
    cases es with
    | nil => simp [sumLR, lsum]
    | cons e es => simp [chainOK] at h
  | cons p rest ih =>
    cases rest with
    | nil =>
      cases es with
      | nil => simp [chainOK] at h; simp [sumLR, lsum, h]
      | cons e es => simp [chainOK] at h
    | cons q rest' =>
      cases es with
      | nil => simp [chainOK] at h
      | cons e es =>
        simp only [chainOK] at h
        have h2 := ih es h.2
        simp only [sumLR, lsum] at h2 ⊢
        omega

theorem sumU_le (ps : List Pos) (h : ∀ p ∈ ps, p.U ≤ p.L + p.R) : sumU ps ≤ sumLR ps := by
  induction ps with
  | nil => simp [sumU, sumLR]
  | cons p l ih =>
    simp only [sumU, sumLR]
    have h1 := h p (List.mem_cons_self ..)
    have h2 := ih (fun x hx => h x (List.mem_cons_of_mem _ hx))
    omega

/-- the certificate inequality: start cost + Σ e ≥ Σ U -/
theorem triple_split_bound (p : Pos) (rest : List Pos) (es : List Int)
    (hc : chainOK (p :: rest) es) (hU : ∀ x ∈ p :: rest, x.U ≤ x.L + x.R) :
    sumU (p :: rest) ≤ p.L + lsum es := by
  have h1 := sumU_le (p :: rest) hU
  have h2 := chain_links (p :: rest) es hc
  simp only at h2
  omega

/-! ## 4. order cuts cannot separate points of the order hull -/

def dot : List Int → List Int → Int
  | a :: as, b :: bs => a * b + dot as bs
  | _, _ => 0

theorem hull_cut_useless (lams vals : List Int) (β : Int)
    (hlen : lams.length = vals.length)
    (hlam : ∀ l ∈ lams, 0 ≤ l) (hval : ∀ v ∈ vals, β ≤ v) :
    β * lsum lams ≤ dot lams vals := by
  induction lams generalizing vals with
  | nil => simp [lsum, dot]
  | cons l ls ih =>
    cases vals with
    | nil => simp at hlen
    | cons v vs =>
      simp only [List.length_cons, Nat.add_right_cancel_iff] at hlen
      have hl : 0 ≤ l := hlam l (List.mem_cons_self ..)
      have hv : β ≤ v := hval v (List.mem_cons_self ..)
      have hrec := ih vs hlen (fun x hx => hlam x (List.mem_cons_of_mem _ hx)) (fun x hx => hval x (List.mem_cons_of_mem _ hx))
      have hm : β * l ≤ v * l := Int.mul_le_mul_of_nonneg_right hv hl
      simp only [lsum, dot]
      rw [Int.mul_add, Int.mul_comm l v]
      omega

end OrderCoupling
