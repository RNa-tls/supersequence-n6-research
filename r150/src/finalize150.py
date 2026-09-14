"""Check audit artifacts, preserve honest hand/finite scope, extend the proof DAG."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import py_compile
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'r150/certs'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def write(name,x):
    p=OUT/name;assert '--refresh' in sys.argv or not p.exists(),p
    p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def main():
    conf=read('r150/certs/source_conformance.json');arb=read('r150/certs/arbitrary_states.json')
    cov=read('r150/certs/coverage.json');blk=read('r150/certs/blocks_production_comparison.json')
    mut=read('r150/certs/master_mutations150.json');mv=read('r150/certs/master150.json')
    assert conf['ok'] and conf['disagreements']==0 and arb['ok'] and cov['ok']
    assert all(x['completed'] and x['false_rejections']==0 for x in arb['results'])
    assert all(x['comparison']=='MATCH' and not x['production']['capped'] for x in blk['rows'])
    assert mut['ok'] and mut['detected']==18 and mv['certified']
    for r in conf['sources']:
        assert sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','r150/src','-p','test_feas150.py','-v'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stderr
    for p in (ROOT/'r150/src').glob('*.py'):
        py_compile.compile(str(p),cfile=str(ROOT/'r150/build'/ (p.stem+'.pyc')),doraise=True)
    # Recount row units without evaluating capacities: s variants vs base coordinate groups.
    sys.path.insert(0,str(ROOT/'r147/src'));import rows147
    units={}
    for t in range(5):
        rs=rows147.rows(t)
        units[str(t)]={'with_s':len(rs),'coordinate_groups':len({tuple(r[c] for c in rows147.COORD) for r in rs})}
        assert len(rs)==cov['row_counts_with_s'][str(t)]
    assert sum(x['coordinate_groups'] for x in units.values())==1609
    # Keep the earlier hand proof nodes. No finite experiment upgrades a theorem node.
    dag=read('r148/certs/dag_148.json')['dag']
    dag['H.feas']={'status':'PURE_HAND_PROOF','audit_status':'UNIVERSAL_INDEPENDENT_HAND_PROOF_WITH_FINITE_FALSIFICATION',
                  'what':'Token-Touched-Orbit Deficit Lemma; all admissible single-active-chain states, not just reached DFS states',
                  'where':'r150/PROOF.md sections 1-6','deps':['H.charging_rules150']}
    dag['H.charging_rules150']={'status':'INDEPENDENTLY_DUPLICATED','what':'Accepted R149 clean E stays in current orbit; every non-E old-orbit arrival costs one token; distinct-port D identity; source correspondence audited in R150',
                              'where':'r149/PROOF.md; r150/certs/source_conformance.json','deps':['E.catalogue']}
    for name in ('E.cells','E.implB','E.piecetab'):dag[name]['deps']=sorted(set(dag[name]['deps']+['H.feas']))
    dag['E.feas_falsification']={'status':'EXHAUSTIVE_UNCAPPED','what':'ONLY stated finite arbitrary-state and small-cell domains; corroboration, not the universal proof','deps':[], 'where':'r150/certs/arbitrary_states.json'}
    forbidden={'TESTED_ONLY','UNKNOWN_CAP','ERROR','REFUTED','UNAUDITED','BROKEN_TABLE','EXTERNAL_ASSUMPTION','MISSING','EMPIRICAL_ONLY'}
    def closure(n,trail=()):
        assert n not in trail,('cycle',trail,n)
        assert n in dag,n
        s={n}
        for d in dag[n]['deps']:s|=closure(d,trail+(n,))
        return s
    conclusions={}
    for n in ('C.ge872','C.le872','C.eq872'):
        ancestors=closure(n)
        bad=[k for k in ancestors if dag[k]['status'] in forbidden]
        assert not bad
        conclusions[n]=dict(ancestors=sorted(ancestors),forbidden=bad,
                            pure_hand_proof_nodes=sorted(k for k in ancestors if dag[k]['status']=='PURE_HAND_PROOF'))
    write('dag150.json',dict(dag=dag,conclusions=conclusions,
         scope='Existing non-feas ancestors are accepted as requested, not independently reproved in R150. Hand proofs remain hand proofs.'))
    clauses=[
      ('skip_current','omit nonnegative current-orbit deficit','MONOTONE_RELAXATION','SOUND'),
      ('opened_only','u=5-popcount over nonzero opened masks','EXACT_IDENTITY','SOUND'),
      ('ignore_hist0','zero contributes zero','EXACT_IDENTITY','SOUND'),
      ('descending_deficits','erase largest deficits to MINIMIZE required final deficit','LOWER_BOUND_MINIMIZATION','IDENTICAL'),
      ('take_min','take=min(hist[d],tok_left)','EXACT_RELAXED_ALLOCATION','IDENTICAL'),
      ('token_subtraction','one erased orbit per relaxed token','NECESSARY_RESOURCE_LOWER_BOUND','IDENTICAL'),
      ('residual_sum','sum deficits not erased','LOWER_BOUND_ON_FINAL_DEFICIT','IDENTICAL'),
      ('final_compare','reject iff lower bound > final deficit upper budget','NECESSARY_CONDITION_FAILURE','IDENTICAL')]
    write('clauses_and_monotonicity.json',dict(clauses=[dict(clause=a,interpretation=b,role=c,verdict=d) for a,b,c,d in clauses],
       budget_semantics='all six are upper budgets',monotonicity={'tok':'nondecreasing acceptance','d':'nondecreasing acceptance','a':'feas independent; completion set nondecreasing','bb':'feas independent; completion set nondecreasing','e':'feas independent; completion set nondecreasing','h':'feas independent; completion set nondecreasing'},
       only_rejection_clause='tot > DMAX',universal_proof='r150/PROOF.md'))
    summary=dict(verdict='ROUND150_FEAS_FULLY_CERTIFIED',success_route='A: universal hand proof of all clauses + independent tests, not old-prune transcript certification',
        source_conformance_cases=conf['cases'],implementations=5,arbitrary_states=sum(x['arbitrary_states'] for x in arb['results']),
        rejected_state_budget_pairs=sum(x['rejected_state_budget_pairs'] for x in arb['results']),false_rejections=0,
        independent_n6_cells=len(blk['rows']),n6_matches=16,n6_unknown=0,
        targeted_mutations=dict(Counter(x['actual'] for x in conf['mutation_results'].values())),
        historical_mutations_before={'detected':17,'escaped':['10_source_hash_changed']},
        master150_mutations={'detected':18,'escaped':[]},master_verifier=True,
        row_units=units,budget_maxima=cov['t_le_4_maxima'],regression_stdout=tests.stdout,regression_stderr=tests.stderr,
        pure_hand_nodes=conclusions['C.eq872']['pure_hand_proof_nodes'],
        cheapest_remaining_risk='Error in an accepted extraction/charging premise or production state-maintenance implementation; not removed by A/B agreement. No proof-assistant kernel or historical per-prune certificates are claimed.',
        limits='No large cell recomputation, no full historical search replay, no expansion of theorem scope beyond accepted R148/R149 premises.',
        input_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        audit_sha256={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in (ROOT/'r150').rglob('*') if p.is_file() and p.suffix in ('.py','.md','.json','.c') and 'build' not in p.parts and p.name!='final150.json'})
    write('final150.json',summary)
    print(json.dumps({k:summary[k] for k in ('verdict','arbitrary_states','independent_n6_cells','targeted_mutations','row_units','pure_hand_nodes')}))

if __name__=='__main__':main()
