"""Bounded helper investment justified by observed failed-prune queries.

Never updates the bulk manifest or admits the helper to running workers.
"""
from bulk_j171 import *


if __name__=='__main__':
    f,refs,dep,env,base=initial();m=load(MAN)
    refs,dep=add_accepted(refs,m['accepted'])
    probe=load(BASE+'helper_e_query_probe.json')
    candidate=key('1|2|0|0|0|0');bound=45
    potential=sum(r['count'] for r in probe['rows'] if bound<=r['required_upper']
                  and all(a>=b for a,b in zip(candidate,key(r['query']))))
    assert potential>0 and probe['inserted_helpers']==[]
    out=dict(cell=text(candidate),bound=bound,node_cap=100000,potential_useful_calls=potential,
        observation_sha256=sha(BASE+'helper_e_query_probe.json'),
        source_sha256=sha('r171/src/probe_bulk_e_helper_j171.py'),
        production_environment_modified=False,load_bearing_target=False)
    start=time.monotonic();g=G.Engine({k:v[0] for k,v in dep.items()},100000)
    toks,error=g.build(candidate,bound)
    out.update(nodes=g.nodes,detail=error,generation_seconds=time.monotonic()-start)
    if toks is None:
        out['status']='DEFERRED' if 'node cap' in (error or '') else 'CANDIDATE_BOUND_NOT_PROVED_FEASIBLE_THRESHOLD_REACHED'
    else:
        path=BASE+'proofs/helper_e_b1d2_upper45.txt.gz'
        assert not (ROOT/path).exists()
        plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(candidate,bound,toks)])
        out['certificate']=dict(path=path,sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest())
        aa=A.verify(path);bb=B.verify_any(path)
        aa.pop('certified',None);bb.pop('certified',None)
        assert aa['ok'] and bb['ok']
        assert aa['nodes']==bb['nodes']==bb['hist_checks']==g.nodes
        assert [(r['cell'],r['cap'],r['nodes']) for r in aa['rows']]==[(r['cell'],r['cap'],r['nodes']) for r in bb['rows']]==[(text(candidate),bound,g.nodes)]
        out.update(status='DUAL_VERIFIED_HELPER_NOT_YET_ADMITTED',A=aa,B=bb,histogram_mismatches=0)
    atomic(BASE+'helper_e_b1d2_trial.json',out)
    print(json.dumps(out,indent=1))
