"""Bounded, dependency-pinned Round171 production across every remaining J cell.

No capacity discovery, historical table, or speculative predecessor insertion.
Each search cap is a restart, never an exhaustion claim. New proof trees are
promoted only by fresh A/B checks and equal per-cell node counts.
"""
from production_j171 import *
from helper_decision_j171 import setup
import concurrent.futures as cf
import functools, os, ctypes

BASE='r171/certs/bulk_j171/'
MAN=BASE+'manifest.json'
DRIVER='r171/src/bulk_j171.py'

def atomic(rel,value):
    p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,sort_keys=True,indent=1)+'\n',encoding='utf-8')
    os.replace(tmp,p)

def peak_memory():
    class PMC(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ['peak','working','peakPaged','paged','peakNonpaged','nonpaged','pagefile','peakPagefile']]
    if os.name!='nt':return None
    p=PMC();p.cb=ctypes.sizeof(p)
    k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
    fn=ctypes.windll.psapi.GetProcessMemoryInfo
    fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(PMC),ctypes.c_ulong]
    assert fn(k.GetCurrentProcess(),ctypes.byref(p),p.cb)
    return p.peak

def validate_dag(refs):
    """Header/closure checks are explicit even when a verifier reuses trust."""
    contents={};dep={}
    for cs,ps,rel in refs:
        raw=(ROOT/rel).read_bytes();plain=gzip.decompress(raw).decode()
        assert hashlib.sha256(raw).hexdigest()==cs
        assert hashlib.sha256(plain.encode()).hexdigest()==ps
        rr,dd,own=B.scan_headers(plain);closure={}
        for ref in rr:
            prior=contents[ref[-1]]
            assert prior[0]==ref[0]
            if len(ref)==3:assert prior[1]==ref[1]
            closure.update(prior[2])
        for cell,cap,want,path in dd:
            assert any(x[-1]==path for x in rr)
            assert contents[path][1]==want and contents[path][2].get(cell)==cap
            closure[cell]=cap
        for cell,cap in own:
            closure[cell]=cap
            if cell not in dep or cap<dep[cell][0]:dep[cell]=(cap,ps,rel)
        contents[rel]=(cs,ps,closure)
    return dep

@functools.lru_cache(None)
def initial():
    f,refs,dep,env,h,direct,cert=setup()
    hv=load(PREFIX+'family_B1_upper_verified_codex_171.json')
    assert [(x['cell'],x['cap'],x['nodes']) for x in hv['A']['rows']]==[(x['cell'],x['cap'],x['nodes']) for x in hv['B']['rows']]==[(h['cell'],64,122892)]
    r=load(PREFIX+'helper_decision_codex_171.json');m=r['certificate']
    assert r['verdict']=='ROUND171_HELPER_TARGET_CERTIFIED' and r['histogram_mismatches']==0
    assert r['driver_sha256']==sha('r171/src/helper_decision_j171.py')
    assert r['environment_sha256']==canonical(env)
    assert r['verifier_A']['ok'] and r['verifier_B']['ok']
    assert r['verifier_A']['nodes']==r['verifier_B']['nodes']==r['verifier_B']['hist_checks']==m['nodes']
    assert [(x['cell'],x['cap'],x['nodes']) for x in r['verifier_A']['rows']]==[(x['cell'],x['cap'],x['nodes']) for x in r['verifier_B']['rows']]==[(r['selected'],f['J'][r['selected']],m['nodes'])]
    assert sha(m['path'])==m['sha256']==r['verifier_A']['sha256']==r['verifier_B']['sha256']
    refs=refs+[(m['sha256'],m['plain_sha256'],m['path'])]
    dep=validate_dag(refs)
    assert dep[key(h['cell'])][0]==64 and dep[key(r['selected'])][0]==f['J'][r['selected']]
    B.TRUST[m['sha256']]={'report':sha(PREFIX+'helper_decision_codex_171.json'),'versions':env['versions']}
    backed={text(k) for k,v in dep.items() if text(k) in f['J'] and v[0]<=f['J'][text(k)]}
    assert len(f['J'])==35 and len(backed)==6 and len(set(f['J'])-backed)==29
    assert backed==set(load(PREFIX+'production_progress_codex_171.json')['backed_cells'])
    return f,refs,dep,env,backed

