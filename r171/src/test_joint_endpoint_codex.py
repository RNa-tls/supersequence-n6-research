import copy, unittest
from joint_endpoint_codex import load, minimal_masks

class EndpointRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=load('r171/certs/joint_endpoint_codex_171.json')
        cls.d=load('r171/certs/joint_dossier_codex_171.json')

    def test_complete_universe(self):
        self.assertEqual([r['mask'] for r in self.e['assignments']],list(range(8192)))
        self.assertEqual(self.e['feasible'],1)
        self.assertTrue(all(r['equality']==['EQUALITY']*2 for r in self.e['assignments']))

    def test_real_pair_defeats_singleton_probe(self):
        p=self.d['diagnostic_pair_regression']
        self.assertTrue(all(not x['open_rows'] for x in p[:3]))
        self.assertTrue(p[3]['open_rows'])

    def test_real_three_way_defeats_pair_probe_on_its_rows(self):
        triples=[e for e in self.e['minimal_row_hyperedges'] if len(e['cells'])==3]
        self.assertEqual(len(triples),2)
        for e in triples:
            mask,row=e['mask'],e['row_index']
            self.assertIn(row,self.e['assignments'][mask]['open_rows'])
            for sub in range(mask):
                if sub&mask==sub:self.assertNotIn(row,self.e['assignments'][sub]['open_rows'])

    def test_synthetic_three_way(self):
        self.assertEqual(minimal_masks([7]),[7])

    def test_dont_invent_missing_active_coordinate(self):
        self.assertNotIn('1|5|10|0|0|0',self.e['active'])
        self.assertEqual(self.e['I']['1|5|10|0|0|0'],self.e['J']['1|5|10|0|0|0'])
        self.assertFalse(self.e['known_pair_diagnosis']['expected_pair_can_appear'])

    def test_no_promotion_of_weak_bound(self):
        weak=[c for c in self.d['certificates'] if c['cell']=='1|7|8|0|0|0' and c['cap']==123]
        self.assertEqual(weak[0]['joint_usability'],'VALID_BUT_NOT_JOINTLY_SUFFICIENT')
        self.assertEqual(self.d['jointly_usable'],5)
        self.assertEqual(self.d['remaining_joint_safe_bounds'],30)
        self.assertFalse(self.d['production_started'])

    def test_downward_box_not_global_quotient(self):
        self.assertEqual(self.d['status'],'JOINT_SAFE_VECTOR_PARTIAL')
        self.assertEqual(len(self.d['box_frontier']['pareto_vectors']),1)
        self.assertIn('Global Pareto',self.d['box_frontier']['NOT_claimed'])

if __name__=='__main__':unittest.main()
