import importlib.util
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from research_round143_budgets_codex import domain
from verify_round143_general_endpoint_codex import solver, forward
from verify_round143_coupled_codex import replay, WORDS, validate_capacity_file
from verify_round143_coupled_extraction_codex import optimizers as coupled_optimizers


class Round143(unittest.TestCase):
    def test_budget_identity(self):
        parts,rows=domain()
        self.assertEqual(len(parts),65)
        self.assertEqual(len(rows),2067)
        for r in rows:
            self.assertEqual(r['t'],r['k']+r['Z']+r['H']+r['Bstar'])
            self.assertEqual(r['Z']+r['D2'],2*r['g']+r['d'])
            self.assertGreaterEqual(2*r['g'],r['D2']+r['Qs'])

    def test_two_general_optimizers(self):
        table={(0,0):[5,0,0,0],(0,1):[5,4,4,4],(0,2):[5,4,4,3]}
        back=solver(table)
        for a,o,d,bad in itertools.product(range(3),range(2),range(3),range(3)):
            self.assertEqual(back(a,o,0,d,bad,0),forward(table,a,o,0,d,bad))

    def test_missing_capacity_is_unknown(self):
        self.assertIsNone(solver({})(0,0,0,0,0,0))

    def test_literal_sigma_pair(self):
        ids=[WORDS.index(tuple(map(int,p))) for p in ('012345','123450')]
        self.assertEqual(replay(ids)['A'],1)
        self.assertEqual(replay(ids)['D'],8)
        with self.assertRaises(AssertionError):
            replay(ids+[ids[0]])

    def test_completed_sigma_pilot(self):
        cells,_=validate_capacity_file(ROOT/'outputs/rr_round143_coupled_A2_pilot_codex.json')
        self.assertEqual([(c['D'],c['upper']) for c in cells],
                         [(0,0),(1,0),(2,13),(3,27),(4,46),(5,46)])

    def test_869_paired_closure(self):
        data=json.loads((ROOT/'outputs/rr_round143_general_endpoint_corrected_codex.json').read_text())
        rows=[r for r in data['rows'] if r['L']==869]
        self.assertEqual(len(rows),92)
        self.assertTrue(all(r['status']=='STRICT' and r['independent_dp_match'] for r in rows))
        self.assertTrue(all(r['upper']<r['P_required'] for r in rows))
        self.assertFalse(data['threshold_closed']['870'])
        self.assertFalse(data['threshold_closed']['871'])

    def test_coupled_allocation_independence(self):
        cells=[dict(A=0,b=0,D=0,upper=20),dict(A=0,b=0,D=1,upper=20),
               dict(A=0,b=0,D=2,upper=33),dict(A=1,b=0,D=1,upper=9),
               dict(A=1,b=0,D=2,upper=28),dict(A=2,b=0,D=2,upper=13)]
        cap,back,fwd=coupled_optimizers(cells)
        for m,A,b,D in itertools.product(range(1,4),range(4),range(2),range(4)):
            self.assertEqual(back(m,A,b,D),fwd(m,A,b,D))
        self.assertEqual(cap(2,0,1),0)
        self.assertIsNone(cap(3,0,3))

    def test_sigma_propagation_certificate(self):
        data=json.loads((ROOT/'outputs/rr_round143_sigma_deficit_codex.json').read_text())
        self.assertEqual(data['local_renamings'],720)
        self.assertEqual(data['extension_control_count'],196)
        self.assertTrue(data['completed'])

    def test_870_complete_871_not_claimed(self):
        data=json.loads((ROOT/'outputs/rr_round143_coupled_extraction_codex.json').read_text())
        rows=[r for r in data['rows'] if r['L']==870]
        self.assertEqual(len(rows),427)
        self.assertTrue(all(r['status'] in ('STRICT','SIGMA_DEFICIT_OBSTRUCTION') for r in rows))
        self.assertTrue(data['threshold_closed']['869'])
        self.assertTrue(data['threshold_closed']['870'])
        self.assertFalse(data['threshold_closed']['871'])


if __name__=='__main__':
    unittest.main()
