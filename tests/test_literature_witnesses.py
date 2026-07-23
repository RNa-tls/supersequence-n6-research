import unittest

from data.known_witnesses import N4_LENGTH_33
from src.verify import verify_superpermutation


class TestLiteratureWitnesses(unittest.TestCase):
    def test_n4_length_33_witness_is_actually_valid(self):
        report = verify_superpermutation(N4_LENGTH_33, 4, alphabet=("1", "2", "3", "4"))
        self.assertTrue(report["valid"], f"missing: {report['missing']}")
        self.assertEqual(report["length"], 33)


if __name__ == "__main__":
    unittest.main()
