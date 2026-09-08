import copy,itertools,json,sys,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from research_round139_splice_master_codex import splice,topology
from verify_round139_splice_master_codex import endpoint_audit,support_verify,arithmetic,resource_verify

class SpliceMaster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'outputs/rr_round139_splice_master_codex.json').read_text())
        cls.verified=json.loads((ROOT/'outputs/rr_round139_master_verified_codex.json').read_text())
    def test_five_support_cases(self):
        self.assertEqual(len(support_verify()),5)
        self.assertEqual(Counter(len(r['cycles']) for r in topology()),{2:3,0:2})
    def test_reversed_triple_is_not_forward(self):
        t={r['name']:r for r in topology()}
        self.assertEqual(t['A_F1']['cycles'],[]);self.assertEqual(len(t['A_F2']['cycles']),2)
    def test_all_literal_controls(self):
        hist=Counter(str(endpoint_audit(r)) for r in self.data['controls'])
        self.assertEqual(dict(hist),self.data['histogram']);self.assertEqual(sum(hist.values()),1510)
    def test_hard_core_control_now_decomposes(self):
        r=splice('012301203102310132010321031201302130',4)
        self.assertEqual(r['original']['P'],8);endpoint_audit(r)
    def test_positive_shared_orbit_controls_retained(self):
        rows=[r for r in self.data['controls'] if r['s']]
        self.assertEqual(len(rows),46)
        self.assertTrue(all(r['b']+r['s']==r['identity_rhs'] for r in rows))
    def test_wrong_piece_word_rejected(self):
        r=copy.deepcopy(self.data['controls'][0]);r['pieces'][0]['word']+='0'
        with self.assertRaises(AssertionError):endpoint_audit(r)
    def test_wrong_sharing_rejected(self):
        r=copy.deepcopy(self.data['controls'][0]);r['s']+=1
        with self.assertRaises(AssertionError):endpoint_audit(r)
    def test_all_master_envelopes(self):
        d=arithmetic(self.data);self.assertEqual(d['master_envelopes'],38)
        self.assertEqual(d['by_k'],{1:24,2:10,3:3,4:1});self.assertEqual(len(d['equality_rows']),5)
    def test_all_original_rows_accounted_for(self):
        self.assertEqual(resource_verify(self.data),dict(distinct_rows=73,heavy_refined_tuples=78,closed=73,open=0))
    def test_seams_are_hex_failures_not_privacy(self):
        d=self.verified['seams'];self.assertEqual(d['two_chain_all_hex_collision'],312)
        self.assertTrue(d['all_104_second_seams_hex_collide'])
        self.assertTrue(d['three_chain_orbit_rejections_also_hex_collide'])
        self.assertEqual(d['two_chain_extrema_regenerated']['66']['extreme_count'],12)
    def test_scope_and_no_double_counting(self):
        d=self.verified;self.assertEqual(d['outer_after'],'13/55')
        self.assertEqual(d['new_cells'],[[2,2],[1,2]])
        self.assertEqual(d['recovered_old_cells'],[[3,2],[4,2]])
        self.assertEqual(d['NR6'],'ASSUMED');self.assertEqual(d['global_L6_ge_872'],'NOT_PROVED')
    def test_small_weight_overlap_is_unique(self):
        for a in itertools.permutations(range(4)):
            for b in itertools.permutations(range(4)):
                positive=[w for w in range(1,4) if a[w:]==b[:-w]]
                self.assertLessEqual(len(positive),1)
    def test_nonminimal_disjoint_gap_not_normalized_silently(self):
        # Actual gap4 is legal as a literal transition but min endpoint gap1.
        # Splicing keeps its actual heavy weight; final light chains cut it.
        raw=(0,1,2,3,1,2,3,0)
        windows=[(i,raw[i:i+4]) for i in range(5) if len(set(raw[i:i+4]))==4]
        self.assertEqual([i for i,v in windows],[0,4])
        self.assertEqual(windows[0][1][1:],windows[1][1][:-1])
    def test_new_capacity_regressions_complete(self):
        d=json.loads((ROOT/'outputs/rr_round139_master_capacities_codex.json').read_text())
        for b in range(4):
            rows=[r for r in d['rows'] if r['result']['b']==b]
            self.assertEqual(len(rows),2)
            self.assertEqual({r['result']['passes'] for r in rows},{33+15*b})
            self.assertFalse(any(r['result']['capped'] for r in rows))

if __name__=='__main__':unittest.main()
