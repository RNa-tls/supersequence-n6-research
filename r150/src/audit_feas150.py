"""Independent finite/dual audit. No production feasibility call in any DP.
The production function bodies are separately extracted and compiled for conformance.
"""
import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations_with_replacement, product
import json
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'r150/certs'
SOURCES = ['r147/src/l6_chain_capacity_147.c','r147/src/chain2_147.c',
           'src/l6_marked_capacity_pruned_144.c','src/l6_marked_capacity_144.c',
           'src/l6_chain_capacity_144.c']

def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    p=OUT/name
    assert '--refresh' in sys.argv or not p.exists(), p
    p.write_text(json.dumps(data, indent=2)+'\n', encoding='utf8')

def dual(us, tok):
    """Independent certificate: maximize a capped-sum expression, no sorting."""
    return max((sum(min(u,lam) for u in us)-tok*lam,lam) for lam in range(5))

def subset_opt(us, tok):
    """Knapsack DP: spend a token to erase one whole orbit, or keep its cost."""
    dp=[0]+[10**6]*tok
    for u in us:
        nd=[10**6]*(tok+1)
        for j,v in enumerate(dp):
            nd[j]=min(nd[j],v+u)
            if j<tok: nd[j+1]=min(nd[j+1],v)
        dp=nd
    return min(dp)

def body(s):
    a=s.index('static int feas('); b=s.index('{',a); level=1; end=b+1
    while level:
        level+=(s[end]=='{')-(s[end]=='}');end+=1
    return a,end,s[a:end]

