"""Finite consecutive-sigma run geometry, independent of traversal order."""
import itertools,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def E(p):return p[1:-1]+p[:1]+p[-1:]
def rot(p):return p[1:]+p[:1]
def hx(p):return min(p[j:]+p[:j] for j in range(6))
def blocks(lengths,start=tuple(range(6))):
    out=[];p=start
    for r in lengths:
        block=[]
        for j in range(r):block.append(p);p=E(p)
        out.append(block);p=rot(block[-1])
    return out
def inspect(lengths,start=tuple(range(6))):
    runs=blocks(lengths,start);allports=sum(runs,[])
    prior={hx(p) for block in runs[:-1] for p in block};last={hx(p) for p in runs[-1]}
    repeated=len(last&prior);assert repeated>=1
    return dict(lengths=lengths,entry_collision=len(set(allports))!=len(allports),
      last_run_extra_overlap=repeated-1,union_excess=len(allports)-len({hx(p) for p in allports}),
      entries=[''.join(map(str,p)) for p in allports])
def independent(lengths):
    # Literal full exits derive free w2 and dirty w2 using endpoint suffixes.
    p='012345';runs=[]
    for r in lengths:
        one=[]
        for j in range(r):
            one.append(p);end=(p+p[:5])[-6:];p=end[2:]+end[1]+end[0]
        runs.append(one);end=(one[-1]+one[-1][:5])[-6:];p=end[2:]+end[:2]
    canon=lambda x:min(x[j:]+x[:j] for j in range(6))
    prior=set(map(canon,sum(runs[:-1],[])));last=set(map(canon,runs[-1]));flat=sum(runs,[])
    return dict(entry_collision=len(set(flat))!=len(flat),last_run_extra_overlap=len(last&prior)-1,union_excess=len(flat)-len(set(map(canon,flat))))
def main():
    rows=[]
    for size in (2,3):
        for lengths in itertools.product(range(1,6),repeat=size):
            r=inspect(lengths);other=independent(lengths)
            assert all(r[k]==v for k,v in other.items())
            for p in itertools.permutations(range(6)):
                check=inspect(lengths,p);assert all(check[k]==r[k] for k in other)
            rows.append(r)
    out=dict(schema='round143-sigma-run-compatibility-v1',rows=rows,templates=len(rows),renaming_checks=len(rows)*720,
      independent_match=True,capped=False,completed=True,
      scope='Two/three consecutive A joins between whole E-runs only; not all globally realizable dirty histories')
    (ROOT/'outputs/rr_round143_sigma_local_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps({k:out[k] for k in ['templates','renaming_checks','completed']}))
if __name__=='__main__':main()
