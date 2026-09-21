"""One-target measured decision; unchanged generator, explicit capped restarts."""
from production_j171 import *

OUT = PREFIX+'helper_decision_codex_171.json'
MEMBERS = ['1|4|5|1|0|0','1|6|3|1|0|0','1|8|1|1|0|0']
HK = key('1|1|5|1|0|0')

class Meter(G.Engine):
    def __init__(self, cert, cap, target, direct):
        super().__init__(cert,cap)
        self.target=target; self.control=G.Engine(direct,0)
        self.calls=0;self.fallback=0;self.p_leaves=0;self.new_p=0
        self.first=None;self.used=collections.Counter();self.misses=collections.Counter()
        self.shapes={}
    def ub(self,*k):
        v=super().ub(*k);self.calls+=1
        loc=sys._getframe(1).f_locals;ports=loc['ports'];fb=G.R.UBFALL+sum(k[2:5])
        self.fallback+=v==fb
        if ports+v-1<self.target:
            self.p_leaves+=1
            if v<fb:
                winner=min(c for c,x in self.cert.items() if x==v and all(a>=b for a,b in zip(c,k)))
                self.used[text(winner)]+=1
            if ports+self.control.ub(*k)-1>=self.target:
                self.new_p+=1
                if self.first is None:self.first=ports-1
        else:
            # Count only (p) failures, not a claim that this entire node is hard.
            z=(k,ports,v,self.target-ports)
            self.misses[z]+=1
            if z not in self.shapes:
                self.shapes[z]=dict(endpoint=loc['v'],current_orbit=loc['corb'],
                    opened_orbits=len(loc['phm']),covered_hexagons=len(loc['hexc']),
                    deficit=loc['deficit'],used_A=loc['au'],used_B=loc['bu'])
        return v
    def report(self):
        miss=[]
        for (k,ports,v,needed),n in self.misses.most_common(12):
            near=sorted((sum(max(0,b-a) for a,b in zip(c,k)),x,text(c)) for c,x in self.cert.items())[:5]
            miss.append(dict(query=text(k),d_star=k[1],ports=ports,current_upper=v,
                sufficient_upper=needed,count=n,analytic_fallback=v==G.R.UBFALL+sum(k[2:5]),
                exemplar=self.shapes[(k,ports,v,needed)],nearest_genuine_helpers=near))
        return dict(ub_calls=self.calls,fallback_calls=self.fallback,
            fallback_fraction=self.fallback/self.calls if self.calls else None,
            useful_p_leaf_count=self.p_leaves,useful_genuine_helper_prunes=sum(self.used.values()),
            new_helper_essential_p_leaves=self.new_p,first_new_helper_prune_depth=self.first,
            helpers_used=dict(self.used),unpruned_query_diagnostics=miss)

