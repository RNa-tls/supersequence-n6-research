import unittest
from joint_endpoint_codex import load

def verify_projection(e,edges):
    for row in {x['row_index'] for x in e['minimal_row_hyperedges']}:
        masks=[x['mask'] for x in edges if x['row_index']==row]
        for r in e['assignments']:
            predicted=any(r['mask']&m==m for m in masks)
            if predicted!=(row in r['open_rows']):
                raise ValueError(('unsafe interaction projection',row,r['mask']))

class ProductionRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=load('r171/certs/joint_endpoint_codex_171.json')
        cls.f=load('r171/certs/production_J_codex_171.json')
    def test_full_hypergraph(self):
        verify_projection(self.e,self.e['minimal_row_hyperedges'])
    def test_singleton_mutation_rejected(self):
        with self.assertRaises(ValueError):
            verify_projection(self.e,[e for e in self.e['minimal_row_hyperedges'] if len(e['cells'])<=1])
    def test_pairwise_mutation_rejected(self):
        with self.assertRaises(ValueError):
            verify_projection(self.e,[e for e in self.e['minimal_row_hyperedges'] if len(e['cells'])<=2])
    def test_J_is_frozen_not_optimized(self):
        self.assertEqual(self.f['J'],self.e['J'])
        self.assertEqual(self.f['PRODUCTION_VECTOR_J'],'SOUND')
        self.assertEqual(self.f['GLOBAL_PARETO_OPTIMUM'],'UNRESOLVED')
    def test_genuine_and_planning_are_separate(self):
        self.assertEqual(sum(r['value_role']=='GENUINELY_BACKED_VALUE' for r in self.f['dossier']),5)
        self.assertEqual(sum(r['value_role']=='PRODUCTION_TARGET_VALUE' for r in self.f['dossier']),30)
    def test_pilots_use_J_not_individual(self):
        p=load('r171/certs/production_pilots_codex_171.json')
        self.assertTrue(p['complete']);self.assertEqual(len(p['rows']),30)
        self.assertEqual(len({r['cell'] for r in p['rows']}),30)
        for r in p['rows']:
            self.assertEqual(r['target'],self.f['J'][r['cell']]+1)
            if not r['completed']:self.assertEqual(r['status'],'DEFERRED')

if __name__=='__main__':unittest.main()
