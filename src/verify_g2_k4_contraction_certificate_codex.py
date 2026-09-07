"""Independent persisted-word replayer: does not import block builders/replay."""
import hashlib
import json
import sys
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def measure(raw,n):
    w=tuple(map(int,raw));alphabet=set(range(n))
    occ=[(i,w[i:i+n]) for i in range(len(w)-n+1) if set(w[i:i+n])==alphabet]
    assert occ[0][0]==0 and occ[-1][0]==len(w)-n
    words=[x for i,x in occ];assert len(set(words))==len(words)
    ps=[(words[0],1)];joints=[]
    for (i,a),(j,b) in zip(occ,occ[1:]):
        d=j-i
        if d==1:
            assert b==a[1:]+a[:1]
            ps[-1]=(ps[-1][0],ps[-1][1]+1)
        else:
            assert 2<=d<=n and a[d:]==b[:n-d]
            assert not any(a[k:]==b[:n-k] for k in range(1,d))
            joints.append((a,b,d));ps.append((b,1))
    def orbit(v):return min(v[j:n-1]+v[:j]+v[n-1:] for j in range(n-1))
    qs=[orbit(v) for v,l in ps];O=len(set(qs));P=len(ps)
    r=1+sum(a!=b for a,b in zip(qs,qs[1:]))
    m=dict(P=P,O=O,D=(n-1)*O-P,r=r,e=r-O,
           x=sum(wt>=3 and a==b for (u,v,wt),a,b in zip(joints,qs,qs[1:])),
           S=sum(wt>=3 for u,v,wt in joints),H=sum(max(wt-3,0) for u,v,wt in joints),windows=len(words))
    return m,ps,set(words),[j for j in joints if j[2]>=3]


def check(row,n):
    a,ap,aw,aj=measure(row['original']['word'],n)
    b,bp,bw,bj=measure(row['contracted']['word'],n)
    assert a==row['before'] and b==row['after']
    assert bw<aw and len(aw-bw)==2*n*(n-2)
    assert len(row['original']['word'])-len(row['contracted']['word'])==2*(n*n-n-1)
    assert aj==bj # every paid source/target/tail weight literally preserved
    assert ap[0][0]==bp[0][0]
    assert row['original']['word'][-n:]==row['contracted']['word'][-n:]
    assert all(l==n for v,l in bp)
    assert b['P']==a['P']-2*(n-1) and b['O']==a['O']-2
    assert a['D']==b['D'] and b['e']==b['x']==0
    for key in ('S','H'):assert a[key]==b[key]


def main():
    p=ROOT/'outputs/rr_locked_detour_contraction_codex.json'
    c=ROOT/'outputs/rr_g2_k4_contraction_certificate_codex.json'
    data=json.loads(p.read_text());cert=json.loads(c.read_text())
    assert sha(p)==cert['controls_sha256']
    capacity_source=(ROOT/'src/chain_capacity_115.c').read_bytes()
    assert hashlib.sha256(capacity_source.replace(b'\r\n',b'\n')).hexdigest()==cert['capacity_source_lf_sha256']
    counts={}
    for name,n,rows in [('rigid_n6',6,data['finite_blocks']['rigid_controls']),
                        ('alpha_n6',6,data['finite_blocks']['alpha_controls']),
                        ('complete_n4',4,data['n4']['controls'])]:
        for row in rows:check(row,n)
        counts[name]=len(rows)
    bound=cert['dependencies']['outputs/rr_round115_codex_nstar_0_0_20.json']['payload']
    assert bound['capped'] is False and bound['passes']==103 and bound['nodes']==2465729298
    assert bound['b']==bound['g']==0 and bound['s']==20
    contracted=cert['contracted']
    assert contracted['P']==122-2*5 and contracted['O']==28-2
    assert contracted['D']==5*contracted['O']-contracted['P']<=bound['s']
    assert contracted['S']==contracted['O']-1 and contracted['H']==0
    assert contracted['P']>bound['passes']
    assert sum(r['round133_remaining_splits'] for r in cert['class_ledger'])==118
    assert all(r['new_remaining_splits']==0 for r in cert['class_ledger'])
    result=dict(schema='codex/g2-k4-contraction-independent-word-replay/1',verified=True,
                literal_pairs=counts,control_sha256=sha(p),certificate_sha256=sha(c),
                verifier_sha256=sha(Path(__file__)),
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                binary_sha256=sha(Path(sys.executable)),full_argv=[sys.executable,*sys.argv],
                scope='independent persisted-word/control and ledger checks; hand reduction proof and inherited finite capacity explicitly required',
                capacity_reenumerated=False,remaining_B_classes=0,global_L6_ge_872_proved=False)
    (ROOT/'outputs/rr_g2_k4_contraction_verified_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
