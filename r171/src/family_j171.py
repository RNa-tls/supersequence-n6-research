"""Small b1/B1 shared-family experiment. Timing separate; no historical hints."""
import argparse, hashlib, time
from production_j171 import *

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['measure','verify-helper','invested','reduce-helper']);a=p.parse_args()
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    cert={k:v[0] for k,v in dep.items()};members=['1|4|5|1|0|0','1|6|3|1|0|0','1|8|1|1|0|0']
    out=[];tim=[]
    if a.mode=='measure':
        for c in members:
            k=key(c);g=Telemetry(cert,2_000_000,f['J'][c]+1);t=time.monotonic();toks,err=g.build(k,f['J'][c])
            out.append(dict(cell=c,J=f['J'][c],nodes=g.nodes,completed=toks is not None,cap=2_000_000,detail=err,helpers_used=dict(g.used)))
            tim.append(dict(task=c,seconds=time.monotonic()-t));del toks
            save(PREFIX+'family_B1_direct_codex_171.json',dict(rows=out,environment_sha256=canonical(env),complete=len(out)==len(members)))
            print('DIRECT',c,out[-1]['completed'],g.nodes,flush=True)
        # Only one rung is attempted; do not pre-build a ladder.
        k=key('1|2|5|1|0|0');t=time.monotonic();g=G.Engine(cert,1_000_000);cap,err=g.discover(k)
        result=dict(cell=text(k),discovery_nodes=g.nodes,discovered_cap=cap,detail=err,node_cap=1_000_000)
        if cap is not None:
            g2=G.Engine(cert,1_000_000);toks,err=g2.build(k,cap);result.update(build_nodes=g2.nodes,detail=err)
            if toks is not None:
                path=PREFIX+'extree_J_B1_helper_codex_171.txt.gz';assert not (ROOT/path).exists()
                plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(k,cap,toks)])
                result.update(path=path,container_sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest(),status='AWAITING_DUAL_VERIFICATION')
        save(PREFIX+'family_B1_helper_codex_171.json',result)
        tim.append(dict(task='helper',seconds=time.monotonic()-t))
        save(PREFIX+'family_B1_timing_codex_171.json',dict(seconds_noncanonical=tim))
        print('HELPER',result,flush=True)
    elif a.mode=='verify-helper':
        m=load(PREFIX+'family_B1_helper_codex_171.json');path=m['path'];assert sha(path)==m['container_sha256']
        aa=A.verify(path);assert aa['ok'];print('helper A',aa['nodes'],flush=True)
        bb=B.verify_any(path);assert bb['ok'];assert aa['nodes']==bb['nodes']==bb['hist_checks']==m['build_nodes']
        aa.pop('certified',None);bb.pop('certified',None)
        save(PREFIX+'family_B1_helper_verified_codex_171.json',dict(A=aa,B=bb,versions={p:sha(p) for p in VERSIONS},histogram_mismatches=0,status='DUAL_ACCEPTED',certificate_sha256=sha(path)))
    elif a.mode=='invested':
        m=load(PREFIX+'family_B1_helper_codex_171.json');v=load(PREFIX+'family_B1_helper_verified_codex_171.json');assert v['status']=='DUAL_ACCEPTED' and v['certificate_sha256']==sha(m['path'])
        assert v['versions']=={p:sha(p) for p in VERSIONS}
        cert[key(m['cell'])]=m['discovered_cap']
        refs.append((m['container_sha256'],m['plain_sha256'],m['path']))
        dep[key(m['cell'])]=(m['discovered_cap'],m['plain_sha256'],m['path'])
        for c in members:
            k=key(c);g=Telemetry(cert,2_000_000,f['J'][c]+1);t=time.monotonic();toks,err=g.build(k,f['J'][c])
            row=dict(cell=c,J=f['J'][c],nodes=g.nodes,completed=toks is not None,cap=2_000_000,detail=err,helpers_used=dict(g.used))
            if toks is not None:
                path=PREFIX+'extree_J_B1_target_'+c.replace('|','_')+'_codex_171.txt.gz';assert not (ROOT/path).exists()
                plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(k,f['J'][c],toks)])
                row.update(path=path,sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest())
            del toks;out.append(row);tim.append(dict(task=c,seconds=time.monotonic()-t))
            save(PREFIX+'family_B1_invested_codex_171.json',dict(rows=out,complete=len(out)==len(members)))
            print('INVESTED',c,row['completed'],g.nodes,flush=True)
        save(PREFIX+'family_B1_invested_timing_codex_171.json',dict(seconds_noncanonical=tim))
    else:
        # Existing equal-capacity d2/d3 rungs: measure substitution, exclude the
        # already-proved target itself (otherwise root domination trivializes it).
        k=key('1|5|10|0|0|0');cert.pop(k,None)
        for name,drop in [('both',None),('drop_d2',key('1|2|10|0|0|0'))]:
            cc=dict(cert)
            if drop:cc.pop(drop)
            g=Telemetry(cc,1_000_000,130);toks,err=g.build(k,129)
            out.append(dict(case=name,nodes=g.nodes,completed=toks is not None,detail=err,
                            trace_sha256=hashlib.sha256(' '.join(toks or []).encode()).hexdigest(),helpers_used=dict(g.used)))
            print(name,g.nodes,flush=True)
        save(PREFIX+'helper_substitution_codex_171.json',dict(rows=out,equal_complete_traces=all(r['completed'] for r in out) and out[0]['trace_sha256']==out[1]['trace_sha256'],scope='this target at J=129 in the frozen environment, not an additive-benefit claim'))

if __name__=='__main__':main()
