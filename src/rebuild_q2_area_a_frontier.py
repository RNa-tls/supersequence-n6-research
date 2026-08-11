#!/usr/bin/env python3
"""Round 71 (Claude): rebuild the Q2 / Area-A proof frontier.

The Rounds-35-37 coverage searches all stopped on a time cap with a NON-EMPTY
frontier (``frontier_emptied_naturally`` is False for all 33 roots, total
3,321,753 queued states).  They ran in Q1 mode, i.e. under
``search_rr_target_a_unified.q1_safe_prune_reason``, which deliberately omits
every completion-assuming test.

For the Q2 question -- "can any Area-A NR6 completion still come out of this?"
-- those Q2-only tests are available again, and applying them to a STORED
frontier is a filter, not a search.  This module therefore:

  1. re-derives every queued state's coordinates from its literal masks;
  2. applies the Q2-only prunes (Phi >= 0, arithmetic D-reachability, the
     window and orbit-credit tests) to get the Q2-admissible frontier;
  3. applies the committed sharpest capacity bound, ``capacity_slack``, whose
     exact D-form is   D <= 9 - used(q0) + 4*(R_cap + Phi)  (verified
     symbolically over the whole coordinate grid);
  4. applies two Round-70/71 additions -- the monotone dead-port bound and the
     orbit re-entry inequality -- and reports what is left.

NO SEARCH IS RUN and no node-capped expansion is used as a proof step: every
state processed here was already stored by an earlier round.

Helpers deliberately NOT used: the retracted ``true_phase_walk_capacity``
phase-capacity helper and any phase-derived port-count bound; the old parity
conjecture; the v1/v2 completeness claims; the invalidated hierarchy
macro-entry source semantics.

SCOPE: everything here is Q2 / Area-A.  It says nothing about Q1 -- the
frontier states remain perfectly good Q1 objects.
"""
import json,sys,glob,os
from collections import Counter, defaultdict
from pathlib import Path
import importlib.util
ROOT=Path("/home/user/supersequence-n6-research")
s=importlib.util.spec_from_file_location("sru",ROOT/"src"/"search_rr_target_a_unified.py")
sru=importlib.util.module_from_spec(s); sys.modules["sru"]=sru; s.loader.exec_module(sru)
exact,core,macro=sru.exact,sru.core,sru.macro; AREA_A=macro.AREA_A
NORB=len(core.E_REPS)
PORTS=[core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]
PORT_HEXBIT=[[exact.HEX_POSITION[PORTS[q][ph]] for ph in range(5)] for q in range(NORB)]
PORT_HEX=[[h for h,_ in PORT_HEXBIT[q]] for q in range(NORB)]
ORBPH={w:exact.ORBIT_PHASE[w] for w in core.ALL_WORDS}
pc=int.bit_count
TP,TO,TD=exact.TARGET_P,exact.TARGET_O,exact.TARGET_D
NLIM=AREA_A.n_limit
agg=Counter(); per_root=defaultdict(Counter); classes=Counter(); resid_examples=[]
dd_dist=Counter(); reentry_dist=Counter()
for fp in sorted(glob.glob(str(ROOT/"outputs"/"rr_target_a_checkpoints"/"*.json"))):
    key=os.path.basename(fp)[:-5]
    d=json.load(open(fp))
    for e in d["frontier"]:
        st=e["state"]; hm=st["hex_masks"]; om=st["orbit_masks"]; F=st["F"]; S=st["S"]; H=st["H"]
        P=sum(pc(m) for m in om); vis=sum(pc(m) for m in hm)
        O=sum(1 for m in om if m); T=sum(1 for m in hm if m)
        D=5*O-P; Nd=S+F-O; Phi=5+6*(TP-P)-(720-vis)
        # Q2 admissibility (area_a_prune_reason minus f1_normal_form, already Q1-applied)
        if F>1 or H>0 or P>TP or O>TO or Nd>NLIM: continue
        rr=TP-P; num=TD-D+rr
        if not(rr>=0 and num%5==0 and 0<=num//5<=rr): continue
        if 720-vis<TP-P: continue
        if Phi<0: continue
        if (TO-O)>(TP-P)+(1-F): continue
        agg["q2_admissible"]+=1; per_root[key]["q2_admissible"]+=1
        q0,_=ORBPH[tuple(st["p"])]; used=pc(om[q0])
        Rcap=max(NLIM-Nd,0)
        # committed sharpest bound (capacity_slack, exact form)
        slack=(5-used)+5*(TO-O)+4*(Rcap+Phi)-(TP-P)
        if slack<0:
            agg["closed_capacity_slack"]+=1; per_root[key]["closed_capacity_slack"]+=1; continue
        agg["survives_capacity_slack"]+=1; per_root[key]["survives_capacity_slack"]+=1
        # dead-port census over OPEN orbits only
        Ddead=0; u=[]
        for q in range(NORB):
            m=om[q]
            if not m: continue
            dq=0; uq=0
            for ph in range(5):
                if m&(1<<ph): continue
                h,b=PORT_HEXBIT[q][ph]
                if hm[h]&(1<<b): dq+=1
                else: uq+=1
            Ddead+=dq
            if q!=q0 and uq>0: u.append(uq)
        dd_dist[Ddead]+=1
        if Ddead>TD:
            agg["closed_dead_port"]+=1; per_root[key]["closed_dead_port"]+=1; continue
        # ORBIT RE-ENTRY inequality: orbits (other than the current) still holding live
        # unregistered ports must either be re-entered (cost 1 of Rcap+Phi) or abandoned
        # (their live ports die, charged against the remaining dead budget 4 - Ddead)
        budget=TD-Ddead; u.sort(); k=0; acc=0
        for x in u:
            if acc+x<=budget: acc+=x; k+=1
            else: break
        need=len(u)-k
        reentry_dist[need-(Rcap+Phi)]+=1
        if need>Rcap+Phi:
            agg["closed_orbit_reentry"]+=1; per_root[key]["closed_orbit_reentry"]+=1; continue
        agg["RESIDUAL"]+=1; per_root[key]["RESIDUAL"]+=1
        classes[(Nd,Phi,Rcap,O,P,D,Ddead,need,used)]+=1
        if len(resid_examples)<40:
            resid_examples.append(dict(root=key,P=P,O=O,D=D,Ndef=Nd,Phi=Phi,r=P-T,used=used,
                                       Ddead=Ddead,reentry_need=need,budget=Rcap+Phi,slack=slack))
    print(f"{key:16s} {dict(per_root[key])}",flush=True)
    del d
json.dump({"aggregate":dict(agg),"per_root":{k:dict(v) for k,v in per_root.items()},
           "residual_classes":{str(k):v for k,v in classes.most_common()},
           "residual_examples":resid_examples,
           "D_dead_distribution":dict(sorted(dd_dist.items())),
           "reentry_margin_distribution":dict(sorted(reentry_dist.items()))},
          open("q2_stage2.json","w"),indent=1)
print("AGG:",dict(agg)); print("distinct residual classes:",len(classes)); print("DONE")
