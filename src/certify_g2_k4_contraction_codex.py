"""Assemble a portable dependency ledger; never runs a complete NR6 search."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    old=ROOT.parent/'supersequence-n6-research-round115-f0-audit'
    dependencies=['outputs/rr_round115_codex_nstar_0_0_20.json',
                  'outputs/rr_round115_codex_source_replays.json',
                  'outputs/rr_round115_f0_codex_audit.json']
    dep={name:dict(original_path=str(old/name),sha256=sha(old/name),
                   payload=json.loads((old/name).read_text())) for name in dependencies}
    capacity=dep[dependencies[0]]['payload']
    replay=dep[dependencies[1]]['payload']
    assert capacity=={k:v for k,v in replay['nstar']['0,0,20'].items() if k!='elapsed_seconds'}
    assert (capacity['b'],capacity['g'],capacity['s'],capacity['passes'],capacity['capped'])==(0,0,20,103,False)
    source=ROOT/'src/chain_capacity_115.c'
    assert sha(source)==replay['source_sha256']['chain_capacity_115.c']
    controls=json.loads((ROOT/'outputs/rr_locked_detour_contraction_codex.json').read_text())
    assert controls['verdict']=='UNSAT_COMPLETE'
    assert sum(controls['n4']['counts'].values())==25
    rows=[]
    for name,count in [('P0-alpha',25),('P1-alpha',25),('P1-beta',15),('T',16),('D-alpha',25),('D-beta0',12)]:
        rows.append(dict(family=name,round133_remaining_splits=count,new_remaining_splits=0,
                         proof='two contractions -> P112 O26 D18 e0 x0 H0 -> Nstar(0,0,20)<=103'))
    result=dict(schema='codex/g2-k4-locked-detour-closure/1',
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                theorem_status='PROVED_WITH_EXISTING_FINITE_CAPACITY_CERTIFICATE',
                assumption='NR6; Round131 equality and Round132 exhaustive alpha/beta lock taxonomy',
                dependencies=dep,capacity_source_sha256=sha(source),
                capacity_binary_original_path=str(old/'outputs/chain_capacity_115_codex.exe'),
                capacity_binary_sha256=sha(old/'outputs/chain_capacity_115_codex.exe'),
                capacity_node_count=capacity['nodes'],capacity_capped=False,
                fresh_capacity_search_this_round=False,
                controls_sha256=sha(ROOT/'outputs/rr_locked_detour_contraction_codex.json'),
                control_source_sha256=sha(ROOT/'src/verify_locked_detour_contraction_codex.py'),
                geometry_source_sha256=sha(ROOT/'src/research_alpha_gap_codex.py'),
                new_hand_proof='research/RR_G2_K4_LOCKED_DETOUR_CONTRACTION_CODEX.md',
                contracted=dict(P=112,O=26,D=18,S=25,H=0,e=0,x=0),
                local_capacity_model=dict(b=0,g=0,s=20,max_passes=103),
                contradiction='112 > 103',class_ledger=rows,
                remaining_B_classes=sum(r['new_remaining_splits'] for r in rows),
                cell_closed=True,outer_count_with_previously_accepted_closures='10/55',
                global_L6_ge_872_proved=False,
                units='S counts joints of weight >=3, NOT strand count; contraction is a partial chain, not an NR6 cover')
    result['deterministic_digest']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    (ROOT/'outputs/rr_g2_k4_contraction_certificate_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['theorem_status'],classes_before=sum(r['round133_remaining_splits'] for r in rows),classes_after=0,digest=result['deterministic_digest'])))


if __name__=='__main__':main()
