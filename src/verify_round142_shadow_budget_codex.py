"""Independent shadow-port / repeat-bound checks on finite literal controls.
Producer performs a canonical cut. Checker validates every supplied cut and
piece directly against literal entry/exit geometry; does not trust charges.
"""
import hashlib,itertools,json,math,random,subprocess,time
from pathlib import Path
import research_round142_dirty_topology_codex as producer
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(r):
    n=r['n'];s=r['word'];pp=set(''.join(p) for p in itertools.permutations(map(str,range(n))))
    first=[];seen=set();actual=0
    for at in range(len(s)-n+1):
        p=s[at:at+n]
        if p in pp:
            actual+=1
            if p not in seen:first.append((at,p));seen.add(p)
    groups=[]
    for i,p in enumerate(first):
        if not i or p[0]!=first[i-1][0]+1:groups.append([])
        groups[-1].append(p)
    entries=[g[0][1] for g in groups];which={p:i for i,p in enumerate(entries)}
    def rotate(p):return p[1:]+p[:1]
    def ep(p):return p[1:-1]+p[0]+p[-1]
    def orbit(p):return min(p[i:-1]+p[:i]+p[-1] for i in range(n-1))
    def hexa(p):return min(p[i:]+p[:i] for i in range(n))
    edges={};cross=set();same=set();d2=0;heavyhidden=0
    for j,(a,b) in enumerate(zip(groups,groups[1:])):
        lo,p=a[-1];hi,t=b[0];w=hi-lo;v=which[rotate(p)]
        hidden=[s[i:i+n] for i in range(lo+1,hi) if s[i:i+n] in pp]
        edges[v]=(j+1,w,hidden)
        if w==2 and hidden:d2+=1;same.add(v)
        if w==3 and hidden:
            if hexa(entries[v])==hexa(t):same.add(v)
            else:cross.add(v)
        if w>=4:heavyhidden+=len(hidden)
    retained=set();Dsum=0;globalpieces=set();btotal=0;Ototal=0
    for piece in r['pieces']:
        path=piece['indices'];globalpieces.update(path)
        ports=[entries[v] for v in path];orbits=set(map(orbit,ports))
        assert len(set(map(hexa,ports)))==len(ports)
        missing={p for p in pp if orbit(p) in orbits and p not in ports}
        ghosts=[];freeblocks=1
        for v,tidx in zip(path,path[1:]):
            t,w,hidden=edges[v];assert t==tidx and w<=3
            if w==3:freeblocks+=1
            if v in cross:
                source=entries[v];target=entries[t]
                if ep(rotate(source))==target:ghost=rotate(source)
                else:assert rotate(ep(source))==target;ghost=ep(source)
                assert ghost in missing;ghosts.append(ghost);retained.add(v)
            else:assert not hidden
        assert len(ghosts)==len(set(ghosts))<=len(missing)==piece['D']
        assert freeblocks-len(orbits)==piece['b']
        Dsum+=len(missing);btotal+=piece['b'];Ototal+=len(orbits)
    cutcross=cross-retained
    assert len(cutcross)==r['mixed_cut']<=r['Z']-(len(same)-d2)
    assert len(cross)<=Dsum+len(cutcross)
    assert heavyhidden<=3*r['H']
    repeats=actual-math.factorial(n);t=len(s)-r['exact_length_base']
    bound=(n-1)*t-r['c']-(n-2)*r['Z']-(n-4)*r['H']
    assert repeats==d2+2*(len(same)-d2)+len(cross)+heavyhidden<=bound
    assert btotal+Ototal-(r['selected_O']-r['c'])==r['Bstar']
    return dict(word_sha256=hashlib.sha256(s.encode()).hexdigest(),n=n,R=repeats,bound=bound,
        mixed_retained=len(retained),mixed_cut=len(cutcross),shadow_deficit=Dsum)
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    sources=[Path(__file__),Path(producer.__file__)]
    for p in sources:assert p.read_bytes()==subprocess.check_output(['git','show',head+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT)
    oldpath=ROOT/'outputs/rr_round142_dirty_topology_codex.json';old=json.loads(oldpath.read_text())
    words={(r['n'],r['word']) for r in old['rows']};rng=random.Random(14220260911)
    # Bounded, deterministic construction controls, NOT an exhaustive walk search.
    for n,count in [(4,100),(5,20),(6,8)]:
        pp=[''.join(p) for p in itertools.permutations(map(str,range(n)))]
        for _ in range(count):
            rng.shuffle(pp);w,_=producer.fixed_point(producer.spelling(pp),n);words.add((n,w))
    start=time.perf_counter();rows=[];verified=[]
    for n,w in sorted(words):
        r=producer.audit_word(w,n,keep_mixed=True);v=verify(r);rows.append(r);verified.append(v)
    out=dict(schema='round142-shadow-budget-and-repeat-bound-v1',source_commit=head,
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
        input_sha256={oldpath.relative_to(ROOT).as_posix():sha(oldpath)},
        verified=True,capped=False,continuation_search=False,controls=len(rows),rows=rows,independent=verified,
        theorem='For a first-occurrence geodesic fixed point: R<=(n-1)t-c-(n-2)Z-(n-4)H',
        n6_threshold='L<=871 implies R<=20-c-4Z-2H<=20',
        exact_scope='HAND THEOREM + FINITE CONTROL CORROBORATION; NOT NR-UNIVERSAL',seconds=time.perf_counter()-start)
    (ROOT/'outputs/rr_round142_shadow_budget_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,controls=len(rows),retained_mixed=sum(v['mixed_retained'] for v in verified),cut_mixed=sum(v['mixed_cut'] for v in verified),seconds=out['seconds'])))
if __name__=='__main__':main()
