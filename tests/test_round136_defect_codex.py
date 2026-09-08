import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from research_round136_defect_codex import seven_rows
from verify_round136_defect_codex import audit_control,measure

class Round136(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/'outputs/rr_round136_defects_codex.json').read_text())
        cls.r=json.loads((ROOT/'outputs/rr_round136_repeat_macros_codex.json').read_text())['result']
    def test_seven_rows_eighteen_free_patterns(self):
        rows=seven_rows();self.assertEqual(len(rows),7)
        self.assertEqual(sum(len(r['patterns']) for r in rows),18)
        self.assertTrue(all(r['delta']==1 and r['S']==25 and r['N']==0 for r in rows))
    def test_delta_is_sum_not_missing_exit_alone(self):
        self.assertTrue(any(r['a']==0 and r['eta']==1 for r in self.d['n4']['rows']))
        self.assertTrue(all(r['a']+r['eta']==1 for r in self.d['n4']['rows']))
    def test_coupled_lock_counterexample_retained(self):
        r=self.d['n4']['counterexamples']['no_merge']
        audit_control(r)
        self.assertEqual(r['a'],1);self.assertEqual(len(r['broken_free_locks']),1)
        self.assertEqual(r['maximal_merges'],0)
    def test_corrupt_repeat_decoration_rejected(self):
        r=copy.deepcopy(self.d['n4']['counterexamples']['paid_exception'])
        r['extra_repeat'][0]['pass_index']+=1
        with self.assertRaises(AssertionError):audit_control(r)
    def test_no_free_ascent_exception_in_complete_controls(self):
        for r in self.d['n4']['rows']:
            self.assertTrue(all(x['kind']=='PAID_REENTRY' for x in r['extra_repeat']))
    def test_same_successor_orbit_defect_absorbed(self):
        aligned=[r for r in self.d['n4']['rows'] if r['residual_model']=='M_ALIGNED']
        self.assertEqual(len(aligned),81)
        self.assertTrue(all(r['maximal_merges']==2 for r in aligned))
    def test_repeat_becomes_M3a_after_inner_contraction(self):
        self.assertEqual(len(self.r['beta_paid_return']),60)
        for r in self.r['beta_paid_return']:
            self.assertEqual(measure(r['original']['word'],6)[0]['x'],0)
            self.assertEqual(r['steps'][0]['after']['x'],1)
            self.assertEqual(r['steps'][-1]['after']['S'],0)
    def test_surviving_local_macros_are_not_Nstar_chains(self):
        local=[r for r in self.d['local_n6']['macros'] if r['merge_count']==0]
        self.assertEqual(len(local),10);self.assertEqual(len(self.r['macros']),20)
        for r in local+self.r['macros']:
            m,ps,_,_=measure(r['original']['word'],6)
            self.assertEqual(sum(l<6 for v,l in ps),2)
            self.assertEqual(m['H'],0)
    def test_tight_capacity_and_scope(self):
        d=json.loads((ROOT/'outputs/rr_round136_verified_codex.json').read_text())
        self.assertTrue(d['verified']);self.assertEqual(d['capacity']['passes'],98)
        self.assertFalse(d['capacity']['capped'])
        self.assertEqual(d['new_whole_rows_closed'],0);self.assertEqual(d['rows_remaining'],7)
        self.assertEqual(d['outer_ledger'],'10/55')
if __name__=='__main__':unittest.main()
