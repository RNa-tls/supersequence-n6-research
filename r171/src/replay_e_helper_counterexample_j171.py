"""Literal port replay of the rejected observation-driven helper proposal."""
from bulk_j171 import *


if __name__=='__main__':
    r=load(BASE+'helper_e_b1d2_trial.json')
    assert r['status']=='CANDIDATE_BOUND_NOT_PROVED_FEASIBLE_THRESHOLD_REACHED'
    f,refs,dep,env,base=initial();refs,dep=add_accepted(refs,load(MAN)['accepted'])
    cell=key(r['cell']);path=[]
    def trace(frame,event,arg):
        if event=='exception' and arg[0] is StopIteration and not path and frame.f_code.co_name=='rec' and frame.f_locals.get('ports',0)>r['bound'] and frame.f_locals.get('deficit',999)<=cell[1]:
            p=frame
            while p:
                if p.f_code.co_name=='rec' and 'ports' in p.f_locals:path.append(p.f_locals['v'])
                p=p.f_back
            path.reverse()
        return trace
    g=G.Engine({k:v[0] for k,v in dep.items()},r['node_cap'])
    sys.settrace(trace)
    try:toks,err=g.build(cell,r['bound'])
    finally:sys.settrace(None)
    assert toks is None and g.nodes==r['nodes'] and len(path)>r['bound']
    ok,detail=G.R.replay_chain_witness(cell,path);assert ok
    queries=load(BASE+'helper_e_query_probe.json')['rows']
    blocked=[q for q in queries if all(a>=b for a,b in zip(key(q['query']),cell))
             and q['required_upper']<len(path)]
    out=dict(cell=r['cell'],rejected_upper=r['bound'],ports=len(path),
        witness_port_ids=path,witness_permutations=[G.R.PERMS[p] for p in path],
        replay_ok=ok,replay_detail=detail,additional_generation_nodes=g.nodes,
        observed_failed_query_calls=sum(q['count'] for q in queries),
        calls_not_fixable_by_any_scalar_capacity_helper=sum(q['count'] for q in blocked),
        scalar_scope='Only recorded queries whose resource cell contains this concrete feasible witness; not a claim about target infeasibility.',
        helper_admitted=False,source_sha256=sha('r171/src/replay_e_helper_counterexample_j171.py'))
    atomic(BASE+'helper_e_b1d2_counterexample.json',out)
    print(json.dumps({k:v for k,v in out.items() if not k.startswith('witness_')},indent=1))
