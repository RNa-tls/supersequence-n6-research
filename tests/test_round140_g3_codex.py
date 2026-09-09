"""Round140 soundness regressions; no large search in the test suite."""
import copy,itertools,json,sys,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from research_round140_g3_codex import parse,splice,compose6
from verify_round140_g3_codex import data_word,pieces_verify,graph_check,capacities,seams

def load(name):return json.loads((ROOT/'outputs'/name).read_text())

class Round140(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=load('rr_round140_g3_codex.json')
        cls.cert=load('rr_round140_certificate_codex.json')
        cls.nr4=load('rr_round140_nr4_codex.json')
        cls.cap=load('rr_round140_capacity_codex.json')

    def test_all_G_charging_on_complete_NR4_domain(self):
        hist=Counter()
        for w in self.nr4['words']:
            p=parse(w,4);hist[p['G']]+=1
            self.assertEqual(p['delta'],p['a']+p['eta'])
            self.assertLessEqual(p['f_out'],p['F']+p['e'])
            self.assertEqual(len(p['ordinary']),len(set(p['ordinary'])))
        self.assertEqual(hist,{0:827,1:5999,2:10625,3:7545,4:3384,5:629,6:246})
        self.assertFalse(self.nr4['summary']['capped'])
        self.assertEqual(self.nr4['summary']['nodes'],49682345)

    def test_exact_counterexample_to_delta_ge_J(self):
        r=self.cert['nr4']['stronger_bound_counterexample'];m=data_word(r['word'],4)['metrics']
        self.assertEqual((m['G'],m['F'],m['J'],m['delta']),(3,2,1,0))

    def test_unqualified_privacy_counterexample_and_correct_charge(self):
        r=self.cert['nr4']['unconditional_privacy_counterexample'];p=parse(r['word'],4)
        self.assertEqual((p['delta'],r['designated_typed_defects'],r['s'],r['o'],r['z']),(3,3,1,0,1))
        self.assertLess(p['delta'],r['designated_typed_defects']+r['s'])
        self.assertEqual(p['delta'],r['designated_typed_defects']+r['s']-r['o']-r['z'])

    def test_arbitrary_paid_cut_need_not_charge_repeat_run(self):
        p=parse('0123012013201',4)
        self.assertEqual((p['G'],p['O'],p['e'],p['x']),(0,1,0,1))
        # Cut at this intra-orbit paid joint: orbit shared, but e is zero.
        self.assertEqual(len(p['passes']),2)

    def test_all_connected_incidence_controls(self):
        count=0
        for n in range(1,9):
            for p in itertools.permutations(range(n)):graph_check(p);count+=1
        self.assertEqual(count,46233)

    def test_G3_supports_and_F(self):
        s=self.base['support']['g3_supports']
        self.assertEqual(len(s),41)
        self.assertEqual(Counter(r['type'] for r in s),{'A4':6,'A3B2':20,'B222':15})
        self.assertEqual(Counter((r['K'],r['R']) for r in s),{(4,0):11,(2,2):21,(2,1):8,(2,0):1})
        self.assertEqual({r['F'] for r in s if r['type']=='A4'},{1,2,3})
        self.assertEqual({r['F'] for r in s if r['type']=='A3B2'},{2,3})
        self.assertEqual({r['F'] for r in s if r['type']=='B222'},{3})

    def test_arc_lengths_not_F_equals_G(self):
        self.assertEqual([len(list(compose6(m))) for m in [4,3,2]],[10,10,5])
        counts=Counter()
        for r in self.base['support']['g3_supports']:counts[r['F']]+=r['local_shape_count']
        self.assertEqual(counts,{1:10,2:540,3:2385})

    def test_all_saved_piece_controls(self):
        rows=self.base['controls']['rows']+self.cert['nr4']['representatives']+self.cert['actual_gap_controls']
        for r in rows:pieces_verify(r)
        self.assertEqual(len(rows),1994)

    def test_shared_orbits_not_assumed_private(self):
        rows=[r for r in self.cert['nr4']['representatives'] if r['s']]
        self.assertTrue(rows)
        for r in rows:
            p=r['original'];self.assertEqual(r['b']+r['s'],p['S']+1-p['O']+r['c'])
            self.assertEqual(sum(z['metrics']['D'] for z in r['pieces']),p['D']+(r['n']-1)*r['s'])

    def test_wrong_piece_or_sharing_is_rejected(self):
        row=self.base['controls']['rows'][0]
        bad=copy.deepcopy(row);bad['s']+=1
        with self.assertRaises(AssertionError):pieces_verify(bad)
        bad=copy.deepcopy(row);bad['pieces'][0]['word']+='0'
        with self.assertRaises(AssertionError):pieces_verify(bad)

    def test_no_repeat_not_registration_only(self):
        with self.assertRaises(AssertionError):data_word('012301230',4)

    def test_actual_gap_not_silently_minimized(self):
        for r in self.cert['actual_gap_controls']:
            p=parse(r['word'],r['n'])
            self.assertEqual(p['weights'],[r['n']]);pieces_verify(r)
            a,b=p['passes'];self.assertEqual(a[0][1:],b[0][:-1])

    def test_heavy_refined_resource_coverage(self):
        hist=Counter()
        for r in self.cert['resource_coverage']:
            hist[r['k']]+={0:1,1:1,2:2,3:3}[r['H']]
            self.assertEqual(r['status'],'CLOSED')
        self.assertEqual(hist,{1:377,2:148,3:46,4:9})
        self.assertEqual(sum(hist.values()),580)

    def test_all_capacity_envelopes_and_unique_equality_splits(self):
        d=capacities(self.cert)
        self.assertEqual((d['envelopes'],d['equalities'],d['resource_rows']),(40,3,516))
        self.assertEqual(d['equality_deficit_splits'],[[4,8],[8,4]])

    def test_paired_capacity_complete(self):
        expected={(0,7):58,(1,7):73,(2,7):88,(0,2):33,(1,2):48,(2,2):63,(3,2):78}
        counts=Counter()
        for r in self.cap['rows']:
            z=r['result'];key=(z['b'],z['s']);counts[key]+=1
            self.assertEqual(z['passes'],expected[key]);self.assertFalse(z['capped']);self.assertEqual(r['exit_code'],0)
        self.assertEqual(counts,dict.fromkeys(expected,2))

    def test_wrong_capacity_arithmetic_rejected(self):
        bad=copy.deepcopy(self.cert)
        # Certificate verifier consumes independently preserved capacity inputs;
        # a false arithmetic claim must not survive even with correct counts.
        bad['bounds']['rows'][0]['capacity_bound']-=1
        with self.assertRaises(AssertionError):capacities(bad)
        self.assertTrue(all(int(r['result']['nodes'])<20000000000 for r in self.cap['rows']))

    def test_cap_cannot_mean_complete(self):
        bad=copy.deepcopy(self.cap);bad['rows'][0]['result']['capped']=True
        def mutated_load(f):return bad if f=='rr_round140_capacity_codex.json' else load(f)
        with patch('verify_round140_g3_codex.load',side_effect=mutated_load):
            with self.assertRaises(AssertionError):capacities(self.cert)

    def test_all_extremal_seams_hex_collide(self):
        d=seams(self.base)
        self.assertEqual(d['attempts'],52);self.assertEqual(d['hex_collision'],52)
        self.assertEqual(d['extreme_counts'],{'4':1,'8':2})

    def test_scope_and_provisional_inheritance(self):
        c=self.cert
        self.assertEqual(c['G3_cells'],[[1,3],[2,3],[3,3],[4,3]])
        self.assertEqual(c['inherited_R139'],'PROVISIONAL_PENDING_EXTERNAL_AUDIT')
        self.assertEqual(c['combined_provisional_ledger'],'17/55')
        self.assertEqual(c['NR6'],'ASSUMED');self.assertEqual(c['global_L6_ge_872'],'NOT_PROVED')

if __name__=='__main__':unittest.main()
