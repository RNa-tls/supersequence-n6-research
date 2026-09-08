"""Independent endpoint-lookup verification of the successor-splicing proof.
No producer splicing function, no continuation search, no new capacity DFS.
"""
import hashlib,itertools,json,subprocess
from collections import Counter
from pathlib import Path
from certify_round139_multidefect_codex import literal,canon_orbit,canon_hex,seams_verify
ROOT=Path(__file__).resolve().parents[1]
def load(f):return json.loads((ROOT/'outputs'/f).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rotate(v,n=1):return v[n%len(v):]+v[:n%len(v)]
def E(v):return v[1:-1]+v[:1]+v[-1:]
def fullword(entries,joint):
    raw=list(entries[0]);n=len(entries[0])
    for k,v in enumerate(entries):
        if k:
            end=rotate(entries[k-1],-1);target,w=joint[end];assert target==v
            raw.extend(v[-w:])
        raw.extend(v[:n-1])
    return ''.join(map(str,raw))

def endpoint_audit(row):
    n=row['n'];d=literal(row['word'],n);passes=d['passes'];entries=[v for v,l in passes]
    endmap={}
    for (v,l),(target,m) in zip(passes,passes[1:]):
        end=rotate(v,l-1);w=next((i for i in range(1,n) if end[i:]==target[:-i]),n)
        assert end not in endmap;endmap[end]=(target,w)
    # No nu lookup here: identify an outgoing joint only by its old literal
    # exit window matching this completed pass's exit window.
    successor={v:endmap[rotate(v,-1)] for v in entries if rotate(v,-1) in endmap}
    assert len(successor)==len(entries)-1
    predecessor={t:v for v,(t,w) in successor.items()};assert len(predecessor)==len(successor)
    unseen=set(entries);path=[];v=entries[0]
    while True:
        assert v in unseen;unseen.remove(v);path.append(v)
        if v not in successor:break
        v=successor[v][0]
    cycles=[]
    while unseen:
        v=start=min(unseen);seq=[]
        while v in unseen:unseen.remove(v);seq.append(v);v=successor[v][0]
        assert v==start;cycles.append(seq)
    assert len(cycles) in (0,2)
    if cycles:assert all(len(set(map(canon_hex,z)))==len(z) for z in [path]+cycles)
    freecycles=[z for z in cycles if all(successor[v][1]==2 for v in z)]
    for z in freecycles:
        assert len(z)==n-1 and len(set(map(canon_orbit,z)))==1
        assert all(successor[v][0]==E(v) for v in z)
    removed=set(sum(freecycles,[]));kept=set(entries)-removed
    assert set(map(canon_orbit,removed)).isdisjoint(map(canon_orbit,kept))
    # Validate the producer's serialized decomposition, not its decision code.
    used=set();actual_b=0;sumO=0;sumD=0;sumP=0;retained_edges=set()
    for p in row['pieces']:
        ee=[entries[i] for i in p['indices']];raw=fullword(ee,endmap)
        assert raw==p['word'];q=literal(raw,n)
        assert all(l==n for v,l in q['passes']) and q['metrics']['H']==0
        assert not used&set(ee);used.update(ee)
        for a,b in zip(ee,ee[1:]):assert successor[a][0]==b;retained_edges.add(a)
        for k,v in q['metrics'].items():assert v==p['metrics'][k]
        actual_b+=q['metrics']['e']+q['metrics']['x'];sumO+=q['metrics']['O'];sumD+=q['metrics']['D'];sumP+=q['metrics']['P']
    assert used==kept
    for v,(t,w) in successor.items():
        if v in kept and v not in retained_edges:assert w>=3,'cut illegally split a free E block'
    c=len(freecycles);s=sumO-(d['metrics']['O']-c)
    assert (c,actual_b,s)==(row['c'],row['b'],row['s'])
    assert actual_b+s==d['metrics']['S']+1-d['metrics']['O']+c
    assert sumP==len(entries)-(n-1)*c
    assert sumD==d['metrics']['D']+(n-1)*s
    heavy=sum(w>3 for t,w in successor.values());assert len(row['pieces'])<=3-c+heavy
    return (n,len(cycles),c,actual_b,s)

def support_verify():
    out=[]
    for count in [3,4]:
        for nu in itertools.permutations(range(count)):
            if any(nu[i]==i for i in range(count)):continue
            orbit=[];unseen=set(range(count))
            while unseen:
                start=min(unseen);z=[];v=start
                while v in unseen:unseen.remove(v);z.append(v);v=nu[v]
                orbit.append(z)
            if sorted(map(len,orbit))!=([3] if count==3 else [2,2]):continue
            ext=list(nu)+[count];inv=[ext.index(i) for i in range(count+1)]
            perm=[(inv[i]+1)%(count+1) for i in range(count+1)]
            cycles=[];unseen=set(range(count+1))
            while unseen:
                v=min(unseen);z=[]
                while v in unseen:unseen.remove(v);z.append(v);v=perm[v]
                cycles.append(z)
            assert len(cycles) in [1,3]
            if len(cycles)==3:
                for h in orbit:assert len({j for j,z in enumerate(cycles) if set(z)&set(h)})==len(h)
            out.append(dict(nu=nu,extended_cycles=cycles))
    assert len(out)==5
    return out

def allocations(total,n):
    if n==1:yield (total,);return
    for j in range(total+1):
        for rest in allocations(total-j,n-1):yield (j,)+rest

def arithmetic(data):
    old=load('rr_f0_column_115.json')['table'];old['1,0,13']=load('rr_round136_capacity_codex.json')['capacity']['result']
    model=load('rr_round139_master_capacities_codex.json');assert model['verified']
    for b in range(4):
        rows=[r for r in model['rows'] if r['result']['b']==b];assert len(rows)==2
        assert all(not r['result']['capped'] for r in rows)
        assert {r['result']['passes'] for r in rows}=={[33,48,63,78][b]}
    b2=load('rr_round139_independent_codex.json')['independent_b2'][-1]['result']
    producer=load('rr_round139_capacities_codex.json')['rows'][-1]['result']
    assert b2['passes']==producer['passes']==92 and not b2['capped'] and not producer['capped']
    def capacity(b,d):
        if b==3:assert d<=3;return 78
        if b==2:
            assert d<=8;return 63 if d<=3 else 92
        q=old[f'{b},0,{d}'];assert not q['capped'];return q['passes']
    expected=set()
    for k in range(1,5):
        for circuits in [0,2]:
            for c in range(circuits+1):
                for H in range(max(0,3-k+c)):
                    B=2-k+c-H
                    for h in range(4):
                        for weights in itertools.combinations_with_replacement([4,5,6],h):
                            if sum(w-3 for w in weights)!=H:continue
                            m=3-c+h
                            for s in range(B+1):
                                if m==1 and s:continue
                                expected.add((k,circuits+1,c,H,tuple(sorted(weights,reverse=True)),s))
    actual=set();equalities=[]
    for r in data['bounds']['rows']:
        key=(r['k'],r['topology_components'],r['c'],r['H'],tuple(r['heavy']),r['s']);assert key not in actual;actual.add(key)
        assert r['B']==2-r['k']+r['c']-r['H'] and r['b']==r['B']-r['s']
        assert r['D_sum']==5*r['k']-2+5*r['s'] and r['required_passes']==122-5*r['c']
        m=r['max_light_pieces'];upper=max(sum(capacity(b,d) for b,d in zip(bs,ds)) for bs in allocations(r['b'],m) for ds in allocations(r['D_sum'],m))
        assert upper==r['capacity_bound'] and upper<=r['required_passes']
        if upper==r['required_passes']:
            assert r['c']==2 and r['topology_components']==3
            assert (tuple(r['heavy']),m,r['D_sum'],r['b']) in [((4,),2,13,0),((4,4),3,8,0)]
            equalities.append(key)
    assert actual==expected and len(actual)==38
    return dict(master_envelopes=38,by_k=dict(Counter(r['k'] for r in data['bounds']['rows'])),equality_rows=equalities)

def resource_verify(data):
    from verify_round139_multidefect_codex import independent_rows
    rows=data['resource_coverage']['rows']
    actual=sorted((r['resource']['type'],r['resource']['F'],r['resource']['delta'],r['resource']['x'],r['resource']['H'],r['resource']['e']) for r in rows)
    assert actual==independent_rows() and len(rows)==73
    for r in rows:
        z=r['resource'];expected=[]
        top=[1] if (z['type'],z['F'])==('A',1) else [3] if z['type']=='A' else [1,3]
        for index,m in enumerate(data['bounds']['rows']):
            if m['k']!=2 or m['topology_components'] not in top or m['H']!=z['H'] or list(m['heavy']) not in z['heavy_multisets']:continue
            # Independently use S+1-O+c, not the producer's delta formula.
            exact=z['S']+1-z['O']+m['c']
            if 0<=m['s']<=exact:
                assert exact-m['s']<=m['b'];expected.append(index)
        assert expected==r['master_envelope_indices'] and r['status']=='CLOSED'
        if not expected:
            assert all(z['S']+1-z['O']+c<0 for t in top for c in range(t))
    return dict(distinct_rows=73,heavy_refined_tuples=sum(len(r['resource']['heavy_multisets']) for r in rows),closed=73,open=0)

def provenance_verify():
    out={}
    for f,field in [('rr_round139_capacities_codex.json','committed_blob_sha256'),
                    ('rr_round139_independent_codex.json','committed_source_sha256'),
                    ('rr_round139_master_capacities_codex.json','sources')]:
        d=load(f);head=d['commit']
        for p,expected in d[field].items():
            assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest()==expected
        rows=d.get('rows',d.get('independent_b2',[]))
        for r in rows:
            assert not r['result']['capped'] and r.get('exit_code',0)==0
        out[f]=dict(commit=head,committed_source_blobs=len(d[field]),all_runs_complete=True)
    assert load('rr_round139_independent_codex.json')['input_sha256']['initial']==sha(ROOT/'outputs/rr_round139_initial_codex.json')
    return out

def main():
    data=load('rr_round139_splice_master_codex.json');hist=Counter()
    for row in data['controls']:hist[str(endpoint_audit(row))]+=1
    assert dict(hist)==data['histogram'] and len(data['controls'])==1510
    identities=0
    for n in [4,5,6]:
        for v in itertools.permutations(range(n)):
            for length in range(1,n+1):
                c=rotate(v,length);assert rotate(c,-1)==rotate(v,length-1);identities+=1
    assert identities==5016
    sources=['src/verify_round139_splice_master_codex.py','src/certify_round139_multidefect_codex.py',
             'src/verify_round135_structural_codex.py','src/round135_heavy_seam_codex.py',
             'src/research_round135_contraction_codex.py','src/research_alpha_gap_codex.py',
             'src/verify_round139_multidefect_codex.py']
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    result=dict(schema='codex/round139-master-independent/1',endpoint_identity_count=identities,
        support_permutations=support_verify(),literal_controls=1510,histogram=dict(hist),arithmetic=arithmetic(data),
        seams=seams_verify(load('rr_round139_initial_codex.json')),resources=resource_verify(data),provenance=provenance_verify(),verified=True,
        commit=head,committed_source_sha256={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in sources},
        runtime_source_sha256={p:sha(ROOT/p) for p in sources},
        inputs={f:sha(ROOT/'outputs'/f) for f in ['rr_round139_splice_master_codex.json','rr_round139_initial_codex.json','rr_round139_capacities_codex.json','rr_round139_independent_codex.json','rr_round139_master_capacities_codex.json','rr_f0_column_115.json','rr_round136_capacity_codex.json','rr_round135_heavy_seams_codex.json']},
        universal_proof='research/RR_ROUND139_SUCCESSOR_SPLICING_MASTER_CODEX.md sections 1-6',
        theorem_scope='NR6 AND G=2 AND L<=871: no covering walk',
        new_cells=[[2,2],[1,2]],recovered_old_cells=[[3,2],[4,2]],outer_before='11/55',outer_after='13/55',
        NR6='ASSUMED',global_L6_ge_872='NOT_PROVED')
    (ROOT/'outputs/rr_round139_master_verified_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['literal_controls','arithmetic','verified','outer_after']}))
if __name__=='__main__':main()
