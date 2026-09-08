"""Final conditional ledger. Does not turn finite control coverage into a theorem."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    files=['research/RR_G2_K3_ONE_DEFECT_GAP_CUT_CODEX.md',
           'outputs/rr_round137_gap_cut_codex.json','outputs/rr_round137_verified_codex.json',
           'outputs/rr_round137_root_return_capacity_codex.json','outputs/rr_round137_protected_seam_codex.json',
           'outputs/rr_round136_verified_codex.json','outputs/rr_round135_verified_codex.json']
    v=json.loads((ROOT/files[2]).read_text());assert v['verified']
    assert (v['M_bound'],v['R_bound'],v['required_pass_sum'])==(112,103,117)
    data=json.loads((ROOT/'outputs/rr_round136_defects_codex.json').read_text())
    rows=[]
    for r in data['rows']:
        kinds=sorted({'M' if p['a']==1 else 'R' for p in r['patterns']})
        rows.append(dict(id=r['id'],type=r['type'],e=r['e'],f_out=r['f_out'],P=122,O=27,D=13,S=25,N=0,
                         mechanisms=kinds,bounds={k:v[k+'_bound'] for k in kinds},required_pass_sum=117,
                         proof='multi-orbit gap extraction inclusion + inherited/new finite capacities',
                         status='EXCLUDED_UNDER_NR6'))
    assert len(rows)==7
    out=dict(schema='codex/round137-conditional-gap-closure/1',author='CODEX',
             source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             dependencies_sha256={f:sha(ROOT/f) for f in files},rows=rows,
             proof_layers=dict(universal_inclusion='HAND_PROOF, sections 5-6; not certified by samples',
                               local_capacities='FINITE_COMPLETE, two algorithms',controls='FINITE_SPECIFIED_DOMAIN'),
             new_rows_closed=7,prior_rows_closed=18,total_cell_rows=25,rows_remaining=0,
             M_off_target='EXCLUDED',R_target_coupled='EXCLUDED',cell_3_2='CLOSED_UNDER_NR6',
             outer_before='10/55',outer_after='11/55',NR6='ASSUMED',L6_ge872='NOT_PROVED',
             complete_NR6_search_performed=False,other_cells_investigated=False,
             final_status='ASTRA_G2_K3_CLOSED')
    out['mathematical_digest']=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (ROOT/'outputs/rr_round137_gap_closure_ledger_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['new_rows_closed','rows_remaining','outer_after','final_status']}))
if __name__=='__main__':main()