def add_accepted(refs,records):
    refs=list(refs)
    for r in records:
        assert r['status']=='CERTIFIED' and r['histogram_mismatches']==0
        assert r['versions']=={p:sha(p) for p in VERSIONS}
        assert r['driver_sha256']==sha(DRIVER)
        m=r['certificate'];assert sha(m['path'])==m['sha256']
        aa,bb=r['A'],r['B']
        assert aa['ok'] and bb['ok'] and aa['sha256']==bb['sha256']==m['sha256']
        assert aa['nodes']==bb['nodes']==bb['hist_checks']==r['nodes']
        assert [(x['cell'],x['cap'],x['nodes']) for x in aa['rows']]==[(x['cell'],x['cap'],x['nodes']) for x in bb['rows']]==[(r['cell'],r['bound'],r['nodes'])]
        refs.append((m['sha256'],m['plain_sha256'],m['path']))
    dep=validate_dag(refs)
    for r in records:B.TRUST[r['certificate']['sha256']]={'report':canonical(r),'versions':r['versions']}
    return refs,dep

def job(spec):
    f,refs,dep,env,backed=initial()
    assert spec['driver_sha256']==sha(DRIVER)
    refs,dep=add_accepted(refs,spec['accepted'])
    assert spec['bound']==f['J'][spec['cell']]
    rel=BASE+'jobs/'+spec['id']+'.json';tim=BASE+'timings/'+spec['id']+'.json'
    assert not (ROOT/rel).exists()
    row=dict(id=spec['id'],cell=spec['cell'],bound=spec['bound'],target=spec['bound']+1,
        cap=spec['cap'],status='GENERATING',driver_sha256=sha(DRIVER),versions=env['versions'],
        predecessor_refs=refs,predecessor_set_sha256=canonical([(text(k),v) for k,v in sorted(dep.items())]),
        predecessor_count=len(dep))
    atomic(rel,row);start=time.monotonic()
    g=Telemetry({k:v[0] for k,v in dep.items()},spec['cap'],spec['bound']+1)
    toks,err=g.build(key(spec['cell']),spec['bound'])
    row.update(nodes=g.nodes,detail=err,helpers_used=dict(g.used),fallback_fraction=g.fallback/g.calls if g.calls else None,
        first_useful_prune_depth=g.first_useful)
    atomic(tim,dict(generation_seconds=time.monotonic()-start,peak_memory_bytes=peak_memory()))
    if toks is None:
        row['status']='DEFERRED' if 'node cap' in (err or '') else 'FAILED_INVALID'
        atomic(rel,row);return row
    path=BASE+'proofs/'+spec['id']+'.txt.gz';(ROOT/path).parent.mkdir(parents=True,exist_ok=True)
    assert not (ROOT/path).exists()
    plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(key(spec['cell']),spec['bound'],toks)])
    row['certificate']=dict(path=path,sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest())
    row['status']='PROVISIONALLY_GENERATED';atomic(rel,row);del plain,toks,g
    t=time.monotonic();aa=A.verify(path);row['A']=aa;aa.pop('certified',None)
    assert aa['ok'];row['status']='VERIFIER_A_ACCEPT';atomic(rel,row)
    ta=time.monotonic()-t;t=time.monotonic();bb=B.verify_any(path);row['B']=bb;bb.pop('certified',None)
    assert bb['ok'];row['status']='VERIFIER_B_ACCEPT';atomic(rel,row)
    assert aa['nodes']==bb['nodes']==bb['hist_checks']==row['nodes']
    assert [(x['cell'],x['cap'],x['nodes']) for x in aa['rows']]==[(x['cell'],x['cap'],x['nodes']) for x in bb['rows']]==[(row['cell'],row['bound'],row['nodes'])]
    row.update(status='CERTIFIED',histogram_mismatches=0);atomic(rel,row)
    timing=load(tim);timing.update(verifier_A_seconds=ta,verifier_B_seconds=time.monotonic()-t,peak_memory_bytes=peak_memory());atomic(tim,timing)
    return row

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def plan():
    assert git('rev-parse','HEAD')=='a636fd0584b129f50f769659aecd450d2bf9232f'
    assert not (ROOT/MAN).exists()
    f,refs,dep,env,backed=initial();pilots={r['cell']:r for r in load(PREFIX+'production_pilots_codex_171.json')['rows']}
    rows=[]
    for c in sorted(set(f['J'])-backed,key=key):
        k=key(c);p=pilots[c]
        dependencies=[d for d in f['J'] if d!=c and all(a>=b for a,b in zip(key(d),k)) and f['J'][d]<=f['J'][c]]
        rows.append(dict(cell=c,bound=f['J'][c],target=f['J'][c]+1,status='PLANNED',family=family(k),
            current_root_P1_query=text((k[0],k[1]+5*k[0],*k[2:])),
            current_genuine_exact_bound=dep[k][0] if k in dep else None,
            prior_cap=p['node_cap'],prior_nodes=p['search_nodes'],prior_fallback=p['fallback_fraction'],
            useful_P1_dominators=p['helpers_used'],possible_required_predecessors=dependencies,
            helper_policy='No speculative helper; use accepted DAG, reconsider investment only after measured bottlenecks.',
            bridge_policy='No new bridge rule; only consequences already encoded in accepted predecessors.',attempts=[]))
    out=dict(base_commit=git('rev-parse','HEAD'),driver_sha256=sha(DRIVER),J_sha256=f['J_sha256'],
        versions=env['versions'],initial_backed=sorted(backed),initial_refs=refs,targets=rows,accepted=[],
        certified=6,remaining=29,actual_max_concurrency=0,status='PLANNED',
        cap_policy='Each capped restart is DEFERRED; never absence or proof. Generation uses J+1 only.')
    atomic(MAN,out);print('PLANNED 29; certified 6/35',flush=True)