def conformance(compiler):
    code=['#include <stdio.h>\n#define NQ2 144\nstatic int nopened, opened[144], ocnt[144], DM, DMAX;\nstatic unsigned char phm[144];\nstatic int pc5(unsigned x){int z=0;while(x){z+=x&1;x>>=1;}return z;}']
    calls=[]
    for i,rel in enumerate(SOURCES):
        raw=(ROOT/rel).read_bytes();s=raw.decode('utf8').replace('\r\n','\n');a,end,fun=body(s)
        code.append(fun.replace('feas(',f'feas_{i}('))
        calls.append(dict(file=rel,sha256=sha256(raw).hexdigest(),definition_line=s[:a].count('\n')+1,
                          call_lines=[j+1 for j,line in enumerate(s.splitlines()) if 'feas(' in line and 'static int' not in line],
                          original_function=fun,mathematical_condition='TOP_K_ERASURE_LOWER_BOUND <= DMAX'))
    code.append('int main(void){int k,d,c,n,u;while(scanf("%d%d%d%d",&k,&d,&c,&n)==4){DM=DMAX=d;for(int j=0;j<144;j++){ocnt[j]=phm[j]=0;}nopened=n+1;for(int j=0;j<=n;j++){if(j<n)scanf("%d",&u);else u=c;opened[j]=j;ocnt[j]=5-u;phm[j]=(1u<<(5-u))-1;}printf("%d %d %d %d %d\\n",feas_0(k,n),feas_1(k,n),feas_2(k,n),feas_3(k,n),feas_4(k,n));}return 0;}')
    build=ROOT/'r150/build';build.mkdir(parents=True,exist_ok=True)
    cp=build/'extracted_feas.c';cp.write_text('\n'.join(code),encoding='utf8',newline='\n')
    exe=build/'extracted_feas.exe'
    subprocess.run([compiler,'cc','-O2','-std=c11',str(cp),'-o',str(exe)],check=True)
    cases=[]; primary=[]; mutants={}; relations=Counter()
    for n in range(9):
        for us in combinations_with_replacement(range(5),n):
            for k in range(6):
                lb,lam=dual(us,k);opt=subset_opt(us,k)
                assert lb==opt
                assert dual(us,k+1)[0]<=lb
                relations['dual_DP_equality']+=1
                # Local potential transitions cover fresh, old-different, old-current and free E.
                for curdef in range(5):
                    assert dual(us+(curdef,),k)[0]>=lb
                    relations['fresh']+=1
                    if k:
                        assert dual(us,k-1)[0]>=lb
                        relations['old_current']+=1
                        for j in range(len(us)):
                            if us[j]:
                                assert dual(us[:j]+us[j+1:]+(curdef,),k-1)[0]>=lb
                                relations['old_different']+=1
                    for dm in sorted({0,max(0,lb-1),lb,lb+1,40}):
                        cases.append((us,k,dm,curdef,lb<=dm))
                primary.append((us,k,lb,lam))
    rng=random.Random(150)
    for n in (9,25,72,143):
        for _ in range(30):
            us=tuple(rng.randrange(5) for _ in range(n))
            for k in range(6):
                lb,lam=dual(us,k);assert lb==subset_opt(us,k)
                for dm in (0,20,40,lb,max(0,lb-1)):
                    cases.append((us,k,dm,rng.randrange(5),lb<=dm))
    data=''.join(f'{k} {dm} {c} {len(us)} '+ ' '.join(map(str,us))+'\n' for us,k,dm,c,_ in cases)
    run=subprocess.run([str(exe)],input=data,text=True,capture_output=True,check=True)
    lines=run.stdout.splitlines();assert len(lines)==len(cases)
    for line,case in zip(lines,cases):assert list(map(int,line.split()))==[int(case[-1])]*5,(line,case)
    # Targeted unsafe and safe/equivalent mutants; witnesses are optimistic-model completions.
    functions={
      'reverse_final_inequality':lambda us,k,d,c: dual(us,k)[0]>=d,
      'strict_lt':lambda us,k,d,c: dual(us,k)[0]<d,
      'lower_bound_plus_one':lambda us,k,d,c: dual(us,k)[0]+1<=d,
      'lower_bound_minus_one':lambda us,k,d,c: max(0,dual(us,k)[0]-1)<=d,
      'budget_minus_one':lambda us,k,d,c: dual(us,k)[0]<=d-1,
      'budget_plus_one':lambda us,k,d,c: dual(us,k)[0]<=d+1,
      'minimum_instead_of_maximum_dual':lambda us,k,d,c: min(sum(min(u,z) for u in us)-k*z for z in range(5))<=d,
      'erase_smallest_instead_of_largest':lambda us,k,d,c: sum(sorted(us)[min(k,len(us)):])<=d,
      'delete_token_term':lambda us,k,d,c: sum(us)<=d,
      'double_token_term':lambda us,k,d,c: dual(us,2*k)[0]<=d,
      'double_deficit_term':lambda us,k,d,c: 2*dual(us,k)[0]<=d,
      'delete_deficit_term':lambda us,k,d,c: 0<=d,
      'include_current_orbit':lambda us,k,d,c: dual(us+(c,),k)[0]<=d,
      'used_instead_of_remaining_tok_at_initial':lambda us,k,d,c: dual(us,0)[0]<=d,
      'used_instead_of_deficit_budget':lambda us,k,d,c: dual(us,k)[0]<=0,
      'wrong_deficit_4_minus_popcount':lambda us,k,d,c: dual(tuple(max(0,u-1) for u in us),k)[0]<=d,
      'wrong_deficit_6_minus_popcount':lambda us,k,d,c: dual(tuple(u+1 for u in us),k)[0]<=d,
      'ascending_histogram':lambda us,k,d,c: sum(sorted(us)[min(k,len(us)):])<=d,
    }
    # Smallest by used ports, opened orbits, budget; these are abstract, not word counterexamples.
    controls=sorted(((us,k,d,c) for us,k,d,c,ok in cases if ok and len(us)<=3),
                    key=lambda x:(sum(5-u for u in x[0])+5-x[3],len(x[0])+1,x[1]+x[2],x))
    safe={'lower_bound_minus_one','budget_plus_one','minimum_instead_of_maximum_dual','double_token_term','delete_deficit_term','wrong_deficit_4_minus_popcount'}
    for name,fn in functions.items():
        bad=next((x for x in controls if not fn(*x)),None)
        expected='SAFE_WEAKENING' if name in safe else 'UNSOUND_MUTANT'
        assert (bad is None)==(name in safe),(name,bad)
        mutants[name]=dict(expected=expected,actual='NO_FALSE_REJECTION_BY_MONOTONE_RELAXATION' if bad is None else 'DETECTED',
                           witness=None if bad is None else dict(noncurrent_deficits=bad[0],tok=bad[1],DMAX=bad[2],current_deficit=bad[3],exact_optimistic_minimum=subset_opt(bad[0],bad[1])),
                           scope='OPTIMISTIC_ABSTRACT_MODEL; NOT_A_PRODUCTION_COUNTEREXAMPLE')
    save('source_conformance.json',dict(sources=calls,cases=len(cases),implementations=5,disagreements=0,
        finite_domain='all deficit multisets of at most 8 noncurrent orbits, every current deficit 0..4, tok 0..5, boundary DMAX tests; plus seeded maximal-size cases',
        potential_transition_checks=relations,mutation_results=mutants,harness_sha256=sha256(cp.read_bytes()).hexdigest(),exe_sha256=sha256(exe.read_bytes()).hexdigest(),ok=True))
    print('source conformance',len(cases),dict(relations),flush=True)

