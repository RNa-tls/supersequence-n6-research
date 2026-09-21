from probe_bulk_queries_j171 import *

if __name__=='__main__':
    f,refs,dep,env,backed=initial();cert={k:v[0] for k,v in dep.items()}
    cell=key('2|3|1|1|0|0');candidate=key('2|1|2|1|0|0');bound=f['J'][text(cell)]
    p=Probe(cert,100000,cell,bound,candidate);tok,err=p.build(cell,bound)
    control=G.Engine(cert,100000);ct,ce=control.build(cell,bound)
    assert (tok,err,p.nodes)==(ct,ce,control.nodes)
    out=dict(target=text(cell),bound=bound,candidate=text(candidate),candidate_inserted=False,
        probe_nodes=p.nodes,control_nodes=control.nodes,ub_calls=p.queries,
        applicable_calls=sum(p.app.values()),failed_prune_applicable_calls=sum(p.failed.values()),
        failed_query_rows=[dict(query=text(k),required_upper=u,current_upper=v,count=n) for (k,u,v),n in p.failed.most_common()],
        counterfactual_upper_benefit={str(u):sum(n for (k,needed,v),n in p.failed.items() if u<=needed) for u in [50,60,70,80,90,100]},
        source_sha256=sha('r171/src/probe_bulk_b2b_j171.py'),observer_sha256=sha('r171/src/probe_bulk_queries_j171.py'),
        status='BOUNDED_DIAGNOSTIC')
    atomic(BASE+'helper_b2b_query_probe.json',out);print(out)
