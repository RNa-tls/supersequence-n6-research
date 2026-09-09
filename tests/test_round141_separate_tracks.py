import functools,itertools,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import verify_round141_outer_codex as outer
import verify_round141_completion_cover_codex as cover
import research_round141_repeat_credit_codex as repeat
import verify_round141_nr_foundation_codex as nr
import research_round141_nr6_codex as foundation
import verify_round141_j_topology_codex as topo
import verify_round141_nr_geodesic_templates_codex as templates
def load(name):return json.loads((ROOT/'outputs'/name).read_text())

class OuterTests(unittest.TestCase):
    def test_full_grid_scope(self):
        d=load('rr_round141_outer_verified_codex.json');cells=d['ledger']['cells']
        self.assertEqual({(r['k'],r['G']) for r in cells},{(k,g) for k in range(5) for g in range(5*k+1)})
        self.assertEqual(len(cells),55);self.assertTrue(all(r['status']=='CLOSED' for r in cells))
        self.assertEqual(len(d['ledger']['new_cells']),38)
        self.assertEqual(d['NR6'],'ASSUMED');self.assertEqual(d['global_L6_ge872'],'NOT_PROVED')
    def test_envelopes_and_equalities(self):
        rows=load('rr_round141_outer_verified_codex.json')['ledger']['rows']
        self.assertEqual(len(rows),160);self.assertEqual(sum(r['required']==r['upper'] for r in rows),6)
        self.assertTrue(all(r['required']>r['upper'] for r in rows if r['G']>=8))
        self.assertTrue(all(r['m']<=5-r['k'] for r in rows))
    def test_slack_types(self):
        d=load('rr_round141_outer_codex.json')
        self.assertEqual(len(d['slack_types']),56);self.assertEqual(len(d['k0_slack']),35)
        self.assertTrue(all(r['k']+sum(r[v] for v in ['J','delta','x','H'])<=4 for r in d['slack_types']))
    def test_independent_extreme_paths(self):
        a=load('rr_round141_extrema_codex.json')['rows'];b=load('rr_round141_outer_verified_codex.json')['jobs']
        self.assertEqual([r['count'] for r in a],[1,2,2,2])
        for r,z in zip(a,b):
            self.assertFalse(r['capped']);self.assertFalse(z['result']['capped'])
            self.assertEqual({tuple(v) for v in r['paths']},{tuple(v) for v in z['result']['paths']})
    def test_legal_seam_not_mislabelled_collision(self):
        rows=load('rr_round141_outer_verified_codex.json')['seams']
        self.assertEqual(sum(r['G']==4 for r in rows),52)
        legal=[r for r in rows if not r['overlap']];self.assertEqual(len(legal),1)
        self.assertEqual(legal[0]['G'],7);self.assertEqual(legal[0]['status'],'STATIC_COMPLETION_UNSAT')
        self.assertEqual(legal[0]['sharing'],0)
        word,weights=outer.full_word(legal[0]['left']+legal[0]['right'])
        self.assertEqual(word,legal[0]['word']);self.assertEqual(weights.count(4),1)
    def test_second_cover_check_of_legal_seam(self):
        row=next(r for r in load('rr_round141_outer_verified_codex.json')['seams'] if not r['overlap'])
        entries=row['left']+row['right'];ph,pq,blocks,_=cover.geometry()
        U=((1<<120)-1)^sum(1<<h for h in {ph[v] for v in entries})
        closed=[q for q in range(144) if q not in {pq[v] for v in entries}]
        z=cover.exact_k_cover(U,closed,blocks,7)
        self.assertEqual(z['status'],'UNSAT');self.assertFalse(z['capped'])
    def test_both_cover_solvers_on_extrema(self):
        for r in load('rr_round141_outer_verified_codex.json')['completion_covers']:
            self.assertEqual(cover.complete_chain(r['entries'])['status'],r['status'])
    def test_cover_geometry_independence(self):
        self.assertEqual(list(cover.geometry()[2]),outer.BLOCKS)
    def test_binary_solver_positive_and_exhaustive_tiny_controls(self):
        candidates=list(range(8));bits=sorted({h for q in candidates for h in range(120) if outer.BLOCKS[q]>>h&1})[:5]
        for flags in range(32):
            U=sum(1<<h for i,h in enumerate(bits) if flags>>i&1)
            for k in range(5):
                truth=any(U&~functools.reduce(int.__or__,(outer.BLOCKS[q] for q in ss),0)==0 for ss in itertools.combinations(candidates,k))
                z=outer.binary_cover(U,candidates,k)
                self.assertEqual(z['status']=='SAT',truth)
                if truth:self.assertEqual(len(z['witness']),k)
    def test_cap_is_not_exhaustion(self):
        for exe in ['round141_extrema_codex.exe','round141_verify_extrema_codex.exe']:
            p=ROOT/'outputs'/exe
            if not p.exists():self.skipTest('Build finite C executables first')
            z=subprocess.run([str(p),'96','14','1'],capture_output=True,text=True)
            self.assertEqual(z.returncode,2);self.assertTrue(json.loads(z.stdout)['capped'])
    def test_new_J_theorems(self):
        for n in range(1,7):
            for p in itertools.permutations(range(n)):
                z=topo.audit_permutation(p);self.assertLessEqual(z['J'],2*z['g'])
        z=topo.audit_word(topo.CROSSING_WORD);self.assertEqual(z['J'],0);self.assertTrue(z['crossing'])
    def test_no_suspect_supply_helper(self):
        for p in ['src/verify_round141_outer_codex.py','src/research_round141_outer_codex.py','src/round141_verify_extrema_codex.c','src/round141_extrema_codex.c']:
            self.assertNotIn('true_phase_walk_capacity(', (ROOT/p).read_text())

