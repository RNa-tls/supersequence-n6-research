"""Independent re-verification of the archived length-872 n=6 superpermutation.

The string in `data/verified_872_witness.txt` comes from the community
archive at github.com/superpermutators/superperm (superpermutations/6/),
which collects 44,120 distinct length-872 examples; the first such string
was found by Robin Houston in 2014 with a TSP solver.

This test does NOT take that provenance on trust.  It checks the string
directly against `src.verify.verify_superpermutation`, the same
ground-truth checker every other claim in this repository is measured by.
Passing it establishes, inside this repository, that a superpermutation of
length 872 EXISTS.

It establishes nothing about minimality.  L(6) >= 872 remains open; the
only proved lower bound here is 867.
"""
import unittest
from pathlib import Path

from src.verify import verify_superpermutation

WITNESS = Path(__file__).resolve().parent.parent / "data" / "verified_872_witness.txt"
ALPHABET = "123456"


def load():
    return WITNESS.read_text(encoding="utf-8").strip()


class Test872Witness(unittest.TestCase):
    def test_length_is_872(self):
        self.assertEqual(len(load()), 872)

    def test_alphabet_is_exactly_123456(self):
        self.assertEqual(sorted(set(load())), list(ALPHABET))

    def test_raw_window_assertions(self):
        """The check in its most elementary form: 720 permutation windows,
        all distinct."""
        s = load()
        windows = [s[i:i + 6] for i in range(len(s) - 5) if len(set(s[i:i + 6])) == 6]
        self.assertEqual(len(windows), 720)
        self.assertEqual(len(set(windows)), 720)

    def test_verified_by_repository_ground_truth_checker(self):
        report = verify_superpermutation(load(), 6, alphabet=ALPHABET)
        self.assertTrue(report["valid"], f"missing permutations: {report['missing']}")
        self.assertEqual(report["length"], 872)
        self.assertEqual(report["required"], 720)
        self.assertEqual(report["covered"], 720)

    def test_beats_the_repositorys_own_greedy_873(self):
        """The archived witness is strictly shorter than this repository's
        own from-scratch construction, which reaches 873."""
        self.assertLess(len(load()), 873)

    def test_structural_fingerprint(self):
        """Weight profile of the walk: consecutive permutation windows differ
        by 1, 2 or 3 new characters.  6 + sum(weights) must be the length."""
        s = load()
        pos = [i for i in range(len(s) - 5) if len(set(s[i:i + 6])) == 6]
        weights = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
        self.assertEqual(len(weights), 719)
        self.assertEqual(6 + sum(weights), 872)
        self.assertEqual(sorted(set(weights)), [1, 2, 3])
        self.assertEqual(weights.count(1), 575)
        self.assertEqual(weights.count(2), 141)
        self.assertEqual(weights.count(3), 3)


if __name__ == "__main__":
    unittest.main()
