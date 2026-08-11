#!/usr/bin/env python3
"""Round 72 (Claude): the SKIP-COST theorem, and the LIVE-PORT SUPPLY bound.

TWO EXACT ENGINE FACTS, re-verified in this module's companion checks:

  1. Exactly TWO of the 24 macro generators preserve the E-orbit of the
     ENDPOINT, and each does so for all 720 words with no partial cases:
         (ell=5, w2:10)  == E^1   joint_kind Z2, free
         (ell=5, w3:120) == E^2   joint_kind R,  costs exactly one unit of Ndef
     (E^2 always lands in the endpoint's own orbit, which already holds the
      endpoint as a registered port, so new_orbit is False; at ell=5
      abandonment is False because sigma^6(p) = p is visited; and R has
      dS=+1, dO=0, dF=0, so Ndef = S+F-O rises by exactly 1.)

  2. Consequently a "segment" -- a maximal run of orbit-preserving macro edges
     -- walks its orbit's 5-cycle forward by +1 (free) or +2 (one Ndef), and
     every joint target must be an UNVISITED permutation.

AVOIDING THE RETRACTED HELPER'S FAILURE MODE.  src/audit_rr_capacity_helpers.py
refuted true_phase_walk_capacity on long_found_142: the helper rejected a port
because its HEXAGON had popcount 5, reasoning that an ell=5 run from it needs
all six slots free; but a joint landing needs only its own target permutation
free.  It predicted 3 ports where the engine achieves 4.

Everything here therefore tests ONLY whether the target PERMUTATION is
unvisited.  It never consults hexagon popcount, never asks whether a segment
can COMPLETE a hexagon, and it deliberately DROPS the rotation-run legality
requirement -- all three choices make the reachability estimate LARGER, which
is the sound direction for an upper bound on what a walk can achieve.  Replayed
on long_found_142 the formulation here returns 4, matching the engine.

THE TWO BOUNDS

  LIVE-PORT SUPPLY.  Every future registration is a port that is unvisited now
  (a visited-unregistered port is dead forever).  So
      B  <=  sum over open orbits of live(q)  +  the O_cap largest live(q)
             over closed orbits.

  SKIP-COST.  Budget T = R_cap + Phi is shared: each orbit-changing joint into
  an already-open orbit costs one unit, and each E^2 skip costs one unit of the
  same Ndef budget -- a charge capacity_slack does not make.  With f = O_cap
  fresh segments the total registrable is bounded by a per-segment reach table
  computed on the 5-cycle from port-level liveness alone.

SCOPE: Q2 / Area-A.  No search is run; this filters states already stored by an
earlier round.  No node-capped expansion is used as a proof step.
"""
import importlib.util,sys,json,glob,os
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path("/home/user/supersequence-n6-research")
s=importlib.util.spec_from_file_location("sru",ROOT/"src"/"search_rr_target_a_unified.py")
sru=importlib.util.module_from_spec(s); sys.modules["sru"]=sru; s.loader.exec_module(sru)
exact,core,macro=sru.exact,sru.core,sru.macro; AREA_A=macro.AREA_A
NORB=len(core.E_REPS); PORTS=[core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]
PORT_HB=[[exact.HEX_POSITION[PORTS[q][ph]] for ph in range(5)] for q in range(NORB)]
PORT_HEX=[[core.hexagon_id(PORTS[q][ph]) for ph in range(5)] for q in range(NORB)]
pc=int.bit_count; TP,TO,TD,NLIM=exact.TARGET_P,exact.TARGET_O,exact.TARGET_D,AREA_A.n_limit

# ---- reach tables, port level only, precomputed for every (live mask, entry phase, skips) ----
def _reach_from(livem,phi,emax):
    best=0; stack=[(0,emax,0)]
    while stack:
        off,e,cnt=stack.pop()
        if cnt>best: best=cnt
        for step in (1,2):
            if step==2 and e==0: continue
            no=off+step
            if no>4: continue
            if (livem>>((phi+no)%5))&1: stack.append((no,e-(step-1),cnt+1))
    return best
