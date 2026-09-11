"""Exact finite arithmetic domain, not a claim of geometric realizability."""
import hashlib,itertools,json,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def domain():
    partitions=[];rows=[]
    for t in (2,3,4):
        for k,Z,H,B in itertools.product(range(t+1),repeat=4):
            if k+Z+H+B!=t:continue
            partitions.append(dict(L=867+t,t=t,k=k,Z=Z,H=H,Bstar=B))
            for G in range(5*k+1):
                for D2 in range(G+1):
                    c=G-Z-D2
                    if c<0:continue
                    for g in range(G//2+1):
                        d=Z+D2-2*g
                        if d<0:continue
                        for Qs in range(min(Z,2*g-D2)+1):
                            for s in range(B+1):
                                for h in range(H+1):
                                    if (H==0)!=(h==0) or H>3*h:continue
                                    m=Z+D2+1+h
                                    if m==1 and s:continue
                                    rows.append(dict(L=867+t,t=t,k=k,Z=Z,H=H,Bstar=B,G=G,D2=D2,
                                      c=c,g=g,d=d,Qs=Qs,s=s,h=h,b_sum=B-s,m_max=m,D_sum=5*k-G+5*s,
                                      P_required=120+G-5*c,R_upper=5*t-c-4*Z-2*H,
                                      scope='NECESSARY_ARITHMETIC_NOT_LITERAL_FEASIBILITY'))
    # Independent exact weak-composition enumeration for the four resource terms.
    check=[]
    for t in (2,3,4):
        for a in range(t+1):
            for b in range(t-a+1):
                for c in range(t-a-b+1):check.append((t,a,b,c,t-a-b-c))
    assert {(r['t'],r['k'],r['Z'],r['H'],r['Bstar']) for r in partitions}==set(check)
    return partitions,rows
def main():
    p,r=domain();out=dict(schema='round143-threshold-arithmetic-v1',completed=True,capped=False,
      source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      partitions=p,partition_counts=dict(Counter(str(x['L']) for x in p)),rows=r,
      row_counts=dict(Counter(str(x['L']) for x in r)),deterministic_digest=digest(r),
      correction_warning='Exact MASTER identity cannot acquire an additive positive RHS term; closure needs a stronger resource/capacity inequality.',
      repeat_bounds={'869':10,'870':15,'871':20},threshold_closure='NOT_ESTABLISHED_BY_ARITHMETIC')
    (ROOT/'outputs/rr_round143_threshold_budgets_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps({k:out[k] for k in ['partition_counts','row_counts','deterministic_digest']}))
if __name__=='__main__':main()
