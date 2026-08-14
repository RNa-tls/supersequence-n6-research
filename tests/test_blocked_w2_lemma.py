"""Regression tests for the blocked-w2 lemma and the exact Ndef transition taxonomy.

``area_a_prune_reason``'s ``N_exceeded_monotone`` prune is Q1-SAFE and is used by every
search in this repository.  Its justification is that ``Delta Ndef = dS + dF - new_orbit``
is never negative, which needs the *blocked-w2 lemma*: a weight-2 joint can open a fresh
orbit only together with an abandonment.  The repository previously cited that lemma from
prior work and recorded (in ``src/analyze_j_completion.py``) that its own check was "a
bounded empirical check, not a proof".

Round 83 supplied a proof, and these tests pin the two facts it rests on.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "superperm_partial_f1_macro",
    ROOT / "legacy_research" / "work" / "superperm_partial_f1_macro.py",
)
macro = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = macro
_SPEC.loader.exec_module(macro)

exact = macro.exact
core = macro.core
W2 = next(m for m in macro.NONROT_H0 if m.label == "w2:10")


class TestBlockedW2Geometry(unittest.TestCase):
    """The geometric half of the lemma, exhaustively over all 720 words x 6 lengths."""

    def test_w2_target_is_the_blocker_advanced_one_phase(self):
        """t = E(sigma(p')): the w2 target shares the blocker's orbit, one phase on.

        ``abandonment`` is decided by whether ``sigma(p')`` is visited, and ``new_orbit`` by
        whether the target's orbit holds a registered port.  This identity is what ties the
        two together: the blocker is itself a port of the target's orbit.
        """
        checked = 0
        for p in core.ALL_WORDS:
            cursor = p
            for _ in range(6):
                blocker = core.word_after(cursor, core.SIGMA)
                target = core.word_after(cursor, W2.action)
                q_b, f_b = exact.ORBIT_PHASE[blocker]
                q_t, f_t = exact.ORBIT_PHASE[target]
                self.assertEqual(q_b, q_t, "w2 target must share the blocker's E-orbit")
                self.assertEqual((f_t - f_b) % 5, 1, "target must be one phase past the blocker")
                self.assertNotEqual(target, blocker)
                cursor = core.word_after(cursor, core.SIGMA)
                checked += 1
        self.assertEqual(checked, 720 * 6)

    def test_full_rotation_run_blocker_is_the_pass_entry(self):
        """At ell = 5 the blocker is p itself, which is why E^1 preserves the orbit."""
        for p in core.ALL_WORDS:
            cursor = p
            for _ in range(5):
                cursor = core.word_after(cursor, core.SIGMA)
            self.assertEqual(core.word_after(cursor, core.SIGMA), p)
            target = core.word_after(cursor, W2.action)
            self.assertEqual(exact.ORBIT_PHASE[target][0], exact.ORBIT_PHASE[p][0])


class TestNdefTaxonomy(unittest.TestCase):
    """Delta Ndef for every (weight, abandonment, new_orbit) combination the engine admits."""

    def _delta(self, weight, abandonment, new_orbit):
        d_f = int(abandonment)
        d_s = int(weight >= 3)
        return d_s + d_f - int(new_orbit)

    def test_only_the_forbidden_row_is_negative(self):
        negative = [(w, a, n)
                    for w in (2, 3) for a in (False, True) for n in (False, True)
                    if self._delta(w, a, n) < 0]
        self.assertEqual(negative, [(2, False, True)],
                         "the only negative row must be the blocked-w2 fresh-orbit row")

    def test_monotone_prune_is_justified_on_the_realisable_rows(self):
        """With the forbidden row excluded, Delta Ndef >= 0 on every remaining row."""
        for w in (2, 3):
            for a in (False, True):
                for n in (False, True):
                    if (w, a, n) == (2, False, True):
                        continue
                    self.assertGreaterEqual(self._delta(w, a, n), 0)

    def test_engine_agrees_with_the_taxonomy(self):
        """Replay real macro edges and check the recorded deltas against the table."""
        state = exact.initial_state()
        checked = 0
        stack = [state]
        seen = {state.stable_key()}
        while stack and checked < 4000:
            cur = stack.pop()
            for edge in macro.macro_edges(cur):
                joint = edge.joint
                predicted = self._delta(joint.move.weight, joint.abandonment, joint.new_orbit)
                self.assertEqual(edge.state.Ndef - cur.Ndef, predicted)
                self.assertNotEqual(
                    (joint.move.weight, joint.abandonment, joint.new_orbit), (2, False, True),
                    "the blocked-w2 fresh-orbit row must never occur")
                checked += 1
                key = edge.state.stable_key()
                if key not in seen and len(seen) < 400:
                    seen.add(key)
                    stack.append(edge.state)
        self.assertGreater(checked, 1000)


if __name__ == "__main__":
    unittest.main()
