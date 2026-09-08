import sys,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from research_round135_contraction_codex import resources,geometry,contractions

class Round135(unittest.TestCase):
    def test_resource_table(self):
        rs=resources();self.assertEqual(len(rs),25)
        for r in rs:
            self.assertEqual(r['L'],846+r['S']+r['H'])
            self.assertEqual(r['N'],r['S']-25)
            self.assertEqual(r['f_out'],r['F']+r['e']-r['delta'])
            self.assertLessEqual(r['delta']+r['x']+r['H'],r['F']-1)
    def test_F1_distinct_from_G(self):
        rs=[r for r in resources() if r['F']==1]
        self.assertEqual(len(rs),3)
        self.assertTrue(all(r['x']==r['H']==r['delta']==0 for r in rs))
    def test_heavy_seam_equality_not_coarse_closure(self):
        d=json.loads((ROOT/'outputs/rr_round135_capacity_codex.json').read_text())['capacity']
        self.assertEqual(d['max_bound'],112)
        self.assertEqual([r['left'] for r in d['two_chain_deficit13'] if r['bound']==112],[4,9])
    def test_partial_arc_merge_not_fullpass_assumption(self):
        g=geometry(6);c=g.s(0,1)
        ps=[(0,1)]+[(g.e(c,j),6) for j in range(1,5)]+[(c,2)]
        new,step=next(contractions(g,ps))
        self.assertEqual(new,[(0,3)])
    def test_external_orbit_registration_blocks_removal(self):
        g=geometry(6);c=g.s(0,1)
        # Intentionally incomplete target run; a remaining port exists outside.
        ps=[(0,1)]+[(g.e(c,j),6) for j in [1,3,4]]+[(c,2),(g.e(c,2),6)]
        self.assertEqual(list(contractions(g,ps)),[])
    def test_x_arc_shortening(self):
        g=geometry(6);c=g.s(0,2)
        ps=[(0,2)]+[(g.e(c,j),6) for j in [1,3,4]]+[(c,4)]
        new,step=next(contractions(g,ps))
        self.assertEqual(new,[(0,6)])
        self.assertEqual(step['before']['S']-step['after']['S'],1)
        self.assertEqual(step['before']['D']-step['after']['D'],1)
    def test_provenance_cap_and_residual(self):
        d=json.loads((ROOT/'outputs/rr_round135_verified_codex.json').read_text())
        self.assertTrue(d['verified']);self.assertEqual((d['closed_rows'],d['open_rows']),(18,7))
        self.assertFalse(d['cell_closed']);self.assertEqual(d['outer_closed'],10)
        self.assertEqual(d['independent_seam_counts']['all_label_tests'],17280)
        self.assertEqual(sum(r['status']=='CLOSED' for r in d['ledger']),18)
    def test_paid_short_entry_also_removes_a_joint(self):
        g=geometry(6);c=g.s(0,2)
        ps=[(0,2)]+[(g.e(c,j),6) for j in [2,3,4]]+[(c,4)]
        self.assertIsNotNone(g.replay(ps))
        new,step=next(contractions(g,ps))
        self.assertEqual(new,[(0,6)])
        self.assertEqual(step['internal_weights'],[3,2,2,2])
        self.assertEqual(step['before']['S']-step['after']['S'],1)
        self.assertEqual(step['before']['x'],0)
        self.assertEqual(step['before']['D']-step['after']['D'],1)
    def test_slack_one_counterexamples_not_discarded(self):
        d=json.loads((ROOT/'outputs/rr_round135_controls_codex.json').read_text())
        self.assertTrue(any(r['delta']==1 and not r['steps'] for r in d['n4']['controls']))

if __name__=='__main__':unittest.main()
