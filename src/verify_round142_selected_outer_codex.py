"""Independent selected-port audit. No producer parser, splice or BFS imported.

The finite domain corroborates hand theorems; it is NOT all n6 covers.
"""
import collections, hashlib, itertools, json, math, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def cycles(f):
    left=set(range(len(f))); out=[]
    while left:
        v=min(left); start=v; a=[]
        while v in left: left.remove(v); a.append(v); v=f[v]
        assert v==start; out.append(a)
    return out
def geometry(n):
    pp=list(itertools.permutations(range(n))); ix={p:i for i,p in enumerate(pp)}
    rr=[ix[p[1:]+p[:1]] for p in pp]
    ee=[ix[p[1:-1]+p[:1]+p[-1:]] for p in pp]
    hh=cycles(rr); qq=cycles(ee)
    return pp,ix,rr,ee,{v:i for i,c in enumerate(hh) for v in c},{v:i for i,c in enumerate(qq) for v in c}
def check(row):
    n=row['n']; pp,ix,rr,ee,h,q=geometry(n); w=tuple(map(int,row['word']))
    seen=set(); first=[]; occ=[]
    for at in range(len(w)-n+1):
        v=ix.get(w[at:at+n])
        if v is not None:
            occ.append(v)
            if v not in seen: first.append((at,v)); seen.add(v)
    assert len(seen)==math.factorial(n)
    starts=[0]+[j for j in range(1,len(first)) if first[j][0]!=first[j-1][0]+1]
    groups=[first[a:b] for a,b in zip(starts,starts[1:]+[len(first)])]
    entries=[g[0][1] for g in groups]; P=len(entries); O=len({q[v] for v in entries})
    # Reconstruct successor matching from the cyclic order of registered
    # entry positions in each hex, not from producer's endpoint formula.
    nu=[None]*P
    for hi in sorted({h[v] for v in entries}):
        ids={v:i for i,v in enumerate(entries) if h[v]==hi}
        for v,i in ids.items():
            t=rr[v]
            while t not in ids:t=rr[t]
            nu[i]=ids[t]
    assert nu==row['nu'] and sorted(nu)==list(range(P))
    for i,g in enumerate(groups):assert rr[g[-1][1]]==entries[nu[i]]
    inv={v:i for i,v in enumerate(nu+[P])}
    beta=[(inv[v]+1)%(P+1) for v in range(P+1)]
    cc=cycles(beta); K=len(cc); comp={v:j for j,c in enumerate(cc) for v in c if v!=P}
    Rint=sum(x-1 for x in collections.Counter((h[v],comp[i]) for i,v in enumerate(entries)).values())
    cleanE={}; d2=[]; d3same=[]; dirty=[]; weights=[]
    for i,(a,b) in enumerate(zip(groups,groups[1:])):
        lo=a[-1][0]; hi=b[0][0]; gap=hi-lo; weights.append(gap)
        hidden=[(j,ix[w[j:j+n]]) for j in range(lo+1,hi) if w[j:j+n] in ix]
        if hidden: dirty.append(i)
        v=entries[nu[i]]; t=b[0][1]
        cleanE[nu[i]]=gap==2 and not hidden
        if gap==2 and hidden:
            assert t==rr[v] and nu[i]<i; d2.append(nu[i])
        if gap==3 and hidden and h[v]==h[t]:
            assert t==rr[rr[v]] and nu[i]<i; d3same.append(nu[i])
    pure=[c for c in cc if P not in c and all(cleanE.get(v,False) for v in c)]
    c=len(pure); G=P-math.factorial(n-1); k=O-math.factorial(n-2)
    D2=len(d2); Z=G-c-D2; H=sum(max(0,x-3) for x in weights); S=sum(x>=3 for x in weights)
    Bstar=S+1+D2-O+c
    assert D2+len(d3same)<=Rint<=G+1-K and Z>=len(d3same)
    assert min(k,Z,H,Bstar)>=0
    base=math.factorial(n)+math.factorial(n-1)+math.factorial(n-2)+n-3
    assert len(w)==base+k+Z+H+Bstar
    assert G<=(n-1)*k and len(dirty)<=len(occ)-math.factorial(n)
    assert (K,Rint,c,D2,Z,H,Bstar)==tuple(row[z] for z in ['K','R_int','c','D2','Z','H','Bstar'])
    covered=[]; osum=bsum=dsum=0
    for piece in row['pieces']:
        ids=piece['indices']; covered+=ids
        text=tuple(map(int,piece['word'])); windows=[ix[text[j:j+n]] for j in range(len(text)-n+1) if text[j:j+n] in ix]
        assert len(windows)==n*len(ids)==len(set(windows))
        assert {h[v] for v in windows}=={h[entries[i]] for i in ids}
        pq=[q[entries[i]] for i in ids]; po=len(set(pq))
        b=1+sum(not cleanE.get(i,False) for i in ids[:-1])-po
        assert (po,b,(n-1)*po-len(ids))==(piece['O'],piece['b'],piece['D'])
        osum+=po;bsum+=b;dsum+=piece['D']
    removed=set(v for cyc in pure for v in cyc)
    assert len(covered)==len(set(covered)) and set(covered)==set(range(P))-removed
    sharing=osum-(O-c)
    assert bsum+sharing==Bstar and dsum==(n-1)*k-G+(n-1)*sharing
    return {'n':n,'word_sha256':digest(row['word']),'k':k,'G':G,'D2':D2,'Z':Z,'Bstar':Bstar}
def main():
    t=time.perf_counter(); src=Path(__file__); rel=src.relative_to(ROOT).as_posix()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert src.read_bytes()==subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
    inp=ROOT/'outputs/rr_round142_dirty_topology_codex.json'; d=json.loads(inp.read_text())
    rows=[check(r) for r in d['rows']]
    out=dict(schema='round142-independent-selected-outer-v1',verified=True,source_commit=head,
        source_sha256=sha(src),input_sha256=sha(inp),controls=len(rows),capped=False,
        scope='FINITE_CONTROLS_OF_HAND_THEOREMS_NOT_GLOBAL_COVER_ENUMERATION',rows=rows,
        deterministic_digest=digest(rows),seconds=time.perf_counter()-t)
    (ROOT/'outputs/rr_round142_selected_outer_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps({k:out[k] for k in ['verified','controls','seconds']}))
if __name__=='__main__':main()
