#!/usr/bin/env python3
"""Round P -- A-identity conflict witness on the stored relaxed-optimal phi path (value 20): identity-free
vs identity-aware value for the same phi order and gap layout, and the per-gap cheapest A trails.
usage: relaxed_witness.py SCRATCH (reads pdp/T1.bin, Ed.bin, cut.bin, trail.bin, sym7_opt_path.json)"""
import numpy as np, json, itertools, sys
SP=sys.argv[1]; P=2016; NO=84
T1=np.fromfile(f'{SP}/pdp/T1.bin',np.uint8).reshape(6,P,P).astype(np.int32)
Ed=np.fromfile(f'{SP}/pdp/Ed.bin',np.uint8).reshape(P,P).astype(np.int32)
cut=np.fromfile(f'{SP}/pdp/cut.bin',np.int32); trail=np.fromfile(f'{SP}/pdp/trail.bin',np.int32)
Aid=[1,8,15,22,28,29]; phit=[t for t in range(30) if t not in Aid]
d=json.load(open(f'{SP}/pdp/sym7_opt_path.json')); order=[phit.index(t) for t in d['phi_order']]; gaps=d['gap_A']
assert d['start_A']==0 and d['end_A']==0 and all(g in (0,1) for g in gaps)
rows=lambda i: slice(i*NO,(i+1)*NO)
topts=[np.nonzero(trail==phit[i])[0] for i in range(24)]
s0=(cut[topts[order[0]]]==2).astype(np.int32)
# identity-free (relaxed) DP over options
def relaxed():
    v=s0.copy(); back=[]
    for k in range(23):
        a,b=order[k],order[k+1]
        M=(T1[:,rows(a),rows(b)].min(0) if gaps[k] else Ed[rows(a),rows(b)])
        w=v[:,None]+M; back.append(w.argmin(0)); v=w.min(0)
    return int(v.min()), v, back
rv,_,_=relaxed()
# identity-aware DP: state (option, mask)
INF=10**6
V={0:s0.copy()}
for k in range(23):
    a,b=order[k],order[k+1]; NV={}
    for m,v in V.items():
        if not gaps[k]:
            w=(v[:,None]+Ed[rows(a),rows(b)]).min(0); NV[m]=np.minimum(NV.get(m,np.full(NO,INF)),w)
        else:
            for al in range(6):
                if m>>al&1: continue
                w=(v[:,None]+T1[al][rows(a),rows(b)]).min(0); m2=m|1<<al; NV[m2]=np.minimum(NV.get(m2,np.full(NO,INF)),w)
    V=NV
ia=min(int(v.min()) for v in V.values())
# per-gap sets of A trails achieving the relaxed per-gap minimum, along one relaxed-optimal option assignment
v=s0.copy(); hist=[v]
for k in range(23):
    a,b=order[k],order[k+1]; M=(T1[:,rows(a),rows(b)].min(0) if gaps[k] else Ed[rows(a),rows(b)]); w=v[:,None]+M; v=w.min(0); hist.append(v)
# backtrack one optimal assignment
o=int(hist[-1].argmin()); opts=[o]
for k in range(22,-1,-1):
    a,b=order[k],order[k+1]; M=(T1[:,rows(a),rows(b)].min(0) if gaps[k] else Ed[rows(a),rows(b)])
    y=int(np.argmin(hist[k]+M[:,o])); opts.append(y); o=y
opts=opts[::-1]
sets=[]
for k in range(23):
    if not gaps[k]: continue
    a,b=order[k],order[k+1]; y,x=opts[k],opts[k+1]; vals=T1[:,a*NO+y,b*NO+x]
    sets.append(dict(gap=k, cost=int(vals.min()), argmin_A=[Aid[i] for i in range(6) if vals[i]==vals.min()]))
print(json.dumps(dict(relaxed_value=rv, identity_aware_value_same_phi_order_and_gaps=ia, gap_min_sets_on_one_relaxed_optimum=sets)))
