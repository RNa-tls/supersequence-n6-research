import unittest
from itertools import product
from certificate150 import verify_rejection
from audit_feas150 import dual, subset_opt

class FeasTests(unittest.TestCase):
    def test_current_is_not_charged(self):
        self.assertFalse(verify_rejection([1],0,0,0,4))
    def test_untouched_old_orbit(self):
        self.assertTrue(verify_rejection([1,1],1,0,3,4))
        self.assertFalse(verify_rejection([1,1],1,1,0,4))
    def test_q0_is_not_permanently_exempt(self):
        self.assertTrue(verify_rejection([1,31],1,0,0,4))
    def test_dual_vs_allocation(self):
        for us in product(range(5),repeat=4):
            for k in range(6):self.assertEqual(dual(us,k)[0],subset_opt(us,k))
    def test_budget_monotonicity(self):
        for us in product(range(5),repeat=3):
            for k in range(5):self.assertLessEqual(dual(us,k+1)[0],dual(us,k)[0])
    def test_no_invalid_domain_certificate(self):
        for masks,cur,tok,d,lam in [([0],0,0,0,1),([32],0,0,0,1),([1],0,-1,0,1),([1],0,0,-1,1),([1],0,0,0,5)]:
            self.assertFalse(verify_rejection(masks,cur,tok,d,lam))
    def test_phase_pattern_does_not_matter(self):
        for a in range(1,32):
            for b in range(1,32):
                if a.bit_count()==b.bit_count():
                    self.assertEqual(verify_rejection([a,1],1,0,2,4),verify_rejection([b,1],1,0,2,4))

if __name__=='__main__':unittest.main()
