import unittest

from src.lower_bound import houston_lower_bound, sum_of_factorials_upper_bound


class TestLowerBound(unittest.TestCase):
    def test_matches_known_proven_minimal_lengths_n_le_4(self):
        # For n <= 4 the Houston bound is known to be exactly tight against
        # the proven minimal superpermutation length.
        known_minimal = {1: 1, 2: 3, 3: 9, 4: 33}
        for n, minimal in known_minimal.items():
            self.assertEqual(houston_lower_bound(n), minimal)

    def test_n5_bound_is_below_but_close_to_proven_minimal(self):
        # L(5) = 153 is proven (Chaffin et al. 2014); the formula gives 152,
        # i.e. it is valid but NOT tight starting at n=5.
        self.assertEqual(houston_lower_bound(5), 152)
        self.assertLess(houston_lower_bound(5), 153)

    def test_n6_bound_value(self):
        self.assertEqual(houston_lower_bound(6), 867)

    def test_sum_of_factorials_matches_known_minimal_for_n_le_5(self):
        known_minimal = {1: 1, 2: 3, 3: 9, 4: 33, 5: 153}
        for n, minimal in known_minimal.items():
            self.assertEqual(sum_of_factorials_upper_bound(n), minimal)

    def test_lower_bound_never_exceeds_sum_of_factorials(self):
        for n in range(1, 8):
            self.assertLessEqual(houston_lower_bound(n), sum_of_factorials_upper_bound(n))


if __name__ == "__main__":
    unittest.main()
