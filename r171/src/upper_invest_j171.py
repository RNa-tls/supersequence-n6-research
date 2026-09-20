"""Validate the one shallow upper helper, then measure only its chosen family."""
from production_j171 import *

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify-helper','measure','promote']);p.add_argument('--cap',type=int,default=2000000);a=p.parse_args()
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    h=next(r for r in load(PREFIX+'family_B1_upper_trials_codex_171.json')['rows'] if r['complete'])
    path=h['path'];assert sha(path)==h['sha256']
    if a.mode=='verify-helper':
        aa=A.verify(path);assert aa['ok'];print('A helper',aa['nodes'],flush=True)
        bb=B.verify_any(path);assert bb['ok'];assert aa['nodes']==bb['nodes']==bb['hist_checks']==h['nodes']
        aa.pop('certified',None);bb.pop('certified',None)
        save(PREFIX+'family_B1_upper_verified_codex_171.json',dict(A=aa,B=bb,source_versions={p:sha(p) for p in VERSIONS},certificate_sha256=sha(path),status='DUAL_ACCEPTED',histogram_mismatches=0,J_census=census({key(k):v for k,v in f['J'].items()})))
        print('B helper',bb['nodes'],flush=True);return
    hv=load(PREFIX+'family_B1_upper_verified_codex_171.json');assert hv['status']=='DUAL_ACCEPTED' and hv['certificate_sha256']==sha(path)
    assert hv['source_versions']=={p:sha(p) for p in VERSIONS}
    assert hv['A']['nodes']==hv['B']['nodes']==hv['B']['hist_checks']==h['nodes']
    B.TRUST[sha(path)]={'versions':hv['source_versions'],'report_sha256':sha(PREFIX+'family_B1_upper_verified_codex_171.json')}
    cert={k:v[0] for k,v in dep.items()};cert[key(h['cell'])]=h['proposed_upper_bound']
    refs.append((h['sha256'],h['plain_sha256'],path));dep[key(h['cell'])]=(h['proposed_upper_bound'],h['plain_sha256'],path)
    if a.mode=='measure':
        out=[];tim=[]
        for c in ['1|4|5|1|0|0','1|6|3|1|0|0','1|8|1|1|0|0']:
            k=key(c);g=Telemetry(cert,a.cap,f['J'][c]+1);t=time.monotonic();toks,err=g.build(k,f['J'][c])
            r=dict(cell=c,J=f['J'][c],completed=toks is not None,nodes=g.nodes,node_cap=a.cap,detail=err,helpers_used=dict(g.used))
            if toks is not None:
                dst=PREFIX+'extree_J_upper_target_'+c.replace('|','_')+'_codex_171.txt.gz';assert not (ROOT/dst).exists()
                plain=G.write_batch(ROOT/dst,refs,[(k,*v) for k,v in sorted(dep.items())],[(k,f['J'][c],toks)])
                r.update(path=dst,sha256=sha(dst),plain_sha256=hashlib.sha256(plain.encode()).hexdigest())
            del toks;out.append(r);tim.append(dict(cell=c,seconds=time.monotonic()-t))
            save(PREFIX+'family_B1_upper_invested_codex_171.json',dict(rows=out,complete=len(out)==3,helper=h['cell'],helper_sha256=sha(path),environment_sha256=canonical(env)))
            save(PREFIX+'family_B1_upper_invested_timing_codex_171.json',dict(seconds_noncanonical=tim))
            print('UPPER INVESTED',c,r['completed'],g.nodes,flush=True)
        return
    runs=load(PREFIX+'family_B1_upper_invested_codex_171.json');assert runs['complete']
    out=[]
    for r in runs['rows']:
        if not r['completed']:continue
        assert r['J']==f['J'][r['cell']] and r['sha256']==sha(r['path'])
        aa=A.verify(r['path']);assert aa['ok'];print('A target',r['cell'],aa['nodes'],flush=True)
        bb=B.verify_any(r['path']);assert bb['ok'];assert aa['nodes']==bb['nodes']==bb['hist_checks']==r['nodes']
        aa.pop('certified',None);bb.pop('certified',None)
        out.append(dict(cell=r['cell'],cap=r['J'],path=r['path'],A=aa,B=bb,sha256=sha(r['path'])))
        print('B target',r['cell'],bb['nodes'],flush=True)
    J={key(k):v for k,v in f['J'].items()};backed={k for k,v in dep.items() if k in J and v[0]<=J[k]}|{key(r['cell']) for r in out}
    save(PREFIX+'production_progress_codex_171.json',dict(new_load_bearing_certificates=out,jointly_usable=len(backed),remaining=35-len(backed),new_helpers=1,helper_counts_as_load_bearing=False,J_sha256=f['J_sha256'],J_census=census(J),source_versions={p:sha(p) for p in VERSIONS},backed_cells=sorted(map(text,backed)),full_independence=False,verdict='ROUND171_J_PRODUCTION_PROGRESS' if out else 'ROUND171_J_PRODUCTION_BLOCKED'))

if __name__=='__main__':main()
