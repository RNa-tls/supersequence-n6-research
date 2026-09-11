"""Exact local geometry plus finite controls for the separate hand seam proof."""
import hashlib,itertools,json
from collections import Counter
from pathlib import Path
import research_round142_dirty_topology_codex as old
ROOT=Path(__file__).resolve().parents[1]
def rot(s,n=1):return s[n:]+s[:n]
def E(s):return s[1:-1]+s[:1]+s[-1:]
def hx(s):return min(rot(s,k) for k in range(len(s)))
def qports(s):return [rot(s[:-1],k)+s[-1:] for k in range(len(s)-1)]
def control(saved):
    n=saved['n'];r=old.audit_word(saved['word'],n,keep_mixed=True)
    first=old.first_windows(r['word'],n);groups=[]
    for i,item in enumerate(first):
        if not i or item[0]!=first[i-1][0]+1:groups.append([])
        groups[-1].append(item)
    entries=[g[0][1] for g in groups];edges={}
    for i in range(len(groups)-1):
        src=r['nu'][i];target=i+1;w=groups[i+1][0][0]-groups[i][-1][0]
        typ='OTHER'
        if w==2:typ='E' if E(entries[src])==entries[target] else 'A'
        elif w==3 and rot(entries[src],2)==entries[target]:typ='B'
        edges[src]=dict(target_index=target,weight=w,kind=typ)
    components=old.component_paths(len(entries),edges)
    pure=[c for c in components[1:] if all(edges[x]['kind']=='E' for x in c)]
    openings=[]
    for comp in components[1:]:
        if comp in pure:continue
        heavy=[v for v in comp if edges[v]['weight']>=4]
        chosen=min(heavy) if heavy else next(v for v in r['cycle_cuts'] if v in comp)
        openings.append(chosen)
    lostA=sum(edges[x]['kind']=='A' for x in openings);lostB=sum(edges[x]['kind']=='B' for x in openings)
    pi={v:j for j,p in enumerate(r['pieces']) for v in p['indices']};full_first={};full_last={}
    for j,p in enumerate(r['pieces']):
        inds=p['indices'];a=b=1
        while a<len(inds) and edges[inds[a-1]]['kind']=='E':a+=1
        while b<len(inds) and edges[inds[-b-1]]['kind']=='E':b+=1
        full_first[j]=a==n-1;full_last[j]=b==n-1
    bad=[]
    for v,e in edges.items():
        if e['kind']!='A' or v in openings:continue
        j,k=pi[v],pi[e['target_index']]
        assert j!=k and r['pieces'][j]['indices'][-1]==v and r['pieces'][k]['indices'][0]==e['target_index']
        if full_last[j] and full_first[k]:bad.append(v)
    assert lostA+lostB<=r['K']-1-r['c']
    assert r['R_int']>=r['D2']-lostA+r['D3_same']-lostB+len(bad)
    assert len(bad)<=r['Z']-r['D3_same']
    return dict(word_sha256=hashlib.sha256(r['word'].encode()).hexdigest(),n=n,D2=r['D2'],Qs=r['D3_same'],Z=r['Z'],
      R_int=r['R_int'],d=r['K']-1-r['c'],lost_A=lostA,lost_B=lostB,bad=len(bad),bad_sources=bad)
def main():
    local=[]
    for p in itertools.permutations('012345'):
        v=''.join(p);t=rot(v);a=E(v);b=qports(t)[-1]
        inter=set(map(hx,qports(v)))&set(map(hx,qports(t)))
        assert hx(a)==hx(b) and inter=={hx(v),hx(a)} and len(inter)==2
        local.append(dict(source=v,target=t,companion_source=a,companion_target=b,hexes=sorted(inter)))
    inputs=ROOT/'outputs/rr_round142_shadow_budget_verified_codex.json';data=json.loads(inputs.read_text())
    rows=[control(r) for r in data['rows']]
    out=dict(schema='round143-companion-geometry-controls-v1',local_count=len(local),local=local,control_count=len(rows),controls=rows,
      input_sha256=hashlib.sha256(inputs.read_bytes()).hexdigest(),verified=True,capped=False,
      scope='720 local symmetries exhaustive; finite cover controls secondary to hand proof, not global enumeration')
    (ROOT/'outputs/rr_round143_companion_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(local=len(local),controls=len(rows),bad=sum(r['bad'] for r in rows),lost_A=sum(r['lost_A'] for r in rows),verified=True)))
if __name__=='__main__':main()
