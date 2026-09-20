"""Round171 J-target checkpoints. No historical capacity hints for generation."""
import argparse, collections, gzip, hashlib, json, subprocess, sys, time
from pathlib import Path
from joint_endpoint_codex import ROOT, load, sha, key, text, save, ClosedSystem
sys.path.insert(0,str(ROOT/'r168/src'))
import gen168 as G
import verify168 as B
import verifyA168 as A

PREFIX='r171/certs/'
REFS=[
 'r164/certs/extree_prefix_164.txt.gz','r166/certs/extree_batch2_166.txt.gz',
 'r166/certs/extree_batch3_166.txt.gz','r168/certs/extree_batch1_168.txt.gz',
 'r170/certs/extree_ladder_h_170.txt.gz','r170/certs/extree_ladder_a2_170.txt.gz',
 'r170/certs/extree_target_h_170.txt.gz','r170/certs/extree_target_a2_170.txt.gz',
 'r171/certs/extree_probe_b1a10_171.txt.gz','r171/certs/extree_lb_batch1_171.txt.gz',
 'r171/certs/extree_lb_b1a10_d5_171.txt.gz','r171/certs/extree_lb_b1a10_d7_171.txt.gz',
 'r171/certs/extree_lb_b1a10_d7_joint119_171.txt.gz']
VERSIONS=['r152/src/extree152.py','r164/src/routeb164.py','r168/src/verify168.py',
          'r168/src/verifyA168.py','r168/src/gen168.py','r171/src/production_j171.py']

def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def frozen():return load(PREFIX+'production_J_codex_171.json')
def family(k):
    b,d,a,bb,e,h=k
    if d==0:return 'd0_special_no_lower_d_ladder'
    return f'b{b}_H{h}_B{bb}_E{e}_AplusD{a+d}'

def environment():
    """Existing accepted proof objects only, with version-bound reuse manifest.

    Legacy acceptance is retained, not claimed as new replay. Newly added
    trust rows require both per-batch reports and equal node counts.
    """
    B.load_trust()
    gates={}
    for tag,batch in [('probe_b1a10_171',REFS[8]),('lb1_171',REFS[9]),
                      ('lb_d5_171',REFS[10]),('lb_d7_171',REFS[11]),('d7j_171',REFS[12])]:
        pa=PREFIX+'verification_a_'+tag+'.json';pb=PREFIX+'verification_b_'+tag+'.json'
        a,b=load(pa),load(pb);aa,bb=a['batches'][batch],b['batches'][batch]
        assert a['all_ok'] and b['all_ok'] and b['histogram_mismatches']==0
        assert a['extree152_sha256']==sha(VERSIONS[0]) and b['routeb164_sha256']==sha(VERSIONS[1])
        assert aa['nodes']==bb['nodes']==bb['hist_checks']
        assert aa['sha256']==bb['sha256']==sha(batch)
        gates[batch]={'reports':{pa:sha(pa),pb:sha(pb)},'nodes':aa['nodes']}
        B.TRUST[sha(batch)]={'path':batch,**gates[batch],'versions':{p:sha(p) for p in VERSIONS[:4]}}
    refs=[];dep={};contents={};man=[]
    for rel in REFS:
        raw=(ROOT/rel).read_bytes();plain=gzip.decompress(raw).decode();cs=hashlib.sha256(raw).hexdigest();ps=hashlib.sha256(plain.encode()).hexdigest()
        assert cs in B.TRUST,('unverified predecessor',rel)
        rr,dd,own=B.scan_headers(plain)
        closure={}
        for ref in rr:
            path=ref[-1];assert path in contents
            if len(ref)==3:
                wantc,wantp,_=ref
                assert contents[path][0:2]==(wantc,wantp)
            else:
                assert len(ref)==2 and contents[path][0]==ref[0]
            closure.update(contents[path][2])
        for k,v,wantp,path in dd:
            assert any(r[-1]==path for r in rr)
            assert contents[path][1]==wantp and contents[path][2].get(k)==v
            closure[k]=v
        for k,v in own:
            closure[k]=v
            if k not in dep or v<dep[k][0]:dep[k]=(v,ps,rel)
        contents[rel]=(cs,ps,closure);refs.append((cs,ps,rel))
        man.append(dict(path=rel,container_sha256=cs,plain_sha256=ps,own_cells=[{'cell':text(k),'cap':v} for k,v in own],
                        acceptance=B.TRUST[cs],gate=gates.get(rel,'LEGACY_DUAL_ACCEPTANCE_RETAINED')))
    manifest=dict(versions={p:sha(p) for p in VERSIONS},references=man,certified_cells=len(dep),
                  semantics='hash/version-bound reuse of accepted objects; new trees require fresh A/B replay')
    return refs,dep,manifest

