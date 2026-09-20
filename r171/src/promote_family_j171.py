"""Fresh dual replay, then promote completed J targets from the B1 trial."""
import time
from production_j171 import *

def main():
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    h=load(PREFIX+'family_B1_helper_codex_171.json');hv=load(PREFIX+'family_B1_helper_verified_codex_171.json')
    assert hv['status']=='DUAL_ACCEPTED' and hv['versions']=={p:sha(p) for p in VERSIONS}
    assert sha(h['path'])==hv['certificate_sha256']
    assert hv['A']['nodes']==hv['B']['nodes']==hv['B']['hist_checks']==h['build_nodes']
    B.TRUST[sha(h['path'])]={'versions':hv['versions'],'dual_report_sha256':sha(PREFIX+'family_B1_helper_verified_codex_171.json')}
    p=load(PREFIX+'family_B1_invested_codex_171.json');assert p['complete']
    targets=[r for r in p['rows'] if r['completed']][:2]
    assert targets,'no proof to promote'
    out=[];tim=[]
    for r in targets:
        path=r['path'];assert r['sha256']==sha(path)
        assert r['J']==f['J'][r['cell']]
        t=time.monotonic();aa=A.verify(path);assert aa['ok'];print('A accepted',r['cell'],aa['nodes'],flush=True)
        bb=B.verify_any(path);assert bb['ok'];print('B accepted',r['cell'],bb['nodes'],flush=True)
        assert aa['nodes']==bb['nodes']==bb['hist_checks']==r['nodes']
        assert [(x['cell'],x['cap'],x['nodes']) for x in aa['rows']]==[(x['cell'],x['cap'],x['nodes']) for x in bb['rows']]
        aa.pop('certified',None);bb.pop('certified',None)
        out.append(dict(cell=r['cell'],cap=r['J'],path=path,container_sha256=sha(path),plain_sha256=r['plain_sha256'],A=aa,B=bb,histogram_mismatches=0))
        tim.append(dict(cell=r['cell'],seconds=time.monotonic()-t))
    J={key(k):v for k,v in f['J'].items()};backed={k for k,v in dep.items() if k in J and v[0]<=J[k]}
    backed|={key(r['cell']) for r in out}
    dossier=[]
    for row in f['dossier']:
        row=dict(row)
        if key(row['cell']) in backed:
            row['value_role']='GENUINELY_BACKED_VALUE';row['historical_dependency_status']='REPLACED'
            for c in out:
                if c['cell']==row['cell']:row['current_genuine_certified_bound']=c['cap'];row['certificate']=c['path']
        dossier.append(row)
    envversions={p:sha(p) for p in VERSIONS+['r171/src/family_j171.py','r171/src/promote_family_j171.py']}
    result=dict(status='DUAL_ACCEPTED',new_targets=out,jointly_usable=len(backed),remaining=35-len(backed),
                J_sha256=f['J_sha256'],J_census=census(J),dossier=dossier,
                target_vs_proof='remaining J values are planning assumptions, not genuinely backed upper bounds',
                source_versions=envversions,environment_sha256=canonical(env),
                helper_report_sha256=sha(PREFIX+'family_B1_helper_verified_codex_171.json'),
                full_independence=len(backed)==35,verdict='ROUND171_J_PRODUCTION_PROGRESS')
    save(PREFIX+'family_B1_promotion_codex_171.json',result)
    save(PREFIX+'family_B1_promotion_timing_codex_171.json',dict(seconds_noncanonical=tim,canonical_sha256=canonical(result)))
    print('JOINTLY USABLE',len(backed),'/35',flush=True)

if __name__=='__main__':main()
