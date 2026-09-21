"""One bounded observation-only helper-admissibility probe; no helper insertion."""
from bulk_j171 import *

class Probe(G.Engine):
    def __init__(self,cert,cap,cell,bound,candidate):
        super().__init__(cert,cap);self.cell=cell;self.bound=bound;self.candidate=candidate
        self.app=collections.Counter();self.failed=collections.Counter();self.queries=0
    def ub(self,*k):
        v=super().ub(*k);self.queries+=1
        ports=sys._getframe(1).f_locals['ports']
        if all(a>=b for a,b in zip(self.candidate,k)):
            needed=self.bound+1-ports
            self.app[(k,needed)]+=1
            if v>needed:self.failed[(k,needed,v)]+=1
        return v

if __name__=='__main__':
    f,refs,dep,env,backed=initial();cert={k:v[0] for k,v in dep.items()}
    cell=key('2|6|4|0|0|0');candidate=key('2|2|4|0|0|0');bound=f['J'][text(cell)]
    p=Probe(cert,100000,cell,bound,candidate);tok,err=p.build(cell,bound)
    direct=G.Engine(cert,100000);dt,de=direct.build(cell,bound)
    assert (tok,err,p.nodes)==(dt,de,direct.nodes)
    out=dict(target=text(cell),bound=bound,target_ports=bound+1,candidate=text(candidate),
        probe_nodes=p.nodes,control_nodes=direct.nodes,exact_bound_or_cost_inferred=False,
        candidate_inserted=False,ub_calls=p.queries,applicable_calls=sum(p.app.values()),
        failed_prune_applicable_calls=sum(p.failed.values()),status='BOUNDED_DIAGNOSTIC',
        failed_query_rows=[dict(query=text(k),required_upper=u,current_upper=v,count=n) for (k,u,v),n in p.failed.most_common()],
        counterfactual_upper_benefit={str(u):sum(n for (k,needed,v),n in p.failed.items() if u<=needed) for u in [50,60,70,80,90,100]},
        source_sha256=sha('r171/src/probe_bulk_queries_j171.py'),unchanged_generator_sha256=sha('r168/src/gen168.py'),
        concurrency='one diagnostic process alongside up to three production workers; no shared output paths')
    atomic(BASE+'helper_query_probe.json',out);print(out,flush=True)