def arbitrary_states(m, slots, max_tokens):
    """Exact bitmask DP on an optimistic finite phase graph, NOT the feas bound.
    All paid jumps are allowed. Fresh orbit jumps free; used-orbit jumps cost 1.
    The free phase-successor stays in the current orbit. No pruning at all.
    """
    total=m*slots; allmask=(1<<total)-1; expanded=0
    @lru_cache(None)
    def finish(mask,cur,k):
        nonlocal expanded
        expanded+=1
        opened=sum(bool(mask & (((1<<m)-1)<<(m*q))) for q in range(slots))
        best=m*opened-mask.bit_count(); choice=None
        free=(cur//m)*m+(cur+1)%m
        for v in range(total):
            if mask>>v&1:continue
            old=bool(mask & (((1<<m)-1)<<(m*(v//m))))
            cost=int(old and v!=free)
            if cost>k:continue
            got=finish(mask|1<<v,v,k-cost)[0]
            if got<best:best,choice=got,v
        return best,choice
    cases=reject=0; minimum=None; max_gap=0
    for mask in range(1,allmask+1):
        counts=[((mask>>(q*m))&((1<<m)-1)).bit_count() for q in range(slots)]
        for cur in range(total):
            if not mask>>cur&1:continue
            us=tuple(m-n for q,n in enumerate(counts) if n and q!=cur//m)
            for k in range(max_tokens+1):
                # m=3 uses a general dual with lambda 0..m-1, independent from C.
                lb=max(sum(min(u,z) for u in us)-k*z for z in range(m))
                actual=finish(mask,cur,k)[0];cases+=1
                max_gap=max(max_gap,actual-lb)
                if lb>actual:
                    item=(mask.bit_count(),sum(x>0 for x in counts),k,mask,cur,lb,actual)
                    if minimum is None or item<minimum:minimum=item
                reject+=max(0,lb) # all d=0..lb-1 are infeasible, checked against exact minimum
    assert minimum is None,minimum
    return dict(m=m,slots=slots,tok_range=[0,max_tokens],arbitrary_states=cases,exact_DP_states=expanded,
                rejected_state_budget_pairs=reject,max_relaxation_gap=max_gap,false_rejections=0,
                domain='ALL masks with current port present; not generated by the production search; full finite completion DAG, no caps',
                production_feas_called=False,completed=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',required=True);ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
    t=time.monotonic();conformance(args.compiler)
    results=[arbitrary_states(3,4,2),arbitrary_states(5,2,5)]
    save('arbitrary_states.json',dict(results=results,seconds=time.monotonic()-t,ok=True))
    print('arbitrary states',results,flush=True)

if __name__=='__main__':main()
