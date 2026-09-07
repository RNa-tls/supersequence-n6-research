import sys
import unittest
import json
import copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from research_alpha_gap_codex import Geometry
from verify_locked_detour_contraction_codex import contract_once,contract_two,metrics
from verify_g2_k4_contraction_certificate_codex import check


class ContractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Geometry(6)

    def test_all_splits_endpoints(self):
        for b in range(1,6):
            ps,rec=contract_once(self.g,self.g.half(0,b))
            self.assertEqual(ps,[(0,6)])
            self.assertEqual(rec['before']['D'],rec['after']['D'])

    def test_omitted_locked_phase_rejected(self):
        ps=self.g.half(0,2);del ps[2]
        with self.assertRaises(AssertionError):contract_once(self.g,ps)

    def test_wrong_complement_rejected(self):
        ps=self.g.half(0,2);ps[-1]=(ps[-1][0],3)
        with self.assertRaises(AssertionError):contract_once(self.g,ps)

    def test_nonrepeat_required(self):
        ps=self.g.half(0,2)+[(0,6)]
        with self.assertRaises(AssertionError):contract_once(self.g,ps)

    def test_free_b1_exit_collides(self):
        self.assertIsNone(self.g.replay(self.g.half(0,1)+[(self.g.e(0),6)]))

    def test_fullpass_geometry_matches_capacity(self):
        g=self.g
        for v,w in enumerate(g.words):
            ep=g.words[g.s(v,-1)]
            expected={g.idx[ep[3:]+(ep[2],ep[0],ep[1])],
                      g.idx[ep[3:]+(ep[2],ep[1],ep[0])]}
            actual={t for t,wt in g.joint[g.s(v,-1)] if wt==3 and g.q[t]!=g.q[v]}
            self.assertEqual(expected,actual)
            self.assertEqual([t for t,wt in g.joint[g.s(v,-1)] if wt==2],[g.e(v)])

    def test_twice_contracted_arithmetic(self):
        P,O,S,H=122,28,25,0
        P-=10;O-=2
        self.assertEqual((P,O,5*O-P,S,H),(112,26,18,25,0))
        self.assertEqual(S-(O-1),0) # e' + x'
        self.assertGreater(P,103)

    def test_independent_persisted_words(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'outputs/rr_locked_detour_contraction_codex.json').read_text())
        for r in d['finite_blocks']['rigid_controls']+d['finite_blocks']['alpha_controls']:check(r,6)
        for r in d['n4']['controls']:check(r,4)

    def test_corrupted_persisted_control_rejected(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'outputs/rr_locked_detour_contraction_codex.json').read_text())
        r=copy.deepcopy(d['finite_blocks']['rigid_controls'][0])
        r['contracted']['word']+='012345'
        with self.assertRaises(AssertionError):check(r,6)


if __name__=='__main__':unittest.main()
