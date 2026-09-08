"""Privacy-layer ledger only; inherited capacities are not recomputed."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    files=['research/RR_ROUND138_UNIVERSAL_ORBIT_PRIVACY_CODEX.md',
           'outputs/rr_round138_privacy_controls_codex.json','outputs/rr_round138_privacy_verified_codex.json',
           'outputs/rr_round138_source_hash_correction_codex.json']
    x=json.loads((ROOT/files[1]).read_text());v=json.loads((ROOT/files[2]).read_text())
    assert v['verified'] and v['input_sha256']==sha(ROOT/files[1])
    assert v['targeted_delta1_counterexamples']==0 and v['independent_event_models']==12972
    prior='ec8a5f1aaa2d5b42dc885dca86420877287555aa'
    inherited=['outputs/rr_round137_gap_closure_ledger_codex.json',
               'outputs/rr_round137_root_return_capacity_codex.json','outputs/rr_round137_verified_codex.json']
    for p in inherited:assert subprocess.check_output(['git','show',prior+':'+p])==(ROOT/p).read_bytes()
    old=json.loads((ROOT/inherited[0]).read_text());assert len(old['rows'])==7
    rows=[dict(id=r['id'],mechanisms=r['mechanisms'],privacy='PROVED_BY_RUN_OPENING_INJECTION',
               private_orbits_shared=0,capacity=r['bounds'],required_pass_sum=117,status='EXCLUDED_UNDER_NR6') for r in old['rows']]
    out=dict(schema='codex/round138-universal-privacy-closure/1',author='CODEX',
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        dependencies_sha256={p:sha(ROOT/p) for p in files},inherited_unchanged_sha256={p:sha(ROOT/p) for p in inherited},
        quantifier='For every residual M/R walk, the cut selected by section 5 before testing privacy has disjoint registered orbit sets.',
        hand_proof='Report sections 2-5: run-boundary separation, injective additional-repeat charge, exhaustive Type A/B instantiation.',
        hand_proof_machine_formalized=False,finite_controls_do_not_replace_proof=True,
        sharing_charge='delta >= 1+s within the specified event geometry; delta=1 implies s=0',
        deficit_identity='18-5*r+5*s; proved r=1,s=0 for canonical cuts => 13',
        rows=rows,rows_closed=7,rows_remaining=0,cell_3_2='CLOSED_UNDER_NR6',
        accepted_outer_before='10/55',accepted_outer_after='11/55',
        prior_round137_status='PROVISIONAL; independent audit PARTIAL at privacy layer',
        NR6='ASSUMED',L6_ge872='NOT_PROVED',capacity_recomputed=False,NR6_DFS_performed=False,
        other_cells_investigated=False,new_capacity_models=False,
        targeted_configurations=x['controls']['attempted_one_port_contexts'],legal_sharing_configurations=67,
        distinct_legal_sharing_words=len({(r['n'],r['word']) for r in x['controls']['rows']}),
        all_legal_sharing_delta=2,supporting_event_CSP_models=12972,
        source_correction=files[3],final_status='ASTRA_R137_PRIVACY_PROVED')
    (ROOT/'outputs/rr_round138_privacy_ledger_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['rows_remaining','accepted_outer_after','distinct_legal_sharing_words','final_status']}))
if __name__=='__main__':main()