def checkpoint(m,new):
    atomic(MAN,m)
    paths=[MAN]
    for r in new:
        paths += [BASE+'jobs/'+r['id']+'.json',BASE+'timings/'+r['id']+'.json']
        if 'certificate' in r:paths.append(r['certificate']['path'])
    git('add','--',*paths)
    git('-c','core.autocrlf=false','commit','-m',f"Round 171 bulk: {m['certified']}/35 certified; {len(new)} measured jobs checkpointed")
    commit=git('rev-parse','HEAD')
    for r in new:
        if r['status']=='CERTIFIED':
            next(t for t in m['targets'] if t['cell']==r['cell'])['certificate_commit']=commit
    atomic(MAN,m);git('add','--',MAN)
    if git('diff','--cached','--name-only'):
        git('-c','core.autocrlf=false','commit','-m','Round 171 bulk: pin certificate checkpoint commits')
    git('push','origin','codex/round171-joint-audit')
    assert git('ls-remote','origin','refs/heads/codex/round171-joint-audit').split()[0]==git('rev-parse','HEAD')

def run(cap,workers):
    m=load(MAN);assert m['driver_sha256']==sha(DRIVER)
    # Reconcile the last checkpoint before dispatch; do not duplicate attempts.
    pending=[t for t in m['targets'] if t['status']!='CERTIFIED' and not any(a['cap']>=cap and a['environment_count']==len(m['accepted']) for a in t['attempts'])]
    pending.sort(key=lambda t:(-len(t['possible_required_predecessors']),t['prior_fallback'],key(t['cell'])))
    m['status']='RUNNING';m['actual_max_concurrency']=max(workers,m['actual_max_concurrency']);atomic(MAN,m)
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        active={};dirty=[]
        while pending or active:
            while pending and len(active)<workers:
                t=pending.pop(0);id=t['cell'].replace('|','_')+f'_c{cap}_e{len(m["accepted"])}'
                spec=dict(id=id,cell=t['cell'],bound=t['bound'],cap=cap,accepted=list(m['accepted']),driver_sha256=m['driver_sha256'])
                t['status']='GENERATING';atomic(MAN,m);active[pool.submit(job,spec)]=(t,len(m['accepted']))
                print('START',t['cell'],cap,'predecessor additions',len(m['accepted']),flush=True)
            done,_=cf.wait(active,timeout=30,return_when=cf.FIRST_COMPLETED)
            if not done:print('HEARTBEAT active',len(active),'waiting',len(pending),'certified',m['certified'],flush=True)
            for future in done:
                t,n=active.pop(future)
                try:r=future.result()
                except BaseException as e:
                    m['status']='VERIFICATION_FAILURE';m['error']=repr(e);atomic(MAN,m);raise
                t['status']=r['status'];t['attempts'].append(dict(id=r['id'],cap=cap,nodes=r['nodes'],status=r['status'],environment_count=n))
                if r['status']=='FAILED_INVALID':m['status']='VERIFICATION_FAILURE';atomic(MAN,m);raise RuntimeError(r)
                if r['status']=='CERTIFIED':m['accepted'].append(r);m['certified']+=1;m['remaining']-=1
                assert m['certified']==6+len(m['accepted']) and m['certified']+m['remaining']==35
                dirty.append(r);atomic(MAN,m);print('RESULT',r['cell'],r['status'],r['nodes'],'total',m['certified'],flush=True)
                if r['status']=='CERTIFIED' or len(dirty)>=3:checkpoint(m,dirty);dirty=[]
        m['status']='PASS_FINISHED';atomic(MAN,m)
        if dirty:checkpoint(m,dirty)
    print('PASS FINISHED',m['certified'],'/35',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['plan','run']);p.add_argument('--cap',type=int,default=1000000);p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    if a.mode=='plan':plan()
    else:run(a.cap,a.workers)
