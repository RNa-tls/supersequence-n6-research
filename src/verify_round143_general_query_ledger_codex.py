"""Replay generic exact-P certificates and apply ONLY the d=0 inclusion."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from run_round143_general_prefix_codex import FIELDS,readpaths,replay,sha
from verify_round141_completion_cover_codex import geometry,exact_k_cover,controls

ROOT=Path(__file__).resolve().parents[1]
SOURCES=['outputs/rr_round143_general_prefix_pilot_codex.json','outputs/rr_round143_general_prefix_complete_codex.json']
BASE='outputs/rr_round143_t4_combined_codex.json'


def main():
    data=json.loads((ROOT/BASE).read_text());hashes={BASE:sha(ROOT/BASE)};queries={};paths={}
    for rel in SOURCES:
        hashes[rel]=sha(ROOT/rel);source=json.loads((ROOT/rel).read_text())
        assert source['schema']=='round143-paired-general-exact-P-v1'
        manifest=ROOT/source['bound_manifest'];assert sha(manifest)==source['bound_manifest_sha256']
        tableinfo=json.loads(manifest.read_text());assert sha(ROOT/tableinfo['table_file'])==source['table_sha256']==tableinfo['table_sha256']
        for row in source['rows']:
            key=tuple(row[x] for x in FIELDS);assert key not in queries
            sides=[]
            for name in ('producer','independent'):
                run=row[name];assert run['proof_query']=='EXACT_P_NOT_CAPACITY' and run['suffix_bound_enabled']
                file=ROOT/run['export_file'];assert sha(file)==run['export_sha256']
                result=readpaths(file,key);assert len(result)==run['independently_replayed_exports']==run['exported_prefixes']
                sides.append(result)
            if row['complete']:
                assert all(row[s]['completed'] and not row[s]['capped'] for s in ('producer','independent'))
                assert sides[0]==sides[1]
                assert hashlib.sha256(json.dumps(sorted(sides[0]),separators=(',',':')).encode()).hexdigest()==row['canonical_exports_sha256']
                assert bool(sides[0])==(row['status']=='EXACT_P_PREFIXES_COMPLETE')
                paths[key]=sides[0]
            else:assert row['status']=='UNKNOWN_CAP'
            queries[key]=dict(source=rel,status=row['status'],complete=row['complete'])
    phex,pq,blocks,_=geometry();static=[];static_cache={};control=controls()
    closed={'STRICT','SIGMA_DEFICIT_OBSTRUCTION','EXACT_P_EXCLUDED','ALL_PREFIX_STATIC_COMPLETIONS_EXCLUDED'}
    for row in data['rows']:
        if row['L']!=871 or row['d'] or row['status'] in closed:continue
        key=(row['D2'],row['Qs'],row['D2']+row['Z'],row['H'],row['Bstar'],5*row['k']-row['G'],row['P_required'])
        cert=queries.get(key)
        if not cert or not cert['complete']:continue
        row['general_exact_P_certificate']=cert
        if cert['status']=='NO_EXACT_P_PREFIX':
            row['status']='GENERAL_EXACT_P_EXCLUDED';continue
        outcomes=[]
        for entries in sorted(paths[key]):
            cachekey=(entries,row['c'])
            if cachekey not in static_cache:
                covered={phex[i] for i in entries};opened={pq[i] for i in entries}
                uncovered=((1<<120)-1)^sum(1<<h for h in covered)
                candidates=[q for q in range(144) if q not in opened]
                result=exact_k_cover(uncovered,candidates,blocks,row['c'])
                item=dict(query=key,c=row['c'],entries=list(entries),resources=replay(entries),
                          opened_orbits=sorted(opened),uncovered_hexagons=[h for h in range(120) if uncovered>>h&1],decision=result)
                static_cache[cachekey]=len(static);static.append(item)
            index=static_cache[cachekey];outcomes.append(index)
        row['general_static_completion_indices']=outcomes
        if all(static[i]['decision']['status']=='UNSAT' and static[i]['decision']['complete_finite_decision'] and not static[i]['decision']['capped'] for i in outcomes):
            row['status']='GENERAL_ALL_STATIC_COMPLETIONS_EXCLUDED'
    closed|={'GENERAL_EXACT_P_EXCLUDED','GENERAL_ALL_STATIC_COMPLETIONS_EXCLUDED'}
    data.update(schema='round143-generic-one-path-threshold-ledger-v1',generic_input_sha256=hashes,
                generic_unique_queries=len(queries),generic_query_counts=dict(Counter(q['status'] for q in queries.values())),
                generic_static_checks=static,generic_static_controls=control)
    data['counts']={str(L):dict(Counter(r['status'] for r in data['rows'] if r['L']==L)) for L in (869,870,871)}
    data['threshold_closed']={str(L):all(r['status'] in closed for r in data['rows'] if r['L']==L) for L in (869,870,871)}
    data['d0_871_closed']=all(r['status'] in closed for r in data['rows'] if r['L']==871 and r['d']==0)
    (ROOT/'outputs/rr_round143_generic_query_ledger_codex.json').write_text(json.dumps(data,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(counts=data['counts'],queries=len(queries),query_counts=data['generic_query_counts'],static_checks=len(static),d0_871_closed=data['d0_871_closed'])))


if __name__=='__main__':main()
