import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from run_round143_general_prefix_codex import replay,normalized,INDEX
from prepare_round143_general_bounds_codex import build


class GeneralPrefix(unittest.TestCase):
    def test_nonmonotone_suffix_D(self):
        path=[INDEX[tuple(map(int,w))] for w in ['012345','234015','340125','401235']]
        whole=replay(path);prefix=replay(path[:1]);suffix=replay(normalized(path[1:]))
        self.assertEqual((whole['D'],whole['b']),(1,1))
        self.assertEqual((suffix['D'],suffix['b']),(2,0))
        self.assertEqual(whole['D']+5*whole['b']-prefix['D']-5*prefix['b'],2)
        self.assertTrue(whole['details'][0]['oldq'])

    def test_A_B_repeated_arrivals(self):
        path=[INDEX[tuple(map(int,w))] for w in ['012345','123450','345012']]
        result=replay(path)
        self.assertEqual((result['A'],result['Qs'],result['R']),(1,1,2))

    def test_small_materially_independent_controls(self):
        data=json.loads((ROOT/'outputs/rr_round143_general_paired_small_codex.json').read_text())
        self.assertTrue(data['verified'])
        self.assertEqual(len(data['controls']),10)
        for row in data['controls']:
            self.assertEqual(len(row['producer_comparisons']),3)
            self.assertTrue(all(x['prefixes']==row['literal_paths'] for x in row['producer_comparisons']))
        self.assertEqual(data['engine_sha256'],hashlib.sha256((ROOT/'src/round143_general_ports_independent.c').read_bytes()).hexdigest())
        self.assertEqual(data['producer_source_sha256'],hashlib.sha256((ROOT/'src/round143_general_runs_codex.c').read_bytes()).hexdigest())
        self.assertTrue(data['cap_is_unknown'] and data['overwrite_refused'])

    def test_missing_suffix_capacity_is_infinity(self):
        rows,_=build([],[(0,0,0,0,0,0,5),(1,0,1,0,0,1,9)])
        table={r[:-1]:r[-1] for r in rows}
        self.assertEqual(table[(0,0,0,0,0,0)],100000)
        self.assertEqual(table[(1,0,0,0,0,1)],0)


if __name__=='__main__':unittest.main()
