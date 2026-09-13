"""Threshold ledger audit from independent arithmetic generation to closure.

No full-cover search. Rebuild all inherited strict resource bounds, replay
paired exports and static completions, and regenerate the new component
allocation/pair ledger rather than trusting its stored closed flags.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from verify_round143_coupled_codex import validate_capacity_file,replay as sigma_replay
from verify_round143_coupled_extraction_codex import optimizers,NEG
from verify_round143_general_endpoint_codex import solver,forward as endpoint_forward
from verify_round143_component_pairs_codex import load_decisions
from verify_round141_completion_cover_codex import complete_chain,geometry,exact_k_cover,controls
from run_round143_general_prefix_codex import sha,readpaths

ROOT=Path(__file__).resolve().parents[1]
FINAL='outputs/rr_round143_threshold_final_codex.json'
SNAPSHOT='outputs/rr_round143_component_snapshot1_ledger_codex.json'
CYCLE_INPUTS=['outputs/rr_round143_cycle_dominant_pilot_codex.json',
              'outputs/rr_round143_cycle_ordinary_snapshot1_codex.json',
              'outputs/rr_round143_cycle_exceptional_snapshot1_codex.json']
PAIR_INPUTS=['outputs/rr_round143_component_path_refinement_codex.json',
             'outputs/rr_round143_cycle_pair_decisions_codex.json']
KEYS=('L','k','G','D2','Z','H','Bstar','c','g','d','Qs','s','h')


def independent_domain():
    """Start from topology K,c,g rather than weak compositions of k,Z,H,B*."""
    answer=set()
    for L in (869,870,871):
        t=L-867
        for k in range(t+1):
            for G in range(5*k+1):
                for K in range(1,G+2):
                    if (G+1-K)%2:continue
                    g=(G+1-K)//2
                    for c in range(K):
                        d=K-1-c
                        for A in range(2*g+1):
                            Z=G-c-A
                            if Z<0 or k+Z>t:continue
                            for Q in range(2*g-A+1):
                                for H in range(t-k-Z+1):
                                    B=t-k-Z-H
                                    for h in range((H+2)//3,H+1):
                                        if (H==0)!=(h==0):continue
                                        for s in range(B+1):
                                            if A+Z+1+h==1 and s:continue
                                            answer.add((L,k,G,A,Z,H,B,c,g,d,Q,s,h))
    return answer


def audit_old_exact(rel):
    source=json.loads((ROOT/rel).read_text())
    assert source['schema']=='round143-paired-exact-P-v1'
    answer={}
    for row in source['rows']:
        key=tuple(row[k] for k in ('A','b','D','P'));sets=[]
        for side in ('producer','independent'):
            run=row[side]
            assert run['proof_query']=='EXACT_P_NOT_CAPACITY' and run['suffix_bound_enabled']
            file=ROOT/run['exported_file'];assert sha(file)==run['export_sha256']
            paths=[]
            for line in file.read_text().splitlines():
                x=json.loads(line);p=x['entries'] if isinstance(x,dict) else x
                r=sigma_replay(p)
                assert (r['A'],r['P'])==(key[0],key[3]) and r['b']<=key[1] and r['D']<=key[2]
                paths.append(tuple(p))
            assert len(paths)==len(set(paths))==run['independently_replayed_exports']
            sets.append(set(paths))
        complete=all(row[s]['completed'] and not row[s]['capped'] for s in ('producer','independent'))
        assert complete==row['complete']
        if complete:
            assert sets[0]==sets[1]
            assert hashlib.sha256(json.dumps(sorted(sets[0]),separators=(',',':')).encode()).hexdigest()==row['canonical_exports_sha256']
            answer[key]=sets[0]
    return answer


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='outputs/rr_round143_end_to_end_verified_codex.json')
    args=ap.parse_args()
    final=json.loads((ROOT/FINAL).read_text());hashes={FINAL:sha(ROOT/FINAL)}
    projected=[tuple(r[k] for k in KEYS) for r in final['rows']]
    independent=independent_domain()
    assert len(projected)==len(set(projected)) and set(projected)==independent
    for r in final['rows']:
        assert r['L']==867+r['k']+r['Z']+r['H']+r['Bstar']
        assert r['P_required']==120+r['G']-5*r['c']
        assert r['R_upper']==5*(r['L']-867)-r['c']-4*r['Z']-2*r['H']
    cells=[];ordinary={}
    for rel,digest in final['input_sha256'].items():
        if 'general_endpoint_corrected' in rel:continue
        new,checked=validate_capacity_file(ROOT/rel);assert digest==checked
        cells+=new;hashes[rel]=checked
        for c in new:
            if c['A']:continue
            key=c['b'],c['D'];values=tuple(c['endpoints'])
            ordinary[key]=tuple(min(x,y) for x,y in zip(ordinary[key],values)) if key in ordinary else values
    end=solver(ordinary);cap,back,forward=optimizers(cells);checked_end={};checked_coupled={}
    strict_methods=Counter()
    for r in final['rows']:
        delta=5*r['k']-r['G']+5*r['Bstar']
        lower=max(0,r['D2']+r['Qs']-r['Z']-r['d'])
        if r['status']=='SIGMA_DEFICIT_OBSTRUCTION':
            assert delta<lower
        if r['status']!='STRICT':continue
        lost=min(r['D2'],r['d'])
        key=(r['D2']-lost,r['Z']+r['h']+lost,r['Bstar']-r['s'],
             5*r['k']-r['G']+5*r['s'],r['Z']-r['Qs'])
        v=end(*key,0)
        if v is not None and v<r['P_required']:
            if key not in checked_end:
                w=endpoint_forward(ordinary,*key);assert v==w
                checked_end[key]=v
            strict_methods['independent_endpoint_bound']+=1
            continue
        values=[];unknown=False
        for s in range(r['Bstar']+1):
            for m in range(1,r['Z']+r['d']+2+r['h']):
                for Aret in range(lower,r['D2']+1):
                    query=(m,Aret,r['Bstar']-s,5*r['k']-r['G']+5*s)
                    if query not in checked_coupled:
                        x=back(*query);y=forward(*query);assert x==y
                        checked_coupled[query]=x
                    x=checked_coupled[query]
                    if x is None:unknown=True
                    else:values.append(x)
        assert not unknown and max(values,default=NEG)<r['P_required'],('strict bound did not reproduce',r)
        strict_methods['independent_coupled_bound']+=1
    old={}
    for rel in ('outputs/rr_round143_t4_exact_prefix_pilot_codex.json',
                'outputs/rr_round143_t4_b0_exact_prefix_codex.json',
                'outputs/rr_round143_t4_reentry_exact_prefix_codex.json'):
        new=audit_old_exact(rel);assert not(old.keys()&new.keys());old.update(new);hashes[rel]=sha(ROOT/rel)
    generic={};generic_paths={}
    for rel in ('outputs/rr_round143_general_prefix_pilot_codex.json',
                'outputs/rr_round143_general_prefix_complete_codex.json'):
        kind,new=load_decisions(ROOT/rel);assert kind=='path'
        assert not(generic.keys()&new.keys());generic.update(new);hashes[rel]=sha(ROOT/rel)
        source=json.loads((ROOT/rel).read_text())
        for row in source['rows']:
            key=tuple(row[k] for k in ('A','Qs','R','H','b','D','P'))
            if key in generic and generic[key]['possible']:
                generic_paths[key]=readpaths(ROOT/row['producer']['export_file'],key)
    static=[];static_cache={};control=controls();phex,pq,blocks,_=geometry()
    for r in final['rows']:
        if r['status']=='EXACT_P_EXCLUDED':
            assert r['Z']==r['H']==r['d']==r['Qs']==0
            key=(r['D2'],r['Bstar'],5*r['k']-r['G'],r['P_required'])
            assert key in old and not old[key]
        elif r['status']=='ALL_PREFIX_STATIC_COMPLETIONS_EXCLUDED':
            assert r['k']==4 and r['G']==r['c']==6 and r['Z']==r['H']==r['D2']==r['Bstar']==0
            entries=old[(0,0,14,96)];assert entries
            for p in entries:
                ck=('marked96',p)
                if ck not in static_cache:
                    static_cache[ck]=complete_chain(list(p));static.append(static_cache[ck])
                v=static_cache[ck];assert v['status']=='UNSAT' and v['complete_finite_decision'] and not v['capped']
        elif r['status'].startswith('GENERAL_'):
            assert r['d']==0
            key=(r['D2'],r['Qs'],r['D2']+r['Z'],r['H'],r['Bstar'],5*r['k']-r['G'],r['P_required'])
            assert key in generic
            if r['status']=='GENERAL_EXACT_P_EXCLUDED':assert not generic[key]['possible']
            else:
                assert r['status']=='GENERAL_ALL_STATIC_COMPLETIONS_EXCLUDED' and generic[key]['possible']
                for p in generic_paths[key]:
                    ck=('generic',p,r['c'])
                    if ck not in static_cache:
                        covered={phex[i] for i in p};opened={pq[i] for i in p}
                        U=((1<<120)-1)^sum(1<<h for h in covered)
                        static_cache[ck]=exact_k_cover(U,[q for q in range(144) if q not in opened],blocks,r['c'])
                        static.append(static_cache[ck])
                    v=static_cache[ck];assert v['status']=='UNSAT' and v['complete_finite_decision'] and not v['capped']
    # Recompute the remaining component domain from the previously checked
    # generic base, then require the entire record, not only totals, to agree.
    with tempfile.TemporaryDirectory(prefix='r143_final_verify_') as folder:
        a=Path(folder)/'component.json';b=Path(folder)/'final.json'
        subprocess.run([sys.executable,str(ROOT/'src/verify_round143_component_convolution_codex.py'),
                        *CYCLE_INPUTS,'--export-pairs','--output',str(a)],cwd=ROOT,check=True,capture_output=True)
        assert json.loads(a.read_text())==json.loads((ROOT/SNAPSHOT).read_text())
        subprocess.run([sys.executable,str(ROOT/'src/verify_round143_component_pairs_codex.py'),
                        '--base',str(a),'--decisions',*PAIR_INPUTS,'--output',str(b)],cwd=ROOT,check=True,capture_output=True)
        rebuilt=json.loads(b.read_text())
        # Only the temporary input path and its metadata differ.
        assert rebuilt['rows']==final['rows'] and rebuilt['counts']==final['counts']
        assert rebuilt['threshold_closed']==final['threshold_closed']
    for rel in [SNAPSHOT,*CYCLE_INPUTS,*PAIR_INPUTS]:hashes[rel]=sha(ROOT/rel)
    provenance=[];seen_blobs={}
    for rel in hashes:
        source=json.loads((ROOT/rel).read_text())
        if 'source_provenance' not in source:continue
        commit=source['source_commit'];checked_sources=[]
        for item in source['source_provenance']:
            key=commit,item['path']
            if key not in seen_blobs:
                raw=subprocess.check_output(['git','show',commit+':'+item['path']],cwd=ROOT)
                seen_blobs[key]=hashlib.sha256(raw).hexdigest()
            assert seen_blobs[key]==item.get('committed_lf_sha256',item.get('committed_sha256'))
            checked_sources.append(dict(path=item['path'],committed_sha256=seen_blobs[key],
                                        recorded_runtime_sha256=item['runtime_sha256']))
        if 'bound_manifest_sha256' in source:
            if 'bound_manifest' in source:manifest=ROOT/source['bound_manifest']
            else:manifest=(ROOT/source['argv'][source['argv'].index('--table')+1]).with_suffix('.json')
            assert sha(manifest)==source['bound_manifest_sha256']
            assert sha(manifest.with_suffix('.txt'))==source['table_sha256']
        if source.get('pair_ledger'):
            assert sha(ROOT/source['pair_ledger'])==source['pair_ledger_sha256']
        provenance.append(dict(artifact=rel,source_commit=commit,committed_sources=checked_sources,
                               compiler=source.get('compiler'),
                               note='Historical executable hashes remain in source artifacts; mutable legacy executable paths are not substituted for historical binaries'))
    assert all(final['threshold_closed'][str(L)] for L in (869,870,871))
    wordfile=ROOT/'data/verified_872_witness.txt';word=wordfile.read_text().strip()
    windows={word[i:i+6] for i in range(len(word)-5) if len(set(word[i:i+6]))==6}
    assert len(word)==872 and windows=={''.join(p) for p in itertools.permutations('123456')}
    data=dict(schema='round143-end-to-end-ledger-verification-v1',verified=True,
              independent_arithmetic_rows=len(independent),
              row_counts=dict(Counter(str(r[0]) for r in independent)),
              strict_methods=dict(strict_methods),endpoint_cells=len(checked_end),coupled_cells=len(checked_coupled),
              old_exact_queries=len(old),generic_exact_queries=len(generic),static_instances=static,
              static_controls=control,counts=final['counts'],threshold_closed=final['threshold_closed'],
              upper_witness=dict(path=wordfile.relative_to(ROOT).as_posix(),sha256=sha(wordfile),length=len(word),covered=len(windows)),
              proof_inputs_sha256=hashes,source_provenance_audit=provenance,
              verifier_sha256=sha(Path(__file__)),
              scope='Computer-assisted threshold ledger, conditional only on the stated unconditional fixed-point/splicing and capacity inclusion hand lemmas; no NR6 assumption')
    dest=ROOT/args.output;assert not dest.exists()
    dest.write_text(json.dumps(data,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,row_counts=data['row_counts'],strict_methods=data['strict_methods'],threshold_closed=data['threshold_closed'],upper_witness=data['upper_witness'])))


if __name__=='__main__':main()
