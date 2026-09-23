"""Observation-only E-family bottleneck census, with unchanged-search control."""
from bulk_j171 import *


class Probe(G.Engine):
    def __init__(self,cert,limit,bound):
        super().__init__(cert,limit);self.bound=bound;self.failed=collections.Counter()
    def ub(self,*k):
        value=super().ub(*k)
        ports=sys._getframe(1).f_locals['ports']
        needed=self.bound+1-ports
        if value>needed:self.failed[(k,needed,value)]+=1
        return value


if __name__=='__main__':
    f,refs,dep,env,base=initial();m=load(MAN)
    refs,dep=add_accepted(refs,m['accepted'])
    cert={k:v[0] for k,v in dep.items()};cell=key('1|6|3|0|1|0');bound=f['J'][text(cell)]
    probe=Probe(cert,100000,bound);t,e=probe.build(cell,bound)
    control=G.Engine(cert,100000);ct,ce=control.build(cell,bound)
    assert (t,e,probe.nodes)==(ct,ce,control.nodes)
    out=dict(status='BOUNDED_DIAGNOSTIC_NOT_A_CERTIFICATE',cell=text(cell),bound=bound,
        probe_nodes=probe.nodes,control_nodes=control.nodes,inserted_helpers=[],
        control_equivalent=True,predecessor_set_sha256=canonical([(text(k),v) for k,v in sorted(dep.items())]),
        source_sha256=sha('r171/src/probe_bulk_e_queries_j171.py'),
        generator_sha256=sha('r168/src/gen168.py'),
        rows=[dict(query=text(k),required_upper=u,current_upper=v,count=n)
              for (k,u,v),n in probe.failed.most_common()])
    atomic(BASE+'helper_e_query_probe.json',out)
    print(json.dumps({**{k:v for k,v in out.items() if k!='rows'},'top_queries':out['rows'][:12]},indent=1))
