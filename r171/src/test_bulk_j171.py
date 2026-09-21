"""Tiny, isolated bulk-wrapper mutations; never load/replay production DAGs."""
import copy
import gc
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bulk_j171 as W


CELL = (0, 0, 0, 0, 0, 0)
NAME = W.text(CELL)


class BulkSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bulk_mutations_', dir=W.ROOT)
        self.addCleanup(self.cleanup)
        self.folder = Path(self.tmp.name)
        self.trust = patch.dict(W.B.TRUST, {}, clear=True)
        self.trust.start()
        self.addCleanup(self.trust.stop)
        engine = W.G.Engine({}, 1000)
        self.tokens, error = engine.build(CELL, 24)
        self.assertIsNone(error)
        self.assertEqual(engine.nodes, 128)
        self.pred = self.write('pred', [], [], self.tokens)

    def cleanup(self):
        # Streaming verifier generators may be cycle-held until collection.
        gc.collect()
        self.assertEqual(self.folder.resolve().parent, W.ROOT.resolve())
        self.tmp.cleanup()

    def write(self, name, refs, deps, tokens, bound=24):
        path = self.folder / (name + '.txt.gz')
        rel = path.relative_to(W.ROOT).as_posix()
        plain = W.G.write_batch(path, refs, deps, [(CELL, bound, tokens)])
        return (W.sha(rel), W.hashlib.sha256(plain.encode()).hexdigest(), rel)

    def both(self, ref, expected):
        aa = W.A.verify(ref[2], log=lambda *args: None)
        bb = W.B.verify_any(ref[2])
        self.assertEqual(aa['ok'], expected, aa)
        self.assertEqual(bb['ok'], expected, bb)
        if expected:
            self.assertEqual(aa['nodes'], bb['nodes'])
            self.assertEqual(bb['nodes'], bb['hist_checks'])
        return aa, bb

    def dependency(self, cap=24):
        return (CELL, cap, self.pred[1], self.pred[2])

    def test_valid_tiny_dependency_and_dual_replay(self):
        child = self.write('child', [self.pred], [self.dependency()], ['L'])
        dep = W.validate_dag([self.pred, child])
        self.assertEqual(dep[CELL][0], 24)
        self.both(child, True)

    def test_forged_container_and_plain_reference_hashes(self):
        for index in (0, 1):
            with self.subTest(index=index):
                bad = list(self.pred)
                bad[index] = '0' * 64
                child = self.write('forged' + str(index), [bad], [self.dependency()], ['L'])
                with self.assertRaises(AssertionError):
                    W.validate_dag([self.pred, child])
                self.both(child, False)
                with self.assertRaises(AssertionError):
                    W.validate_dag([tuple(bad)])

    def test_unsupported_dependency_cap(self):
        child = self.write('unsupported', [self.pred], [self.dependency(23)], ['L'])
        with self.assertRaises(AssertionError):
            W.validate_dag([self.pred, child])
        self.both(child, False)

    def test_missing_declared_reference(self):
        child = self.write('missing_ref', [], [self.dependency()], ['L'])
        with self.assertRaises(AssertionError):
            W.validate_dag([self.pred, child])
        self.both(child, False)

    def test_missing_predecessor_from_dag(self):
        child = self.write('missing_dag', [self.pred], [self.dependency()], ['L'])
        with self.assertRaises((AssertionError, KeyError)):
            W.validate_dag([child])

    def test_missing_dependency_cannot_use_reference_implicitly(self):
        child = self.write('missing_dep', [self.pred], [], ['L'])
        # Header consistency is not a proof check: A/B must reject this leaf.
        W.validate_dag([self.pred, child])
        self.both(child, False)

    def test_omitted_legal_root_branch(self):
        self.both(self.pred, True)
        tokens = list(self.tokens)
        self.assertEqual(tokens[0], 'N5')
        # Remove the last complete root subtree, updating the claimed arity.
        cursor = 1
        starts = []
        for _ in range(5):
            starts.append(cursor)
            pending = 1
            while pending:
                token = tokens[cursor]
                cursor += 1
                pending += (int(token[1:]) if token.startswith('N') else 0) - 1
        self.assertEqual(cursor, len(tokens))
        omitted = ['N4'] + tokens[1:starts[-1]]
        child = self.write('omitted_branch', [], [], omitted)
        self.both(child, False)

    def record(self):
        aa, bb = self.both(self.pred, True)
        return dict(status='CERTIFIED', histogram_mismatches=0,
                    versions={p: W.sha(p) for p in W.VERSIONS},
                    driver_sha256=W.sha(W.DRIVER), cell=NAME, bound=24,
                    nodes=128, A=aa, B=bb,
                    certificate=dict(path=self.pred[2], sha256=self.pred[0],
                                     plain_sha256=self.pred[1]))

    def test_accepted_metadata_mutations_rejected(self):
        original = self.record()
        mutations = [dict(cell='1|0|0|0|0|0'), dict(bound=23),
                     dict(nodes=127), dict(status='PROVISIONALLY_GENERATED'),
                     dict(histogram_mismatches=1), dict(driver_sha256='0' * 64)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                row = copy.deepcopy(original)
                row.update(mutation)
                with self.assertRaises(AssertionError):
                    W.add_accepted([], [row])
                self.assertNotIn(self.pred[0], W.B.TRUST)

    def test_job_bound_must_equal_frozen_J_before_write(self):
        initial = ({'J': {NAME: 24}}, [], {}, {}, set())
        spec = dict(driver_sha256=W.sha(W.DRIVER), accepted=[], cell=NAME, bound=23)
        with patch.object(W, 'initial', return_value=initial), \
             patch.object(W, 'add_accepted', return_value=([], {})), \
             patch.object(W, 'atomic') as atomic:
            with self.assertRaises(AssertionError):
                W.job(spec)
            atomic.assert_not_called()


if __name__ == '__main__':
    unittest.main()
