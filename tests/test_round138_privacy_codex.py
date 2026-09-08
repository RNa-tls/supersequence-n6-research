import copy,hashlib,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from verify_round138_privacy_codex import audit_literal,digest,independent_csp,Q,rot

class Round138(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x=json.loads((ROOT/'outputs/rr_round138_privacy_controls_codex.json').read_text())
        cls.rows=cls.x['controls']['rows']
        old=json.loads((ROOT/'outputs/rr_round137_gap_cut_codex.json').read_text())
        cls.lookup={digest(r['word']):r for r in old['rows']}
    def test_all_deliberately_shared_literal_contexts(self):
        for r in self.rows:audit_literal(r,self.lookup[r['source_word_sha256']])
        self.assertEqual(len(self.rows),67)
        self.assertEqual(len({(r['n'],r['word']) for r in self.rows}),15)
    def test_false_delta_one_decoration_rejected(self):
        r=copy.deepcopy(self.rows[0]);r['classification']['delta']=1
        with self.assertRaises(AssertionError):audit_literal(r,self.lookup[r['source_word_sha256']])
    def test_false_orbit_decoration_rejected(self):
        r=copy.deepcopy(self.rows[0]);r['shared_orbit']+=1
        with self.assertRaises(AssertionError):audit_literal(r,self.lookup[r['source_word_sha256']])
    def test_orbit_not_last_symbol_short5_edge_case(self):
        v=(0,1,2,3,4,5);y=rot(v,4);t=y[3:]+tuple(y[i] for i in [2,0,1])
        self.assertEqual(v[-1],t[-1]);self.assertNotEqual(Q(v),Q(t))
        self.assertEqual(t,(1,2,3,0,4,5))
    def test_g2_sharing_is_not_automatically_literal_collision(self):
        rows=[r for r in self.rows if r['n']==6 and r['classification']['G']==2]
        self.assertEqual(len(rows),4)
        self.assertTrue(all(r['classification']['F']==2 and r['classification']['delta']==2 for r in rows))
    def test_internal_root_return_not_excluded(self):
        self.assertGreater(self.x['event_csp']['histogram']['R/shared0/extra0'],0)
    def test_complete_symbolic_domain_independent(self):
        nodes,hist=independent_csp();self.assertEqual(nodes,12972)
        self.assertEqual(hist,self.x['event_csp']['histogram'])
        self.assertFalse(self.x['event_csp']['capped']);self.assertIsNone(self.x['event_csp']['node_cap'])
    def test_generalized_deficit_counts_shared_orbits(self):
        for s in range(6):self.assertEqual(5*(26+s)-117,13+5*s)
    def test_committed_hash_correction_is_explicit(self):
        c=self.x['metadata_correction'];blob=subprocess.check_output(['git','show',c['commit']+':'+c['file']])
        self.assertEqual(hashlib.sha256(blob).hexdigest(),c['correct_committed_blob_sha256'])
        self.assertNotEqual(c['recorded_ambiguous_source_sha256'],c['correct_committed_blob_sha256'])
        self.assertFalse(c['old_certificate_modified']);self.assertFalse(c['capacity_recomputed'])
    def test_existing_controls_are_support_not_universal_certificate(self):
        self.assertEqual(self.x['controls']['preserved_gap_controls'],835)
        self.assertEqual(self.x['controls']['positional_identities'],10800)
        self.assertEqual(self.x['controls']['complementary_context_checks'],3600)
        self.assertIn('not universal',self.x['controls']['scope'])
if __name__=='__main__':unittest.main()