def census(vals):
    s=ClosedSystem();s.value_of=lambda k:None
    s.chain_tab={k:None for k in s.chain_tab};s.piece_tab={k:None for k in s.piece_tab}
    assert len(vals)==35 and not set(vals)&set(s.dual_chain)
    s.apply(set(vals),values=vals);v=s.verdicts()
    rows=load(PREFIX+'joint_endpoint_codex_171.json')['rows']
    ex=[(r['t'],tuple(r['coordinates'])) for r in rows]
    eq=[(t,tuple(c)) for t,c in load(PREFIX+'joint_endpoint_codex_171.json')['equality_rows']]
    assert all(v[r]=='STRICTLY_CLOSED' for r in ex) and all(v[r]=='EQUALITY' for r in eq)
    return dict(exposed_closed=180,equality={str(r):v[r] for r in eq},tally=dict(collections.Counter(v.values())),historical_basis_fallback=False)

def freeze():
    e=load(PREFIX+'joint_endpoint_codex_171.json');d=load(PREFIX+'joint_dossier_codex_171.json')
    refs,dep,env=environment();J={key(k):v for k,v in e['J'].items()}
    rows=[];certs=[]
    for row in d['dossier']:
        k=key(row['cell']);v=dep.get(k);r=dict(row)
        r.update(coordinates=k,production_joint_bound=J[k],helper_family=family(k),
                 current_genuine_certified_bound=v[0] if v else None,
                 value_role='GENUINELY_BACKED_VALUE' if v and v[0]<=J[k] else 'PRODUCTION_TARGET_VALUE',
                 historical_dependency_status='REPLACED' if v and v[0]<=J[k] else 'REMAINS_TO_BE_REPLACED')
        rows.append(r)
    for ref in env['references']:
        for c in ref['own_cells']:
            k=key(c['cell'])
            if k in J:
                status='VALID_BUT_TOO_WEAK_FOR_J' if c['cap']>J[k] else ('STRONGER_THAN_J_REQUIRED' if c['cap']<J[k] else 'JOINTLY_USABLE')
                certs.append(dict(**c,path=ref['path'],status=status))
    backed=sum(r['value_role']=='GENUINELY_BACKED_VALUE' for r in rows);assert backed==5
    out=dict(PRODUCTION_VECTOR_J='SOUND',GLOBAL_PARETO_OPTIMUM='UNRESOLVED',
             endpoint_scope='complete I/J endpoint universe only',endpoint_sha256=sha(PREFIX+'joint_endpoint_codex_171.json'),
             removed_stop_condition='Historical pair need not occur as an active endpoint hyperedge.',
             J=e['J'],J_sha256=canonical(e['J']),census=census(J),dossier=rows,certificates=certs,
             jointly_usable=backed,remaining=35-backed,OPT=35,OPT_status='EXACT_MINIMUM_35_CONFIRMED_FROZEN',
             old_dossier_status='SUPERSEDED_FOR_PRODUCTION_TARGETS',environment_sha256=canonical(env))
    save(PREFIX+'production_environment_codex_171.json',env);save(PREFIX+'production_J_codex_171.json',out)
    print('Frozen J; backed 5/35; census 180/180.',flush=True)

class Telemetry(G.Engine):
    def __init__(self,cert,cap,target):
        super().__init__(cert,cap);self.target=target;self.calls=0;self.fallback=0;self.first_useful=None;self.used=collections.Counter();self.winners={}
    def ub(self,*k):
        v=super().ub(*k);self.calls+=1;fb=G.R.UBFALL+sum(k[2:5])
        if v==fb:self.fallback+=1
        frame=sys._getframe(1);ports=frame.f_locals['ports']
        if v<fb and ports+v-1<self.target:
            depth=ports-1
            if self.first_useful is None:self.first_useful=depth
            if k not in self.winners:
                self.winners[k]=min(c for c,x in self.cert.items() if x==v and all(a>=b for a,b in zip(c,k)))
            self.used[text(self.winners[k])]+=1
        return v

