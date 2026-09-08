"""Independent literal/event verification of R138 supporting artifacts.
No capacity recomputation, continuation, or complete-walk enumeration.
"""
import hashlib,itertools,json,subprocess,sys
from collections import Counter
from pathlib import Path
from verify_g2_k4_contraction_certificate_codex import measure
from verify_round137_gap_capacity_codex import audit_gap,apply_ordinary,Q,rot,h
ROOT=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit_literal(row,original):
    n=row['n'];W=list(itertools.permutations(range(n)));ids={v:i for i,v in enumerate(W)}
    _,base,_,_=measure(original['word'],n);cert=original['certificate']
    for step in cert['ordinary_before']:base=apply_ordinary(base,step,n)
    v=W[row['inserted_port']];seq=([(v,n)]+base) if row['side']=='before' else (base+[(v,n)])
    m,ps,_,_=measure(row['word'],n);assert ps==seq
    i,j=cert['cut'];shift=int(row['side']=='before');i+=shift;j+=shift
    inside={Q(t) for t,l in ps[i+1:j+1]};outside={Q(t) for t,l in ps[:i+1]+ps[j+1:]}
    shared=inside&outside;assert shared=={Q(v)} and ids[Q(v)]==row['shared_orbit']
    entries={t:k for k,(t,l) in enumerate(ps)};nu=[entries[rot(t,l)] for t,l in ps]
    qs=[Q(t) for t,l in ps]
    weights=[next(d for d in range(1,n+1) if d==n or rot(t,l-1)[d:]==u[:-d]) for (t,l),(u,z) in zip(ps,ps[1:])]
    asc={k for k,z in enumerate(nu) if k<z}
    free={k for k,w in enumerate(weights) if w==2 and qs[k]!=qs[k+1]}
    repeat=[k for k in range(1,len(ps)) if qs[k]!=qs[k-1] and qs[k] in qs[:k]]
    ordinary={k+1 for k in free if k>nu[k]};extra=set(repeat)-ordinary
    d=dict(F=len(asc),G=len(ps)-len({h(t) for t,l in ps}),a=len(asc-free),eta=len(extra),
           delta=len(asc-free)+len(extra),metrics=m,nu=nu,repeat=repeat,ordinary=sorted(ordinary),exceptional=sorted(extra))
    assert d==row['classification']
    assert d['delta']==2 and m['x']==m['H']==0

def equality_partitions(n):
    # Set partitions of INDEX positions, then ordered canonical orbit labels.
    # Different construction from the producer's restricted-growth run DFS.
    def rec(k,blocks):
        if k==n:
            seq=[None]*n
            for q,block in enumerate(blocks):
                for i in block:seq[i]=q
            if all(a!=b for a,b in zip(seq,seq[1:])):yield tuple(seq)
            return
        for b in range(len(blocks)):
            if k-1 in blocks[b]:continue
            blocks[b].append(k);yield from rec(k+1,blocks);blocks[b].pop()
        yield from rec(k+1,blocks+[[k]])
    yield from rec(0,[])

def independent_csp():
    histogram=Counter();nodes=0
    for n in range(2,8):
        for w in equality_partitions(n):
            first={q:w.index(q) for q in set(w)}
            for lo,hi in itertools.combinations(range(1,n+1),2):
                L=set(w[:lo]);I=set(w[lo:hi]);outside=L|set(w[hi:])
                Bsets=[{w[lo-1]}]+[{w[lo-1],q} for q in L if q!=w[lo-1]]
                repeated={k for k in range(lo,n) if first[w[k]]<k}
                root=w[lo];root_eligible=root not in L and any(w[k]==root for k in range(lo+1,hi))
                for B in Bsets:
                    freed={k for k in repeated if k>=hi and w[k] in B}
                    for mode in (['M','R'] if root_eligible else ['M']):
                        nodes+=1;exceptions=1 if mode=='R' else 0
                        extra=len(repeated-freed)-exceptions
                        s=len(I&outside);assert extra>=s
                        histogram[f'{mode}/shared{s}/extra{extra}']+=1
    return nodes,dict(histogram)

def main():
    inp=ROOT/'outputs/rr_round138_privacy_controls_codex.json';x=json.loads(inp.read_text())
    old=json.loads((ROOT/'outputs/rr_round137_gap_cut_codex.json').read_text())
    lookup={digest(r['word']):r for r in old['rows']}
    for r in old['rows']:audit_gap(r)
    for row in x['controls']['rows']:audit_literal(row,lookup[row['source_word_sha256']])
    assert len(old['rows'])==835 and len(x['controls']['rows'])==67
    nodes,hist=independent_csp();assert nodes==x['event_csp']['nodes'] and hist==x['event_csp']['histogram']
    assert x['controls']['positional_identities']==10800 and x['controls']['complementary_context_checks']==3600
    correction=x['metadata_correction'];blob=subprocess.check_output(['git','show',correction['commit']+':'+correction['file']])
    assert hashlib.sha256(blob).hexdigest()==correction['correct_committed_blob_sha256']
    assert Path(ROOT/correction['file']).read_bytes().replace(b'\r\n',b'\n')==blob
    assert sha(ROOT/correction['historical_certificate'])==correction['historical_certificate_sha256']
    assert not correction['old_certificate_modified'] and not correction['capacity_recomputed']
    for p,s in x['source_sha256'].items():assert sha(ROOT/p)==s
    out=dict(schema='codex/round138-independent-finite-verification/1',verified=True,controls=835,
             targeted_literal_shared_orbit_controls=67,targeted_delta1_counterexamples=0,all_targeted_sharing_delta=2,
             independent_event_models=nodes,event_histogram=hist,source_sha256=sha(__file__),
             input_sha256=sha(inp),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             argv=[sys.executable,*sys.argv],binary_sha256=sha(sys.executable),capped=False,node_cap=None,
             capacity_recomputed=False,scope='finite independent supporting checks; universal proposition requires the explicit run-crossing proof')
    out['mathematical_digest']=digest(hist)
    (ROOT/'outputs/rr_round138_privacy_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    (ROOT/'outputs/rr_round138_source_hash_correction_codex.json').write_text(json.dumps(correction,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['verified','targeted_literal_shared_orbit_controls','targeted_delta1_counterexamples','independent_event_models']}))
if __name__=='__main__':main()
