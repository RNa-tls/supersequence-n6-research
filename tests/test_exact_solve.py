import unittest

from src.exact_solve import minimal_superpermutation_length


class TestExactSolve(unittest.TestCase):
    def test_n2(self):
        length, _, exhausted = minimal_superpermutation_length(2)
        self.assertTrue(exhausted)
        self.assertEqual(length, 3)

    def test_n3(self):
        length, _, exhausted = minimal_superpermutation_length(3)
        self.assertTrue(exhausted)
        self.assertEqual(length, 9)

    def test_n4(self):
        length, _, exhausted = minimal_superpermutation_length(4, node_budget=3_000_000)
        self.assertTrue(exhausted)
        self.assertEqual(length, 33)


if __name__ == "__main__":
    unittest.main()
