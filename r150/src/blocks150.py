"""Third algorithm for n6 small cells: completed-orbit DP, b=d=0.
No feas(), no prefix/suffix bound. Forced full runs follow independently from
zero final deficit and zero tokens: after leaving an orbit it cannot be revisited.
Geometry is spelled from tuples, no imported catalogue.
"""
from functools import lru_cache
from hashlib import sha256
from itertools import permutations, product
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]

def main():
    ps=list(permutations(range(6)));ids={p:i for i,p in enumerate(ps)}
    def rot(p):return p[1:]+p[:1]
    def e(p):return p[1:5]+p[:1]+p[5:]
    def cycle(p,op,n):
        xs=[]
        for _ in range(n):xs.append(p);p=op(p)
        return xs
    oks=sorted({min(cycle(p,e,5)) for p in ps});hks=sorted({min(cycle(p,rot,6)) for p in ps})
    oi={p:i for i,p in enumerate(oks)};hi={p:i for i,p in enumerate(hks)}
    orb=[oi[min(cycle(p,e,5))] for p in ps];hx=[hi[min(cycle(p,rot,6))] for p in ps]
    runs=[[ids[t] for t in cycle(p,e,5)] for p in ps]
    edges=[]
    for i,p in enumerate(ps):
        end=p[-1:]+p[:-1]; row=[]
        for j,t in enumerate(ps):
            if t==p or t==end:continue
            w=next(6-l for l in range(5,-1,-1) if not l or end[-l:]==t[:l])
            if w>4 or t==e(p):continue
            da=int(t==rot(p));db=int(t==rot(rot(p)));hh=max(w-3,0)
            row.append((j,da,db,hh))
        edges.append(row)
    assert len(oks)==144 and len(hks)==120
    records=[]
    for a,bb,ee,hh in product(range(2),repeat=4):
        cells=0;cap=100000;t0=time.monotonic()
        class Capped(Exception):pass
        @lru_cache(None)
        def dp(entry,opened,hexmask,aa,bbb,ex,heavy):
            nonlocal cells
            cells+=1
            if cells>cap:raise Capped()
            q=orb[entry]
            assert not (opened>>q&1)
            opened|=1<<q
            # Entry charge paid by caller. Internal free-E collisions are ordinary.
            hexmask|=1<<hx[entry]
            run=runs[entry]
            for v in run[1:]:
                ex-=bool(hexmask>>hx[v]&1)
                if ex<0:return -10**6,()
                hexmask|=1<<hx[v]
            best=5;wit=tuple(run)
            for target,da,db,h in edges[run[-1]]:
                if opened>>orb[target]&1:continue
                re=int(bool(hexmask>>hx[target]&1) and not(da or db))
                if da>aa or db>bbb or re>ex or h>heavy:continue
                child,tail=dp(target,opened,hexmask,aa-da,bbb-db,ex-re,heavy-h)
                if 5+child>best:best,wit=5+child,tuple(run)+tail
            return best,wit
        try:
            capacity,witness=dp(0,0,0,a,bb,ee,hh)
            status='EXACT_UNCAPPED'
        except Capped:
            capacity=None;witness=();status='UNKNOWN_CAP'
        records.append(dict(cell=[0,0,a,bb,ee,hh],independent_capacity=capacity,
                            literal_port_witness=[list(ps[v]) for v in witness],DP_states=cells,
                            node_cap=cap,status=status,seconds=time.monotonic()-t0))
        print(records[-1]['cell'],status,capacity,cells,flush=True)
        dp.cache_clear()
    # Historical capacities are first read AFTER all independent decisions.
    prod={}
    for name in ('chain_cells_147.json','heavy_cells_147.json'):
        prod.update(json.loads((ROOT/'r147/tables'/name).read_text()))
    for r in records:
        p=prod.get('|'.join(map(str,r['cell'])))
        r['production_capacity']=None if p is None else p['cc']
        r['comparison']='UNKNOWN_CAP' if r['status']=='UNKNOWN_CAP' else ('PRODUCTION_CELL_ABSENT' if p is None else ('MATCH' if r['independent_capacity']==p['cc'] else 'DISAGREE'))
    out=ROOT/'r150/certs/blocks.json';assert not out.exists()
    out.write_text(json.dumps(dict(geometry='independent tuple overlaps',scope='b=0,d=0; a,bb,e,h each 0..1',records=records,
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),feas_called=False),indent=2)+'\n')
    assert not any(r['comparison']=='DISAGREE' for r in records)

if __name__=='__main__':main()
