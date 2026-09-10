import sys,itertools,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import research_round142_route_a_codex as a
import research_round142_dirty_topology_codex as b
import verify_round142_dirty_catalog_codex as c
import verify_round142_selected_outer_codex as v
import verify_round142_shadow_budget_codex as shadow
import research_round142_shadow_capacity_codex as cap

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
    def test_local_repeat_penalty_not_independent(self):
        r=a.formula_catalog(6)['345021']
        self.assertEqual((r['hidden_count'],r['extra_cost']),(1,3))
    def test_shadow_port_not_double_charged(self):
        for order in itertools.permutations(['012','021','102','120','201','210']):
            w,_=b.fixed_point(b.spelling(order),3)
            r=b.audit_word(w,3,keep_mixed=True);shadow.verify(r)
    def test_small_marked_capacities(self):
        for mode in ('A','AB'):
            for D,value in [(0,20),(1,20),(2,33),(3,33)]:
                row=cap.whole(D,mode);self.assertEqual(row['max_passes'],value)
                cap.verify_witness(row['witness'],mode)
    def test_light_clean_all_cells_verified(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'outputs/rr_round142_light_clean_all_g_verified_codex.json').read_text())
        self.assertTrue(d['all_light_clean_cells_closed'])
        self.assertEqual(d['envelope_counts'],{'STRICT':276,'EQUALITY':21,'OPEN_UPPER_BOUND':3})
        self.assertEqual(sum(r['seams'] for r in d['cases']),3504)
        self.assertEqual(sum(r['dirty_seams'] for r in d['cases']),1606)
        self.assertEqual(sum(r['full_disjoint'] for r in d['cases']),3)
    def test_old_outer_not_unconditionally_relabelled(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'outputs/rr_round141_outer_verified_codex.json').read_text())
        self.assertEqual(d['NR6'],'ASSUMED')
    def test_all_envelopes_independent_resource_enumeration(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'outputs/rr_round142_light_clean_envelopes_codex.json').read_text())
        got={(r['k'],r['G'],r['c'],r['H'],tuple(r['heavy']),r['s']) for r in d['rows']}
        expected=set()
        heavy=[()]
        for count in range(1,5):
            heavy+=list(itertools.combinations_with_replacement(range(4,8),count))
        for k in range(5):
            for G in range(5*k+1):
                for c0 in range(G+1):
                    for hs in heavy:
                        H=sum(x-3 for x in hs);B=4-G-k+c0-H;m=G+1-c0+len(hs)
                        if B<0:continue
                        for s in range(B+1):
                            if m==1 and s:continue
                            expected.add((k,G,c0,H,hs,s))
        self.assertEqual(got,expected);self.assertEqual(len(got),300)
    def test_cross_type_shadow_collision_forces_hex_collision(self):
        for p in itertools.permutations(range(6)):
            ghost=c.sigma(p)
            target=c.sigma(ghost)
            self.assertNotEqual(p,target)
            self.assertEqual(c.hx(p),c.hx(target))
    def test_unconditional_low_slack_only(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'outputs/rr_round142_low_slack_verified_codex.json').read_text())
        self.assertFalse(d['NR6_assumed'])
        self.assertEqual((d['L6_lower_bound'],d['L6_upper_bound']),(869,872))
        self.assertEqual(len(d['rows']),14)
        self.assertTrue(all(r['upper']<r['required'] for r in d['rows']))

if __name__=='__main__':unittest.main()