def setup():
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    h=next(r for r in load(PREFIX+'family_B1_upper_trials_codex_171.json')['rows'] if r['complete'])
    v=load(PREFIX+'family_B1_upper_verified_codex_171.json')
    assert key(h['cell'])==HK and h['proposed_upper_bound']==64
    assert v['status']=='DUAL_ACCEPTED' and h['sha256']==v['certificate_sha256']==sha(h['path'])
    assert v['source_versions']=={p:sha(p) for p in VERSIONS}
    assert v['A']['nodes']==v['B']['nodes']==v['B']['hist_checks']==122892
    B.TRUST[sha(h['path'])]={'versions':v['source_versions'],'report_sha256':sha(PREFIX+'family_B1_upper_verified_codex_171.json')}
    direct={k:x[0] for k,x in dep.items()};cert=dict(direct);cert[HK]=64
    refs.append((h['sha256'],h['plain_sha256'],h['path']))
    dep[HK]=(64,h['plain_sha256'],h['path'])
    return f,refs,dep,env,h,direct,cert

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['probe','escalate','verify']);a=p.parse_args()
    f,refs,dep,env,h,direct,cert=setup()
    timings=[]
    def run(c,cap,invested):
        t=time.monotonic();g=Meter(cert if invested else direct,cap,f['J'][c]+1,direct)
        toks,err=g.build(key(c),f['J'][c])
        assert toks is not None or 'node cap' in (err or ''),(c,err)
        row=dict(cell=c,J=f['J'][c],target=f['J'][c]+1,with_helper=invested,
            cap=cap,nodes=g.nodes,status='TREE_BUILT' if toks is not None else 'DEFERRED',detail=err,**g.report())
        timings.append(dict(cell=c,cap=cap,with_helper=invested,seconds=time.monotonic()-t))
        save(PREFIX+'helper_decision_timing_codex_171.json',dict(noncanonical=timings))
        print(c,cap,invested,row['status'],g.nodes,'fallback',row['fallback_fraction'],'new_p',g.new_p,flush=True)
        return row,toks
    if a.mode=='probe':
        assert not (ROOT/OUT).exists()
        out=dict(base_commit='424953a3b86f3361baf4e059e2f784dd1feba6c5',environment_sha256=canonical(env),
            driver_sha256=sha('r171/src/helper_decision_j171.py'),helper_investment=122892,probe=[],stages=[],
            semantics='Each cap is a deterministic restart; cumulative actual node work includes repeated prefixes.')
        old=load(PREFIX+'family_B1_upper_invested_codex_171.json')['rows']
        for c in MEMBERS:
            d,_=run(c,200000,False);r,_=run(c,200000,True)
            prior=next(x for x in old if x['cell']==c)
            assert r['nodes']==prior['nodes'] and r['helpers_used']==prior['helpers_used']
            out['probe'].append(dict(cell=c,direct=d,helper=r));save(OUT,out)
        eligible=[x for x in out['probe'] if x['helper']['new_helper_essential_p_leaves']>0]
        # No measured effect is not evidence of global ineffectiveness. Prefer
        # actual measured effect, then the user's lexicographic priority.
        pool=eligible or out['probe']
        best=min(pool,key=lambda x:(x['helper']['fallback_fraction'],-x['helper']['new_helper_essential_p_leaves'],
            x['helper']['first_new_helper_prune_depth'] if x['helper']['first_new_helper_prune_depth'] is not None else 10**9,x['cell']))
        out.update(selected=best['cell'],selection='Positive counterfactual helper-prune effect first; then fallback, useful count, first depth, stable ID. Total cost unknown from caps.',probe_complete=True)
        save(OUT,out);return
    out=load(OUT);assert out['driver_sha256']==sha('r171/src/helper_decision_j171.py')
    c=out['selected']
    if a.mode=='escalate':
        assert out['probe_complete'] and not out['stages']
        for cap in [500000,1000000,2000000,5000000]:
            r,toks=run(c,cap,True);out['stages'].append(r)
            out['cumulative_escalation_nodes']=sum(x['nodes'] for x in out['stages'])
            if toks is not None:
                path=PREFIX+'extree_J_helper_decision_codex_171.txt.gz';assert not (ROOT/path).exists()
                plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(key(c),f['J'][c],toks)])
                out['certificate']=dict(path=path,sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest(),nodes=r['nodes'])
            save(OUT,out)
            if toks is not None:break
        # Reuse the committed direct 2M run; extend only when needed for economics.
        old=load(PREFIX+'family_B1_direct_codex_171.json');assert old['environment_sha256']==canonical(env)
        control=next(r for r in old['rows'] if r['cell']==c);assert control['J']==f['J'][c]
        out['prior_direct_control']=control
        if 'certificate' not in out or out['certificate']['nodes']+122892>=control['cap']:
            cap=5000000 if 'certificate' not in out else min(5000000,out['certificate']['nodes']+122893)
            r,toks=run(c,cap,False);out['direct_control']=r
            # A complete control trace is cost evidence, not a promoted proof.
            if toks is not None:out['direct_control']['trace_sha256']=hashlib.sha256(' '.join(toks).encode()).hexdigest()
        out['measurement_complete']=True;save(OUT,out);return
    assert out['measurement_complete']
    if 'certificate' not in out:
        out.update(jointly_usable=5,remaining=30,verification='NO_NEW_PRODUCTION_TREE',
            verdict='ROUND171_HELPER_GAIN_BUT_DEFERRED' if any(r['new_helper_essential_p_leaves'] for r in out['stages']) else 'ROUND171_HELPER_NO_GAIN')
        save(OUT,out);return
    m=out['certificate'];assert sha(m['path'])==m['sha256']
    aa=A.verify(m['path']);assert aa['ok'];print('A accepted',aa['nodes'],flush=True)
    bb=B.verify_any(m['path']);assert bb['ok'];print('B accepted',bb['nodes'],flush=True)
    assert aa['nodes']==bb['nodes']==bb['hist_checks']==m['nodes']
    assert [(r['cell'],r['cap'],r['nodes']) for r in aa['rows']]==[(r['cell'],r['cap'],r['nodes']) for r in bb['rows']]==[(c,f['J'][c],m['nodes'])]
    aa.pop('certified',None);bb.pop('certified',None)
    out.update(verifier_A=aa,verifier_B=bb,histogram_mismatches=0,jointly_usable=6,remaining=29,
        independence_restricted_J_census=census({key(k):v for k,v in f['J'].items()}),
        verdict='ROUND171_HELPER_TARGET_CERTIFIED')
    save(OUT,out)

if __name__=='__main__':main()
