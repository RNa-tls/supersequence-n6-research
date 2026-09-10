import sys,itertools,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import research_round142_route_a_codex as a
import research_round142_dirty_topology_codex as b
import verify_round142_dirty_catalog_codex as c
import verify_round142_selected_outer_codex as v

class RepeatDomain(unittest.TestCase):
    def test_clean_suffix_independent(self):
        for n in (3,4):
            rows=a.formula_catalog(n); bfs,meta=a.independent_suffix_bfs(n)
            self.assertEqual({p:r['clean_cost'] for p,r in rows.items()},{p:len(t) for p,t in bfs.items()})
            self.assertTrue(meta['exhausted'])
    def test_spacer_all_n6(self):
        for r in a.formula_catalog(6).values():
            self.assertEqual(a.window_list(r['spacer_witness'],6),[(0,r['source']),(7,r['target'])])
    def test_sigma2_local_counterexample(self):
        rows=a.formula_catalog(6);r=rows['234501'];cert=a.local_counterexample(r,rows)
        self.assertEqual(cert['feasible_repeat_cost'],2)
        self.assertGreater(cert['exact_repeat_free_cost'],2)
    def test_all_n4_orders_are_not_enumerated(self):
        self.assertEqual(len(c.catalog(4)['minimum_rows']),23)
    def test_four_dirty_light_operators(self):
        d=c.catalog(6);v0=(1,2,3,4,5,0)
        pred={'01':c.sigma(v0),'012':c.sigma(c.sigma(v0)),
              '021':c.E(c.sigma(v0)),'102':c.sigma(c.E(v0))}
        selected=[r for r in d['minimum_rows'] if r['weight'] in (2,3) and not r['clean']]
        self.assertEqual(len(selected),4)
        for r in selected:self.assertEqual(r['target']['permutation'],c.encode(pred[r['tail']]))
    def test_actual_vs_shortest_distinction(self):
        # First-occurence selection is preserved on an actual word, not on
        # independently shortened connectors unless a fixed point is reached.
        self.assertEqual(len(a.window_list('01232301',4)),2)
        self.assertEqual(len(a.window_list('012301',4)),3)
    def test_repeat_selected_nu(self):
        word,_=b.fixed_point('0120102102',3)
        row=b.audit_word(word,3); v.check(row)
        self.assertEqual(sorted(row['nu']),list(range(row['selected_P'])))
    def test_dirty_genus_charge_all_s3_projections(self):
        ww=set()
        for p in itertools.permutations(['012','021','102','120','201','210']):
            w,_=b.fixed_point(b.spelling(p),3);ww.add(w)
        for w in ww:
            r=b.audit_word(w,3);v.check(r)
            self.assertLessEqual(r['D2']+r['D3_same'],r['R_int'])
    def test_no_capacity_sigma_silently(self):
        r=b.audit_word(b.fixed_point('0120102102',3)[0],3)
        for p in r['pieces']:
            self.assertEqual(len(b.windows(p['word'],3)),3*p['P'])
    def test_frontier_not_used(self):
        for mod in (a,b,c,v):
            self.assertNotIn('search_rr_target_a',Path(mod.__file__).read_text())

if __name__=='__main__':unittest.main()
