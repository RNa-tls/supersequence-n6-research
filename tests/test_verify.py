import unittest

from src.verify import verify_superpermutation


class TestVerify(unittest.TestCase):
    def test_trivial_valid(self):
        # "123123" is the unique-ish minimal superpermutation for n=3? not
        # necessarily minimal, but must be a *valid* one for this smoke test.
        s = "123121321231"
        report = verify_superpermutation(s, 3, alphabet=("1", "2", "3"))
        self.assertTrue(report["valid"])
        self.assertEqual(report["required"], 6)

    def test_missing_permutation_detected(self):
        s = "12"  # far too short, missing almost everything
        report = verify_superpermutation(s, 3, alphabet=("1", "2", "3"))
        self.assertFalse(report["valid"])
        self.assertEqual(report["covered"], 0)
        self.assertEqual(len(report["missing"]), 6)

    def test_windows_with_repeated_symbols_ignored(self):
        # "111" as a window of length 3 has repeated symbols and must not
        # be counted as covering any permutation.
        s = "111123"
        report = verify_superpermutation(s, 3, alphabet=("1", "2", "3"))
        self.assertLessEqual(report["covered"], 1)


if __name__ == "__main__":
    unittest.main()
