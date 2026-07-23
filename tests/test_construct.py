import unittest

from src.construct import greedy_construct
from src.verify import verify_superpermutation
from src.lower_bound import houston_lower_bound


class TestGreedyConstruct(unittest.TestCase):
    def test_valid_for_small_n(self):
        for n in range(1, 6):
            s = greedy_construct(n)
            report = verify_superpermutation(s, n)
            self.assertTrue(report["valid"], f"greedy_construct({n}) not valid: missing {report['missing']}")

    def test_length_never_below_proven_lower_bound(self):
        for n in range(1, 6):
            s = greedy_construct(n)
            self.assertGreaterEqual(len(s), houston_lower_bound(n))


if __name__ == "__main__":
    unittest.main()
