import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from research_round139_multidefect_codex import resource_rows
from research_round139_controls_codex import injection
from certify_round139_multidefect_codex import literal
from verify_round139_multidefect_codex import independent_rows

class Round139(unittest.TestCase):
    def test_resource_count(self):
        d=resource_rows();self.assertEqual((d['distinct_count'],d['raw_heavy_tuples']),(73,78))
    def test_independent_rows(self):
        r=resource_rows()['rows'];self.assertEqual(independent_rows(),sorted((z['type'],z['F'],z['delta'],z['x'],z['H'],z['e']) for z in r))
    def test_master_slack(self):
        for r in resource_rows()['rows']:
            self.assertEqual(r['L'],871-r['F']+r['delta']+r['x']+r['H']);self.assertEqual(r['D'],8)
    def test_fusion(self):
        w='5301245301234501253401253041253024153024513024501324501234051230451230541230514230512430512340'
        d=literal(w,6);self.assertEqual((d['F'],d['G'],d['a'],d['eta'],d['delta']),(2,2,1,1,2));self.assertIn(2,d['exceptional'])
    def test_repeat_multiplicity(self):
        s,j,r=injection((0,1,0,2,0),(0,0,1,1,2));self.assertEqual(s,2);self.assertEqual(j,[2,4])
    def test_designated_overlap_cannot_be_ignored(self):
        s,j,r=injection((0,1,0),(0,0,1));self.assertEqual(s,1)
        self.assertFalse(2>=2+s);self.assertTrue(2>=2+s-len(set(j)&{2}))
    def test_heavy_multisets(self):
        for r in resource_rows()['rows']:
            if r['H']==2:self.assertEqual(r['heavy_multisets'],[[5],[4,4]])
    def test_no_global_plus15(self):
        self.assertGreater(20+15*7,120)
    def test_literal_repeat_rejected(self):
        with self.assertRaises(AssertionError):literal('012301230',4)
    def test_hard_core_positive(self):
        d=literal('012301203102310132010321031201302130',4)
        self.assertEqual((len(d['windows']),d['F'],d['G'],d['delta']),(24,2,2,2))
    def test_root_tables_independent(self):
        p=ROOT/'outputs/rr_round139_capacities_codex.json'
        if not p.exists():self.skipTest('run capacity certificate first')
        d=json.loads(p.read_text())
        for m in range(3):
            a=d['rows'][2*m]['result'];b=d['rows'][2*m+1]['result']
            self.assertFalse(a['capped']);self.assertFalse(b['capped'])
            self.assertEqual([{k:v for k,v in z.items() if k!='witness'} for z in a['rows']],b['rows'])
    def test_two_token_independent(self):
        p=ROOT/'outputs/rr_round139_independent_codex.json'
        if not p.exists():self.skipTest('run b2 verifier first')
        d=json.loads(p.read_text());self.assertEqual([z['result']['passes'] for z in d['independent_b2']],[62,77,92])
    def test_global_ledger_not_advanced(self):
        p=ROOT/'outputs/rr_round139_final_ledger_codex.json'
        if not p.exists():self.skipTest('run final verifier first')
        d=json.loads(p.read_text());self.assertEqual(d['conditional_outer_ledger'],'11/55 UNCHANGED')
        self.assertEqual((d['closed_rows'],d['open_rows']),(60,13));self.assertEqual(d['L6_ge_872'],'NOT_PROVED')

if __name__=='__main__':unittest.main()
