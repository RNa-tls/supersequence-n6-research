"""Independent persisted literal-word, surgery, and port-step capacity audit.
Does not import the gap generator, Geometry, or the run-level capacity search.
The universal inclusion lemma is a hand proof, not inferred from controls.
"""
import hashlib,itertools,json,subprocess,sys,time
from collections import Counter
from pathlib import Path
from verify_g2_k4_contraction_certificate_codex import measure
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rot(v,k=1):k%=len(v);return v[k:]+v[:k]
def E(v,k=1):return rot(v[:-1],k)+v[-1:]
def Q(v):return min(E(v,k) for k in range(len(v)-1))
def h(v):return min(rot(v,k) for k in range(len(v)))
def root_return(ps):
    qs=[Q(v) for v,l in ps];runs=[qs[0]]
    for q in qs[1:]:
        if q!=runs[-1]:runs.append(q)
    return (runs[0]==runs[-1] and len(runs)==len(set(runs))+1
            and len(set(runs[1:-1]))==len(runs)-2 and E(ps[-1][0])==ps[0][0])
def apply_ordinary(ps,step,n):
    i,j=step['i'],step['j'];v,a=ps[i];c,b=ps[j]
    assert rot(v,a)==c and a+b<=n
    assert all(Q(t)==Q(c) and l==n for t,l in ps[i+1:j])
    assert all(Q(t)!=Q(c) for t,l in ps[:i]+ps[j+1:])
    return ps[:i]+[(v,a+b)]+ps[j+1:]
def audit_gap(row):
    n=row['n'];before,ps,used,_=measure(row['word'],n);assert before==row['before']
    c=row['certificate'];assert row['solutions']>0
    for step in c['ordinary_before']:ps=apply_ordinary(ps,step,n)
    i,j=c['cut'];v,a=ps[i];end,b=ps[j]
    assert rot(v,a)==end and a+b==n
    assert all(l==n for t,l in ps[i+1:j])
    inner=ps[i+1:j]+[(end,n)];outer=ps[:i]+[(v,n)]+ps[j+1:]
    assert {Q(t) for t,l in inner}.isdisjoint(Q(t) for t,l in outer)
    assert {h(t) for t,l in inner}&{h(t) for t,l in outer}=={h(v)}
    for step in c['ordinary_after']:outer=apply_ordinary(outer,step,n)
    im,ip,iw,_=measure(c['inner']['word'],n);om,op,ow,_=measure(c['outer']['word'],n)
    assert ip==inner and op==outer and im==c['inner_metrics'] and om==c['outer_metrics']
    assert all(l==n for t,l in inner+outer)
    assert len({h(t) for t,l in inner})==len(inner)
    assert len({h(t) for t,l in outer})==len(outer)
    assert ow<used and iw<=used
    assert im['x']==im['H']==om['e']==om['x']==om['H']==0
    if c['kind']=='M_FRESH_GAP':assert im['e']==0
    else:assert c['kind']=='R_ROOT_RETURN_GAP' and im['e']==1 and root_return(inner)
    assert len(c['ordinary_before'])+len(c['ordinary_after'])==1
    assert all(all(w==2 for w in step['internal_weights']) for step in c['ordinary_before']+c['ordinary_after'])
    assert im['P']+om['P']==before['P']-(n-1)
    assert im['O']+om['O']==before['O']-1
    assert im['D']+om['D']==before['D']
    assert before['S']-im['S']-om['S']==(1 if c['kind']=='M_FRESH_GAP' else 0)
    # The cut initially shares the split hexagon, not an orbit. A subsequent
    # ordinary outer contraction may remove that hexagon from the outer piece.
    # The two resulting words are not asserted concatenable.
    assert ({h(t) for t,l in inner}&{h(t) for t,l in outer})<={h(v)}
    return c['kind']
