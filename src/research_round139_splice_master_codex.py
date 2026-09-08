"""Finite certificate for the G2 successor-splicing master theorem.
Only archived local/NR4 words and small symbolic support permutations.
"""
import functools,hashlib,itertools,json,subprocess
from collections import Counter
from research_alpha_gap_codex import ROOT
from research_round135_contraction_codex import geometry
from certify_round139_multidefect_codex import literal,seams_verify

def components(n,edge):
    indeg=Counter(t for t,w in edge.values());assert all(z==1 for z in indeg.values())
    assert set(range(n))-set(indeg)=={0}
    path=[];v=0
    while v is not None:
        assert v not in path;path.append(v);v=edge[v][0] if v in edge else None
    seen=set(path);cycles=[]
    for start in range(n):
        if start in seen:continue
        seq=[];v=start
        while v not in seen:seen.add(v);seq.append(v);v=edge[v][0]
        assert v==start;cycles.append(seq)
    return path,cycles

def topology():
    cases=[('A_F2',[1,2,0],[0,0,0]),('A_F1',[2,0,1],[0,0,0]),
           ('B_disjoint',[1,0,3,2],[0,0,1,1]),('B_nested',[3,2,1,0],[0,1,1,0]),
           ('B_crossing',[2,3,0,1],[0,1,0,1])]
    out=[]
    for name,nu,h in cases:
        edges={nu[i]:(i+1,3) for i in range(len(nu)-1)}
        p,cc=components(len(nu),edges);simple=all(len({h[i] for i in z})==len(z) for z in [p]+cc)
        assert len(cc) in [0,2]
        if cc:assert simple
        out.append(dict(name=name,nu=nu,hex_labels=h,path=p,cycles=cc,componentwise_hex_simple=simple))
    return out

def splice(raw,n):
    g=geometry(n);d=literal(raw,n);ps=[(g.idx[v],l) for v,l in d['passes']];P=len(ps)
    # Exact original literal edge, assigned to the nu-successor entry.
    edges={}
    for i,((v,l),(t,b)) in enumerate(zip(ps,ps[1:])):
        src=d['nu'][i];w=g.weight(g.words[g.s(v,l-1)],g.words[t])
        assert g.s(ps[src][0],n-1)==g.s(v,l-1)
        assert (t,w) in g.joint[g.s(ps[src][0],n-1)]
        edges[src]=(i+1,w)
        if w==2:assert t==g.e(ps[src][0])
    path,cycles=components(P,edges);assert len(cycles) in [0,2]
    if cycles:
        for seq in [path]+cycles:assert len({g.h[ps[i][0]] for i in seq})==len(seq)
    pure=[z for z in cycles if all(edges[i][1]==2 for i in z)]
    for z in pure:
        assert len(z)==n-1 and len({g.q[ps[i][0]] for i in z})==1
    removed={i for z in pure for i in z};keep=set(range(P))-removed
    deleted_orbits={g.q[ps[i][0]] for i in removed}
    assert deleted_orbits.isdisjoint({g.q[ps[i][0]] for i in keep})
    cuts={i for i,(t,w) in edges.items() if i in keep and w>3}
    for z in cycles:
        if z in pure:continue
        if not any(i in cuts for i in z):cuts.add(min(i for i in z if edges[i][1]>=3))
    def chains():
        targets={t for i,(t,w) in edges.items() if i in keep and i not in cuts}
        out=[]
        for start in sorted(keep-targets):
            seq=[];v=start
            while True:
                seq.append(v)
                if v not in edges or v in cuts:break
                v=edges[v][0]
            out.append(seq)
        assert sum(map(len,out))==len(keep) and len(set(sum(out,[])))==len(keep)
        return out
    duplicate_cuts=[]
    for seq in chains():
        used=set();block=[];blocks=[]
        for i in seq:
            if block and edges[block[-1]][1]!=2:blocks.append(block);block=[]
            block.append(i)
        blocks.append(block)
        previous=None
        for block in blocks:
            hh={g.h[ps[i][0]] for i in block};assert len(hh)==len(block)
            if used&hh:
                assert previous is not None;cuts.add(previous);duplicate_cuts.append(previous);used=set()
            used|=hh;previous=block[-1]
    assert len(duplicate_cuts)<=2
    if cycles:assert not duplicate_cuts
    pieces=[]
    for seq in chains():
        rep=g.replay([(ps[i][0],n) for i in seq]);assert rep
        dd=literal(rep['word'],n);assert dd['metrics']['H']==0
        pieces.append(dict(indices=seq,word=rep['word'],metrics=dd['metrics']))
    c=len(pure);h=sum(w>3 for t,w in edges.values());S=d['metrics']['S'];O=d['metrics']['O']
    Ototal=sum(p['metrics']['O'] for p in pieces);s=Ototal-(O-c)
    b=sum(p['metrics']['e']+p['metrics']['x'] for p in pieces)
    assert b+s==S+1-O+c
    assert sum(p['metrics']['P'] for p in pieces)==P-(n-1)*c
    assert sum(p['metrics']['D'] for p in pieces)==d['metrics']['D']+(n-1)*s
    assert len(pieces)<=3-c+h
    return dict(n=n,word=raw,nu=d['nu'],spliced_path=path,spliced_cycles=cycles,pure_free_cycles=pure,
                cuts=sorted(cuts),duplicate_separating_cuts=duplicate_cuts,pieces=pieces,
                c=c,b=b,s=s,H=d['metrics']['H'],original=d['metrics'],identity_rhs=S+1-O+c)

