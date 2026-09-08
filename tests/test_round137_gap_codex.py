import copy,json,sys,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from verify_round137_gap_capacity_codex import audit_gap,literal_capacity_witness,root_return

class Round137(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads((ROOT/'outputs/rr_round137_gap_cut_codex.json').read_text())
        cls.c=json.loads((ROOT/'outputs/rr_round137_root_return_capacity_codex.json').read_text())
    def test_all_preserved_gap_certificates(self):
        self.assertEqual(len(self.g['rows']),835)
        for r in self.g['rows']:audit_gap(r)
    def test_wrong_cut_rejected(self):
        r=copy.deepcopy(self.g['rows'][0]);r['certificate']['cut'][1]-=1
        with self.assertRaises(AssertionError):audit_gap(r)
    def test_corrupt_deficit_rejected(self):
        r=copy.deepcopy(self.g['rows'][0]);r['before']['D']+=1
        with self.assertRaises(AssertionError):audit_gap(r)
    def test_root_return_extrema_replay(self):
        for r in self.c['result']['rows']:literal_capacity_witness(r)
    def test_duplicate_hex_witness_rejected(self):
        r=copy.deepcopy(self.c['result']['rows'][0]);r['witness'][1]=r['witness'][0]
        with self.assertRaises(AssertionError):literal_capacity_witness(r)
    def test_disjoint_orbits_not_disjoint_hexes(self):
        # One shared hexagon at the cut, possibly removed by outer contraction.
        audit_gap(self.g['rows'][0])
    def test_strict_convolutions(self):
        self.assertEqual(max(self.c['ordinary_convolution']),112)
        self.assertEqual(max(r['bound'] for r in self.c['root_return_convolution']),103)
        self.assertLess(112,117)
    def test_complete_not_capped(self):
        self.assertFalse(self.c['result']['capped']);self.assertEqual(self.c['exit_code'],0)
        self.assertEqual(self.c['result']['nodes'],7712526)
    def test_tiny_cap_is_not_a_proof(self):
        p=subprocess.run([str(ROOT/'outputs/round137_root_return_capacity_codex.exe'),'1'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertTrue(json.loads(p.stdout)['capped'])
    def test_conditional_seven_row_ledger(self):
        x=json.loads((ROOT/'outputs/rr_round137_gap_closure_ledger_codex.json').read_text())
        self.assertEqual(len(x['rows']),7);self.assertEqual(x['rows_remaining'],0)
        self.assertEqual(x['outer_after'],'11/55');self.assertEqual(x['NR6'],'ASSUMED')
        self.assertEqual(x['L6_ge872'],'NOT_PROVED')
    def test_independent_nodes_differ_but_capacities_agree(self):
        v=json.loads((ROOT/'outputs/rr_round137_verified_codex.json').read_text())
        self.assertTrue(v['verified']);self.assertEqual(v['independent_capacity']['nodes'],29959867)
        self.assertFalse(v['global_L6_ge872']);self.assertEqual(v['NR6'],'ASSUMED')
if __name__=='__main__':unittest.main()