def pilots(cap):
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    cert={k:v[0] for k,v in dep.items()};want=[r for r in f['dossier'] if r['value_role']=='PRODUCTION_TARGET_VALUE']
    assert len(want)==30
    rows=[];timing=[]
    for r in want:
        k=key(r['cell']);bound=r['production_joint_bound'];t=time.monotonic();g=Telemetry(cert,cap,bound+1);toks,err=g.build(k,bound)
        completed=toks is not None
        if not completed and 'node cap' not in (err or ''):raise RuntimeError((k,err))
        rows.append(dict(cell=r['cell'],J=bound,target=bound+1,node_cap=cap,search_nodes=g.nodes,
                         completed=completed,proof_nodes=len(toks) if completed else None,
                         status='COMPLETED_UNVERIFIED_PILOT' if completed else 'DEFERRED',
                         ub_calls=g.calls,analytic_fallback_calls=g.fallback,
                         fallback_fraction=g.fallback/g.calls if g.calls else None,
                         first_useful_P1_prune_depth=g.first_useful,helpers_used=dict(g.used),family=family(k),detail=err))
        del toks
        timing.append(dict(cell=r['cell'],seconds=time.monotonic()-t))
        out=dict(J_sha256=f['J_sha256'],environment_sha256=canonical(env),node_cap=cap,planned=30,
                 rows=rows,complete=len(rows)==30,
                 cap_semantics='DEFERRED means exceeded cap in this environment only; not impossible or helper-required.',
                 node_semantics='Engine increments before cap check; aborted run reports cap+1 attempted visits.')
        save(PREFIX+'production_pilots_codex_171.json',out)
        save(PREFIX+'production_pilots_timing_codex_171.json',dict(seconds_noncanonical=timing,content_sha256=canonical(out)))
        print(r['cell'],rows[-1]['status'],g.nodes,flush=True)

def produce(cells,cap):
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    cert={k:v[0] for k,v in dep.items()};deps=[(k,*v) for k,v in sorted(dep.items())]
    trees=[];rows=[]
    for c in cells:
        k=key(c);bound=f['J'][c];g=Telemetry(cert,cap,bound+1);toks,err=g.build(k,bound)
        if toks is None:raise RuntimeError((c,err))
        trees.append((k,bound,toks));rows.append(dict(cell=c,cap=bound,nodes=g.nodes,proof_nodes=len(toks),helpers_used=dict(g.used)))
        # No within-batch speculative predecessor; every tree uses frozen env.
    path=PREFIX+'extree_J_batch1_codex_171.txt.gz'
    assert not (ROOT/path).exists(),'do not overwrite proof'
    plain=G.write_batch(ROOT/path,refs,deps,trees)
    save(PREFIX+'production_batch1_codex_171.json',dict(path=path,rows=rows,container_sha256=sha(path),
         plain_sha256=hashlib.sha256(plain.encode()).hexdigest(),environment_sha256=canonical(env),J_sha256=f['J_sha256'],status='AWAITING_DUAL_VERIFICATION'))
    print('Built small batch',rows,flush=True)

def verify():
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    meta=load(PREFIX+'production_batch1_codex_171.json');path=meta['path']
    assert path not in REFS and sha(path)==meta['container_sha256']
    t=time.monotonic();a=A.verify(path);assert a['ok'];print('A accepted',a['nodes'],flush=True)
    b=B.verify_any(path);assert b['ok'];print('B accepted',b['nodes'],flush=True)
    assert a['nodes']==b['nodes']==b['hist_checks']==sum(r['nodes'] for r in meta['rows'])
    assert [(r['cell'],r['cap'],r['nodes']) for r in a['rows']]==[(r['cell'],r['cap'],r['nodes']) for r in b['rows']]
    a.pop('certified',None);b.pop('certified',None)
    J={key(k):v for k,v in f['J'].items()};backed={k for k,v in dep.items() if k in J and v[0]<=J[k]}
    for r in meta['rows']:assert r['cap']<=J[key(r['cell'])];backed.add(key(r['cell']))
    out=dict(verifier_A=a,verifier_B=b,histogram_mismatches=0,environment_sha256=canonical(env),
             source_versions={p:sha(p) for p in VERSIONS},certificate_sha256=sha(path),
             J_census=census(J),jointly_usable=len(backed),remaining=35-len(backed),
             backed_cells=sorted(map(text,backed)),J_sha256=f['J_sha256'],
             status='DUAL_ACCEPTED',round_verdict='ROUND171_J_PRODUCTION_PROGRESS')
    save(PREFIX+'production_batch1_verified_codex_171.json',out)
    save(PREFIX+'production_batch1_timing_codex_171.json',dict(seconds_noncanonical=time.monotonic()-t,content_sha256=canonical(out)))
    print('PROGRESS',len(backed),'/35',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','pilots','produce','verify']);p.add_argument('--cap',type=int,default=100000);p.add_argument('--cells',default='');a=p.parse_args()
    if a.mode=='freeze':freeze()
    elif a.mode=='pilots':pilots(a.cap)
    elif a.mode=='produce':produce(a.cells.split(','),a.cap)
    else:verify()
