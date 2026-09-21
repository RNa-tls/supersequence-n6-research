"""One small upper-bound investment trial supported by observed failed queries."""
from bulk_j171 import *

if __name__=='__main__':
    f,refs,dep,env,backed=initial();q=load(BASE+'helper_query_probe.json')
    assert not q['candidate_inserted'] and q['target']=='2|6|4|0|0|0'
    k=key('2|2|0|0|0|0');bound=59
    support=sum(r['count'] for r in q['failed_query_rows'] if key(r['query'])==k and r['required_upper']>=bound)
    assert support>0
    r=dict(cell=text(k),proposed_upper=bound,observed_useful_query_occurrences=support,
        source_diagnostic_sha256=sha(BASE+'helper_query_probe.json'),cap=100000,
        justification='Narrow A=0 query slice observed directly; shared after A/B/E/H expenditure. No exact capacity assumption.',
        driver_sha256=sha('r171/src/probe_bulk_small_helper_j171.py'),versions=env['versions'])
    g=G.Engine({k:v[0] for k,v in dep.items()},r['cap']);t=time.monotonic();toks,err=g.build(k,bound)
    r.update(nodes=g.nodes,detail=err,status='PROVISIONALLY_GENERATED' if toks is not None else ('DEFERRED' if 'node cap' in (err or '') else 'PROPOSED_HELPER_REFUTED'))
    if toks is not None:
        path=BASE+'proofs/helper_b2_d2_a0_upper59.txt.gz';(ROOT/path).parent.mkdir(parents=True,exist_ok=True);assert not (ROOT/path).exists()
        plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(k,bound,toks)])
        r['certificate']=dict(path=path,sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest())
        atomic(BASE+'small_helper_trial.json',r)
        aa=A.verify(path);bb=B.verify_any(path);aa.pop('certified',None);bb.pop('certified',None)
        assert aa['ok'] and bb['ok'] and aa['nodes']==bb['nodes']==bb['hist_checks']==g.nodes
        assert [(x['cell'],x['cap']) for x in aa['rows']]==[(x['cell'],x['cap']) for x in bb['rows']]==[(text(k),bound)]
        r.update(A=aa,B=bb,status='CERTIFIED_HELPER',histogram_mismatches=0)
    atomic(BASE+'small_helper_trial.json',r)
    atomic(BASE+'timings/small_helper_trial.json',dict(elapsed_seconds=time.monotonic()-t,peak_memory_bytes=peak_memory()))
    print(r,flush=True)
