"""Preserve and replay the proposed-helper counterexample; not a production bound."""
from bulk_j171 import *

if __name__=='__main__':
    r=load(BASE+'small_helper_trial.json');assert r['status']=='PROPOSED_HELPER_REFUTED'
    f,refs,dep,env,backed=initial();path=[]
    def trace(frame,event,arg):
        if event=='exception' and arg[0] is StopIteration and not path and frame.f_code.co_name=='rec' and frame.f_locals.get('ports',0)>=60 and frame.f_locals.get('deficit',999)<=2:
            p=frame
            while p:
                if p.f_code.co_name=='rec' and 'ports' in p.f_locals:path.append(p.f_locals['v'])
                p=p.f_back
            path.reverse()
        return trace
    g=G.Engine({k:v[0] for k,v in dep.items()},100000)
    sys.settrace(trace)
    try:toks,err=g.build(key(r['cell']),r['proposed_upper'])
    finally:sys.settrace(None)
    # The first deficit-feasible endpoint may exceed target=60: the generator
    # stops at ports >= target, not necessarily ports == target.
    assert toks is None and g.nodes==r['nodes'] and len(path)>=60,(err,g.nodes,r['nodes'],len(path))
    ok,detail=G.R.replay_chain_witness(key(r['cell']),path);assert ok
    atomic(BASE+'small_helper_counterexample.json',dict(cell=r['cell'],unsupported_upper=59,
        witness_ports=path,witness_permutations=[G.R.PERMS[p] for p in path],replay_ok=ok,
        replay_detail=detail,additional_generation_nodes=g.nodes,production_certificate=False,
        prior_export_assertion_failures=2,prior_export_nodes=2*g.nodes,
        conclusion='No upper <=59 is possible for this candidate; none was admitted.',
        driver_sha256=sha('r171/src/replay_small_helper_counterexample_j171.py')))
    print(detail)
