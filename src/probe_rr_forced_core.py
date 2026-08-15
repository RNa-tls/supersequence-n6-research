#!/usr/bin/env python3
"""라운드 89 — FORCED CORE 의 동역학.

라운드 88 은 표본 1,000 에서 forced 궤도가 실재함을 보였다.  이 모듈은 그것을 전체 잔여로
확장하고, forced core 자체가 동적 제약을 위반하는지 검사한다.

핵심 관찰: cover 를 **완전 열거**하면 forced/forbidden 을 한 번에 얻는다 --

    FORCED    = 모든 cover 비트마스크의 교집합
    FORBIDDEN = candidate 에서 모든 cover 의 합집합을 뺀 것
    OPTIONAL  = 나머지

열거가 캡에 닿지 않고 끝나면 이는 §10 이 요구하는 완전 유한 판정이며, 상태당 260회의
개별 solver 호출(궤도마다 금지/강제 각 1회)을 1회 열거로 대체한다.  캡에 닿으면 UNKNOWN.

사용법:  `python3 src/probe_rr_forced_core.py [LIMIT] [nodyn]`.  두 번째 인자를 생략하면 각
cover 에 대해 라운드 88 의 결합 필요조건(공유 short-edge 예산 2 아래의 G5
induced-reachability + source-port 매칭)을 함께 평가해 **동적으로 허용되는 cover 수**를
센다.  이 값이 0이면 그 상태는 닫히고, 1이면 다음 구조 정리의 자연스러운 표적이 된다.
`nodyn` 은 그 평가를 끄고 정적 census 만 돌린다(전수 6,657 은 이 모드로 938초).
"""

import sys, json, time, importlib.util
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
sys.setrecursionlimit(10000)
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location("uc",ROOT/"src"/"probe_rr_universal_cover.py")
uc=importlib.util.module_from_spec(s); sys.modules["uc"]=uc; s.loader.exec_module(uc)
po=uc.po; slack=uc.slack; NORB=uc.NORB; BB=slack.BLOCKBITS; pc=int.bit_count
COVERCAP=5000; NODECAP=1_500_000

def enumerate_covers(U,K,b,cand,a_bits,do_dyn=True):
    byhex=defaultdict(list)
    for q in cand:
        m=BB[q]&U
        while m:
            low=m&-m; byhex[low.bit_length()-1].append(q); m^=low
    st={"n":0,"sol":0,"done":True,"inter":None,"union":0,"dyn":0,"dyn_inter":None,"dyn_union":0}
    def rec(rem,k,chosen):
        if rem==0:
            st["sol"]+=1
            bm=0
            for q in chosen: bm|=1<<q
            st["inter"]=bm if st["inter"] is None else (st["inter"]&bm)
            st["union"]|=bm
            if do_dyn:
                ok,_=uc.cover_feasible(chosen,a_bits)
                if ok:
                    st["dyn"]+=1
                    st["dyn_inter"]=bm if st["dyn_inter"] is None else (st["dyn_inter"]&bm)
                    st["dyn_union"]|=bm
            if st["sol"]>=COVERCAP: st["done"]=False; return True
            return False
        st["n"]+=1
        if st["n"]>NODECAP: st["done"]=False; return True
        bb=5*k-pc(rem)
        if bb<0: return False
        best=None;bn=99;m=rem
        while m:
            low=m&-m; h=low.bit_length()-1; m^=low
            ok2=[q for q in byhex[h] if pc(BB[q]&rem)>=5-bb]
            if len(ok2)<bn:
                best,bn=ok2,len(ok2)
                if bn==0: break
        if bn==0: return False
        for q in (best or []):
            chosen.append(q)
            if rec(rem&~BB[q],k-1,chosen): return True
            chosen.pop()
        return False
    rec(U,K,[])
    return st

rows=po.load_residual()
LIM=int(sys.argv[1]) if len(sys.argv)>1 else len(rows)
DYN = (len(sys.argv)<3) or sys.argv[2]!="nodyn"
rows=rows[:LIM]
t0=time.time()
forced_h=Counter(); forbid_h=Counter(); cov_h=Counter(); dyn_h=Counter()
byc=defaultdict(Counter); unknown=0; fmasks={}
for i,r in enumerate(rows):
    st=enumerate_covers(r["U"],r["K"],r["b"],r["candidates"],r["open_orbits"],DYN)
    if not st["done"]: unknown+=1; continue
    cand=set(r["candidates"])
    forced=[q for q in cand if st["inter"]>>q&1]
    forbidden=[q for q in cand if not (st["union"]>>q&1)]
    forced_h[len(forced)]+=1; forbid_h[min(len(forbidden),40)]+=1
    n=st["sol"]
    cov_h["1" if n==1 else "2-5" if n<=5 else "6-20" if n<=20 else "21-100" if n<=100 else "101-1000" if n<=1000 else ">1000"]+=1
    if DYN:
        d=st["dyn"]
        dyn_h["0" if d==0 else "1" if d==1 else "2-5" if d<=5 else "6-20" if d<=20 else "21-100" if d<=100 else ">100"]+=1
        byc[r["c"]]["dyn1" if d==1 else "dyn0" if d==0 else "dyn>1"]+=1
    if forced: fmasks[r["sid"]]=dict(root=r["root"],c=r["c"],forced=forced,
                                     covers=n,dyn=st["dyn"] if DYN else None)
    if (i+1)%500==0: print(f"  {i+1}/{len(rows)} {time.time()-t0:.0f}s forced>=1={sum(v for k,v in forced_h.items() if k>0)}",flush=True)
nz=sum(v for k,v in forced_h.items() if k>0)
print(f"\n총 {len(rows)}개, {time.time()-t0:.0f}s, UNKNOWN {unknown}")
print("FORCED 궤도 수 분포:",dict(sorted(forced_h.items())))
print("FORCED>=1 상태:",nz)
print("FORBIDDEN 분포(40+ 병합):",dict(sorted(forbid_h.items())))
print("cover 수 분포:",dict(cov_h))
if DYN: print("동적 허용 cover 수 분포:",dict(dyn_h)); print("c밴드별:",{k:dict(v) for k,v in sorted(byc.items())})
json.dump(dict(n=len(rows),seconds=round(time.time()-t0),unknown=unknown,
 forced=dict(sorted(forced_h.items())),forced_ge1=nz,
 forbidden=dict(sorted(forbid_h.items())),covers=dict(cov_h),
 dyn_covers=dict(dyn_h) if DYN else None,
 by_c={str(k):dict(v) for k,v in sorted(byc.items())} if DYN else None,
 forced_states=fmasks),open(f"c1_census_{LIM}.json","w"),indent=1)
print("DONE")