REACH_FROM=[[[_reach_from(m,phi,e) for e in range(9)] for phi in range(5)] for m in range(32)]
BESTREACH=[[max([1+REACH_FROM[m][phi][e] for phi in range(5) if (m>>phi)&1] or [0]) for e in range(9)]
           for m in range(32)]

def process(fp):
    key=os.path.basename(fp)[:-5]
    d=json.load(open(fp)); out=Counter(); cls=Counter(); ex=[]
    for en in d["frontier"]:
        st=en["state"]; hm=st["hex_masks"]; om=st["orbit_masks"]; F=st["F"]; S=st["S"]; H=st["H"]
        P=sum(pc(m) for m in om); vis=sum(pc(m) for m in hm)
        O=sum(1 for m in om if m); D=5*O-P; Nd=S+F-O
        Phi=5+6*(TP-P)-(720-vis)
        if F>1 or H>0 or P>TP or O>TO or Nd>NLIM: continue
        rr=TP-P; num=TD-D+rr
        if not(rr>=0 and num%5==0 and 0<=num//5<=rr): continue
        if 720-vis<TP-P or Phi<0: continue
        if (TO-O)>(TP-P)+(1-F): continue
        out["q2_admissible"]+=1
        q0,ph0=exact.ORBIT_PHASE[tuple(st["p"])]; used=pc(om[q0]); Rcap=max(NLIM-Nd,0)
        B=TP-P; f=TO-O; T=Rcap+Phi
        if (5-used)+5*f+4*T-B<0: out["closed_capacity_slack"]+=1; continue
        out["survives_capacity_slack"]+=1
        # ---- port-level liveness for every orbit (unvisited ports only) ----
        LM=[0]*NORB
        for q in range(NORB):
            m=0
            for ph in range(5):
                h,b=PORT_HB[q][ph]
                if not (hm[h]>>b)&1: m|=1<<ph
            LM[q]=m
        openq=[q for q in range(NORB) if om[q]]
        closedq=[q for q in range(NORB) if not om[q]]
        # ---- (i) LIVE-PORT SUPPLY: every future registration is a currently-unvisited port ----
        liveopen=sum(pc(LM[q]) for q in openq)
        topclosed=sorted((pc(LM[q]) for q in closedq),reverse=True)[:f]
        supply=liveopen+sum(topclosed)
        if supply<B: out["closed_live_port_supply"]+=1; continue
        # ---- (ii) SKIP-COST: segments, with the budget T shared by re-entries and skips ----
        UB=-1
        for g in range(0,T+1):
            e=T-g
            cur=REACH_FROM[LM[q0]][ph0][e]
            fr=sorted((BESTREACH[LM[q]][e] for q in closedq),reverse=True)[:f]
            re_=sorted((BESTREACH[LM[q]][e] for q in openq if q!=q0),reverse=True)[:g]
            UB=max(UB,cur+sum(fr)+sum(re_))
        if UB<B: out["closed_skip_cost"]+=1; continue
        out["RESIDUAL"]+=1
        cls[(Nd,Phi,O,P,D,used,UB-B)]+=1
        if len(ex)<5: ex.append(dict(root=key,P=P,O=O,D=D,Ndef=Nd,Phi=Phi,used=used,B=B,UB=UB,supply=supply))
    print(f"{key:16s} {dict(out)}",flush=True)
    return key,out,cls,ex

agg=Counter(); per={}; allcls=Counter(); allex=[]
for fp in sorted(glob.glob(str(ROOT/"outputs"/"rr_target_a_checkpoints"/"*.json"))):
    k,o,c,e=process(fp); agg.update(o); per[k]=dict(o); allcls.update(c); allex.extend(e)
json.dump({"aggregate":dict(agg),"per_root":per,
           "residual_classes":{str(k):v for k,v in allcls.most_common()},
           "examples":allex[:40]},open("skip_cost.json","w"),indent=1)
print("AGG:",dict(agg)); print("residual classes:",len(allcls)); print("DONE")
