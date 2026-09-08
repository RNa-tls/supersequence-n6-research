"""R139 resource reconstruction and small, specified local models. No NR6 DFS."""
import hashlib,itertools,json,subprocess,time
from collections import Counter
from pathlib import Path
from research_alpha_gap_codex import Geometry,ROOT
from verify_g2_k4_contraction_certificate_codex import measure

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def resource_rows():
    rows=[]
    for typ,F,shorts in [('A',1,3),('A',2,3),('B',2,4)]:
        for delta in range(F+1):
            for x in range(F-delta+1):
                for H in range(F-delta-x+1):
                    for free in range(shorts+1):
                        e=free-F+delta
                        if e<0:continue
                        S=25+e+x-free;L=846+S+H
                        assert L==871+delta+x+H-F and L<=871
                        patterns=[[]] if H==0 else [[4]] if H==1 else [[5],[4,4]]
                        aeta=[(a,delta-a) for a in range(delta+1)
                              if a<=F and 0<=free-(F-a)<=shorts-F and delta-a<=e]
                        assert aeta
                        rows.append(dict(id=f'{typ}_F{F}_d{delta}_x{x}_H{H}_e{e}',type=typ,F=F,
                            delta=delta,x=x,H=H,e=e,f_out=free,S=S,L=L,P=122,O=26,D=8,
                            N=S+2-26,q_total=delta+x+H,heavy_multisets=patterns,a_eta=aeta))
    return dict(distinct_count=len(rows),raw_heavy_tuples=sum(len(r['heavy_multisets']) for r in rows),
                q_histogram=dict(Counter(r['q_total'] for r in rows)),
                mechanism_histogram=dict(Counter(str((r['delta'],r['x'],r['H'])) for r in rows)),rows=rows)

def full_chains(deficit):
    """Independent run-at-once b=g=0 enumeration, normalized first entry 012345.
    All endpoints allowed, permanent closed-run deficits paid immediately.
    No incumbent pruning. The domain is a single ordinary full-pass light chain.
    """
    g=Geometry(6);best=0;examples=[];nodes=0
    def visit(entry,usedh,usedq,spent,path):
        nonlocal nodes,best,examples
        nodes+=1;seq=list(path);q=g.q[entry]
        assert q not in usedq
        hset=set(usedh)
        for length in range(1,6):
            v=g.e(entry,length-1);h=g.h[v]
            if h in hset:break
            hset.add(h);seq.append(v)
            d=spent+5-length
            if d>deficit:continue
            if len(seq)>best:best=len(seq);examples=[]
            if len(seq)==best:examples.append(tuple(seq))
            endpoint=g.s(v,5)
            for t,w in g.joint[endpoint]:
                if w==3 and g.q[t]!=q and g.q[t] not in usedq and g.h[t] not in hset:
                    visit(t,hset,usedq|{q},d,seq)
    visit(0,set(),set(),0,[])
    assert len(set(examples))==len(examples)
    return dict(deficit=deficit,best=best,nodes=nodes,witnesses=examples,capped=False)

def heavy_seams():
    """All extremal triples for C0 convolution at total deficit eight.
    Literal genuine weight-four seams, exact value renaming; no quotient of histories.
    """
    g=Geometry(6);tables={d:full_chains(d) for d in [0,4]}
    C=[20,20,33,33,46,46,49,58,62]
    conv=[(a,b,8-a-b,C[a]+C[b]+C[8-a-b]) for a in range(9) for b in range(9-a)]
    maximum=max(z[3] for z in conv);splits=[z[:3] for z in conv if z[3]==maximum]
    assert maximum==112 and set(splits)=={(0,4,4),(4,0,4),(4,4,0)}
    moves={}
    for v in range(720):
        p=g.words[g.s(v,5)];out=[]
        for tail in itertools.permutations(p[:4]):
            target=p[4:]+tail
            if g.weight(p,target)!=4:continue
            raw=p+tail
            if any(len(set(raw[j:j+6]))==6 for j in range(1,4)):continue
            out.append(g.idx[target])
        moves[v]=out
    def renamed(seq,start):
        labels=g.words[start]
        return tuple(g.idx[tuple(labels[a] for a in g.words[v])] for v in seq)
    counts=Counter();witnesses=[];pair_examples=[]
    for ds in splits:
        for first in tables[ds[0]]['witnesses']:
            for t in moves[first[-1]]:
                for b in tables[ds[1]]['witnesses']:
                    second=renamed(b,t);counts['pair_attempts']+=1
                    if {g.q[v] for v in first}&{g.q[v] for v in second}:
                        counts['pair_orbit_collision']+=1;continue
                    if {g.h[v] for v in first}&{g.h[v] for v in second}:
                        counts['pair_hex_collision']+=1;continue
                    counts['pair_pass']+=1
                    pair_examples.append(dict(split=ds,first=first,second=second))
                    for u in moves[second[-1]]:
                        for c in tables[ds[2]]['witnesses']:
                            third=renamed(c,u);counts['triple_attempts']+=1
                            if {g.q[v] for v in first+second}&{g.q[v] for v in third}:
                                counts['triple_orbit_collision']+=1;continue
                            if {g.h[v] for v in first+second}&{g.h[v] for v in third}:
                                counts['triple_hex_collision']+=1;continue
                            ps=[(v,6) for v in first+second+third];rep=g.replay(ps)
                            assert rep
                            witnesses.append(dict(split=ds,entries=[first,second,third],word=rep['word']))
                            counts['triple_pass']+=1
    return dict(C0=C,convolution=conv,max_bound=maximum,extremal_splits=splits,
                tables=tables,counts=dict(counts),witnesses=witnesses,pair_examples=pair_examples,
                scope='all normalized ordinary three-chain deficit-eight maximizers at two genuine w4 seams',capped=False)

def main():
    t=time.perf_counter();r=dict(resources=resource_rows(),heavy_seams=heavy_seams())
    r.update(schema='codex/round139-multidefect/1',seconds=time.perf_counter()-t,
             commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             committed_source_sha256=hashlib.sha256(subprocess.check_output(['git','show','HEAD:src/research_round139_multidefect_codex.py'])).hexdigest())
    p=ROOT/'outputs/rr_round139_initial_codex.json';p.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r['resources'].items() if k!='rows'}));print(r['heavy_seams']['counts'])

if __name__=='__main__':main()