def literal_capacity_witness(row):
    if row['passes']<0:assert row['accepted']==0 and row['witness']==[];return
    W=list(itertools.permutations(range(6)));ps=[W[i] for i in row['witness']]
    assert len(ps)==row['passes'] and len(set(map(h,ps)))==len(ps)
    raw=list(ps[0]);previous=None
    for v in ps:
        if previous is not None:
            ep=rot(previous,-1)
            if v==E(previous):tail=(ep[1],ep[0])
            else:
                tails=[tuple(ep[i] for i in t) for t in [(2,0,1),(2,1,0)]]
                possible=[t for t in tails if ep[3:]+t==v];assert len(possible)==1;tail=possible[0]
            raw.extend(tail)
        raw.extend(v[:5]);previous=v
    m,passes,_,_=measure(''.join(map(str,raw)),6)
    assert passes==[(v,6) for v in ps] and m['D']==row['deficit']
    assert m['H']==m['x']==0 and m['e']==1 and root_return(passes)

def main():
    paths=['outputs/rr_round137_protected_seam_codex.json','outputs/rr_round137_gap_cut_codex.json',
           'outputs/rr_round137_root_return_capacity_codex.json','outputs/rr_round135_capacity_codex.json']
    p,g,c,old=[json.loads((ROOT/f).read_text()) for f in paths]
    counts=Counter(audit_gap(r) for r in g['rows']);assert len(g['rows'])==835
    assert counts=={'M_FRESH_GAP':321,'R_ROOT_RETURN_GAP':514}
    # Independently verify the exact S6-invariant offset map.
    identity=0
    for v in itertools.permutations(range(6)):
        for a in range(1,6):
            ep=rot(v,a-1);natural=rot(v,a);inv={x:i for i,x in enumerate(natural)}
            for tail,offset in [((1,2,0),(2,3,4,0,1,5)),((2,0,1),(2,3,4,1,5,0)),((2,1,0),(2,3,4,1,0,5))]:
                t=ep[3:]+tuple(ep[j] for j in tail)
                assert tuple(inv[x] for x in t)==offset
                assert Q(t)!=Q(v) and (Q(t)==Q(natural))==(tail==(1,2,0));identity+=1
    assert identity==10800
    for r in c['result']['rows']:literal_capacity_witness(r)
    C0=[r['result']['passes'] for r in old['capacity']['replays'][:14]]
    assert C0==c['ordinary_capacity'] and all(not r['result']['capped'] for r in old['capacity']['replays'][:14])
    for f,value in c['source_sha256'].items():assert sha(ROOT/f)==value
    assert not c['result']['capped'] and c['exit_code']==0
    exe=ROOT/'outputs/verify_round137_root_return_codex.exe';t=time.perf_counter()
    argv=[str(exe)];proc=subprocess.run(argv,capture_output=True,text=True,check=True)
    ind=json.loads(proc.stdout)
    assert not ind['capped']
    assert ind['rows']==[{k:r[k] for k in ['deficit','passes','accepted']} for r in c['result']['rows']]
    assert max(c['ordinary_convolution'])==112
    assert max(r['bound'] for r in c['root_return_convolution'])==103
    assert max(c['ordinary_convolution'])<117 and max(r['bound'] for r in c['root_return_convolution'])<117
    out=dict(schema='codex/round137-independent-gap-capacity/1',verified=True,identity_count=identity,
        gap_controls=len(g['rows']),gap_histogram=dict(counts),capacity_witnesses=sum(r['passes']>=0 for r in c['result']['rows']),
        independent_capacity=ind,independent_seconds=time.perf_counter()-t,independent_argv=argv,
        independent_source_sha256=sha(ROOT/'src/verify_round137_root_return_codex.c'),independent_binary_sha256=sha(exe),
        verifier_sha256=sha(__file__),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_sha256={f:sha(ROOT/f) for f in paths},M_bound=112,R_bound=103,required_pass_sum=117,
        mathematical_scope='finite controls and local capacity complete; universal gap inclusion is the separate hand proof',
        NR6='ASSUMED',global_L6_ge872=False)
    out['mathematical_digest']=digest(ind)
    (ROOT/'outputs/rr_round137_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['verified','gap_controls','M_bound','R_bound','required_pass_sum']}))
if __name__=='__main__':main()
