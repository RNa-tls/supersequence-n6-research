"""Conservation and proof-scope controls for the final threshold ledger."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from verify_round143_end_to_end_codex import independent_domain,KEYS
from research_round143_budgets_codex import domain
from verify_round143_component_pairs_codex import load_decisions


class ThresholdLedger(unittest.TestCase):
    def test_independent_topology_arithmetic(self):
        _,rows=domain()
        self.assertEqual(independent_domain(),{tuple(r[k] for k in KEYS) for r in rows})

    def test_final_conservation(self):
        d=json.loads((ROOT/'outputs/rr_round143_threshold_final_codex.json').read_text())
        self.assertEqual({tuple(r[k] for k in KEYS) for r in d['rows']},independent_domain())
        self.assertTrue(all(d['threshold_closed'].values()))
        self.assertEqual(sum(sum(c.values()) for c in d['counts'].values()),len(d['rows']))
        for row in d['rows']:
            if row['status']=='ALL_COMPONENT_P_PAIRS_EXCLUDED':
                self.assertEqual(row['remaining_component_pairs'],[])
                self.assertTrue(row['component_pair_exclusions'])
            if row['status']=='COMPONENT_CAPACITY_EXCLUDED':
                self.assertLess(row['component_convolution']['upper'],row['P_required'])

    def test_all_required_cycle_queries_complete(self):
        kind,decisions=load_decisions(ROOT/'outputs/rr_round143_cycle_pair_decisions_codex.json')
        d=json.loads((ROOT/'outputs/rr_round143_component_path_refined_ledger_codex.json').read_text())
        needed={tuple(p['cycle']) for r in d['rows'] for p in r.get('remaining_component_pairs',[])}
        self.assertEqual(kind,'cycle')
        self.assertEqual(set(decisions),needed)
        self.assertTrue(all(not x['possible'] for x in decisions.values()))
        self.assertTrue(all(x['exact_P']==key[-1] for key,x in decisions.items()))


if __name__=='__main__':unittest.main()