class NRTests(unittest.TestCase):
    def test_local_repeat_template_catalog(self):
        a=templates.endpoint_catalog(6);b,nodes=templates.tail_catalog(6)
        self.assertEqual(nodes,55986);self.assertEqual(len(a),719)
        self.assertTrue(all(all(v[k]==a[t][k] for k in v) for t,v in b.items()))
        zero=[r for r in a.values() if r['hidden_count'] and not r['necessary_credit']]
        self.assertEqual(len(zero),7);self.assertEqual(len({tuple(r['actual_gaps']) for r in zero}),5)
    def test_first_projection_equality_is_literal(self):
        for w in ['0120121021','0121020102120','0120102102']:
            path=templates.stabilize(w,3)
            self.assertTrue(all(len(b)<len(a) for a,b in zip(path,path[1:])))
            self.assertEqual(templates.project_first(path[-1],3),path[-1])
    def test_literal_negative_delta_is_retained(self):
        r=repeat.analyse('0120121021',3)
        self.assertGreater(r['Y'],0);self.assertLess(r['delta'],0)
        self.assertGreaterEqual(r['epsilon'],0);self.assertEqual(nr.independent_credit(r['word'],3)['Y'],r['Y'])
    def test_n3_graph_independent(self):
        d=nr.nr3_graph();self.assertEqual((d['vertices'],d['edges'],d['normalized']),(720,10872,720))
    def test_n4_one_repeat_bound_layouts(self):
        rows=load('rr_round141_repeat_credit_codex.json')['nr4_bound_single_repeat_layouts']
        self.assertEqual(len(rows),6)
        self.assertTrue(all(len(r['word'])==33 and r['distinct']<24 for r in rows))
    def test_constructive_minima(self):
        for n,w,L in [(3,'012010210',9),(4,'012301203120132010231021302103210',33)]:
            r=repeat.analyse(w,n);self.assertEqual(r['L'],L);self.assertEqual(r['R'],0)
    def test_nr6_not_claimed(self):
        for f in ['rr_round141_nr6_foundation_codex.json','rr_round141_repeat_credit_codex.json','rr_round141_nr6_verified_codex.json']:
            self.assertEqual(load(f)['NR6'],'UNPROVED')
    def test_repeat_controls_both_implementations(self):
        d=load('rr_round141_repeat_credit_codex.json')
        self.assertEqual(d['controls'],3096);self.assertEqual(d['Y_positive'],1458)
        for r in [d['nr4_trap'],*d['n6_controls']]:
            a=repeat.analyse(r['word'],r['n']);b=nr.independent_credit(r['word'],r['n'])
            self.assertTrue(all(a[k]==b[k] for k in b if k!='bad_sources'))
    def test_loop_deletion_false_stronger_rule(self):
        r=foundation.loop_delete('01202102101200120010200201',3,0,9)
        self.assertFalse(r['globally_unique_inside']);self.assertEqual(r['lost'],['021','210'])
    def test_loop_deletion_exact_safe_case(self):
        r=foundation.loop_delete('012012012',3,0,3)
        self.assertTrue(r['coverage_preserved']);self.assertLess(len(r['after']),len(r['before']))
    def test_non_NR_successor_permutation_fails(self):
        self.assertFalse(foundation.splicing_balance('0120102102',3)['successor_matching_exists'])
    def test_strict_local_trap_not_normalization_counterexample(self):
        d=load('rr_round141_nr6_verified_codex.json')['local_plateau']
        self.assertTrue(d['completed']);self.assertGreater(d['clean_reachable'],0)
        self.assertFalse(d['single_relocation_normalization_refuted'])
        for a,b in zip(d['normalization_path'],d['normalization_path'][1:]):
            self.assertIn(tuple(b),nr.moves(tuple(a)));self.assertLessEqual(len(nr.spelling(b)),len(nr.spelling(a)))
    def test_context_count_is_not_set(self):
        d=load('rr_round141_nr6_foundation_codex.json')['counterexamples']['endpoint_and_coverage_count_insufficient']
        self.assertEqual([d[w]['cost'] for w in ['0120012','0121012']],[6,5])
        self.assertNotEqual(d['0120012']['covered_mask'],d['0121012']['covered_mask'])

if __name__=='__main__':unittest.main()