def heavy_patterns(H):
    if not H:return [()]
    out=[]
    def rec(rem,mx,p):
        if not rem:out.append(tuple(v+3 for v in p));return
        for v in range(min(mx,rem),0,-1):rec(rem-v,v,p+[v])
    rec(H,3,[]);return out

def master_bounds():
    old=json.loads((ROOT/'outputs/rr_f0_column_115.json').read_text())['table']
    old['1,0,13']=json.loads((ROOT/'outputs/rr_round136_capacity_codex.json').read_text())['capacity']['result']
    extra=json.loads((ROOT/'outputs/rr_round139_master_capacities_codex.json').read_text())
    assert extra['verified'];new={r['result']['b']:r['result']['passes'] for r in extra['rows']}
    assert new=={0:33,1:48,2:63,3:78}
    used={}
    def cap(b,d):
        if b==2:
            value=63 if d<=3 else 92 if d<=8 else None
            assert value is not None
            used[str((b,d))]=dict(bound=value,source='R139 independent model',at_most_deficit=3 if d<=3 else 8)
            return value
        if b==3:
            assert d<=3;used[str((b,d))]=dict(bound=78,source='R139 independent model',at_most_deficit=3);return 78
        r=old[f'{b},0,{d}'];assert not r['capped']
        used[str((b,d))]=dict(bound=r['passes'],source='R136 independent capacity' if (b,d)==(1,13) else 'R115 preserved uncapped table',nodes=r['nodes'])
        return r['passes']
    @functools.lru_cache(None)
    def bound(m,b,d):
        if m==1:return cap(b,d)
        return max(cap(t,z)+bound(m-1,b-t,d-z) for t in range(b+1) for z in range(d+1))
    rows=[]
    for k in [1,2,3,4]:
        for topology_components in [1,3]:
            for c in range(1 if topology_components==1 else 3):
                for H in range(4):
                    B=2-k+c-H
                    if B<0:continue
                    for heavy in heavy_patterns(H):
                        m=3-c+len(heavy);required=122-5*c
                        for s in range((B if m>1 else 0)+1):
                            b=B-s;D=5*k-2+5*s;value=bound(m,b,D)
                            reason='STRICT_CAPACITY'
                            if value==required:
                                assert c==2 and topology_components==3
                                if heavy==(4,) and m==2 and D==13 and b==0:reason='ALL_312_W4_SEAMS_HEX_COLLIDE'
                                elif heavy==(4,4) and m==3 and D==8 and b==0:reason='ALL_EXTREMAL_W4_TRIPLES_HEX_COLLIDE'
                                else:raise AssertionError(('unresolved equality',k,c,H,s,b,D,m,value))
                            assert value<=required
                            rows.append(dict(k=k,topology_components=topology_components,c=c,H=H,heavy=heavy,
                                B=B,s=s,b=b,D_sum=D,max_light_pieces=m,required_passes=required,
                                capacity_bound=value,margin=required-value,closure=reason))
    return dict(rows=rows,used_capacity_bounds=used,all_closed=True)

def resource_coverage(bounds):
    source=json.loads((ROOT/'outputs/rr_round139_initial_codex.json').read_text())['resources']
    rows=[]
    for rid,r in enumerate(source['rows']):
        matches=[]
        topologies=[1] if r['type']=='A' and r['F']==1 else [3] if r['type']=='A' else [1,3]
        for idx,z in enumerate(bounds['rows']):
            exact_block_excess=r['delta']-r['F']+r['x']+z['c']
            if (z['k']==2 and z['topology_components'] in topologies and z['H']==r['H']
                    and list(z['heavy']) in r['heavy_multisets'] and 0<=z['s']<=exact_block_excess):
                assert z['b']>=exact_block_excess-z['s']
                matches.append(idx)
        rows.append(dict(row_id=rid,resource=r,master_envelope_indices=matches,
                         status='CLOSED',reason='MASTER_CAPACITY_AND_SEAMS' if matches else 'NEGATIVE_FREE_BLOCK_BUDGET'))
    assert len(rows)==73 and sum(len(r['resource']['heavy_multisets']) for r in rows)==78
    return dict(distinct_rows=73,heavy_refined_tuples=78,closed=73,open=0,rows=rows)

def main():
    inputs=json.loads((ROOT/'outputs/rr_round139_controls_codex.json').read_text())
    words={(4,r['word']) for r in inputs['n4']['rows']}|{(r['n'],r['word']) for r in inputs['local'] if r['classification']['G']==2}
    controls=[splice(w,n) for n,w in sorted(words)];hist=Counter(str((d['n'],len(d['spliced_cycles']),d['c'],d['b'],d['s'])) for d in controls)
    bounds=master_bounds();head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    sources=['src/research_round139_splice_master_codex.py','src/certify_round139_multidefect_codex.py','src/research_round135_contraction_codex.py']
    result=dict(schema='codex/round139-G2-splicing-master/1',topology=topology(),controls=controls,
                control_count=len(controls),histogram=dict(hist),bounds=bounds,resource_coverage=resource_coverage(bounds),
                source_commit=head,
                committed_source_sha256={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in sources},
                runtime_source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
                inputs={f:hashlib.sha256((ROOT/'outputs'/f).read_bytes()).hexdigest() for f in ['rr_round139_controls_codex.json','rr_round139_initial_codex.json','rr_round139_master_capacities_codex.json']},
                scope='finite support topology, preserved local literal words, capacity convolution; no full NR6 search')
    (ROOT/'outputs/rr_round139_splice_master_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print('controls',len(controls),'rows',len(result['bounds']['rows']));print(dict(hist))
if __name__=='__main__':main()
