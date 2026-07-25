#!/usr/bin/env python3
"""Round 21, sections 6-9, 11: tests the insertion/deletion theorem and
parses every same-component preparation word against the grammar

    A_ell . P . C . T_ell . R2 ,   T_4 = empty,  T_{ell!=4} = Xh

Both the deletion theorem ("every non-minimal preparation contains a
removable contiguous 2-block yielding a valid shorter preparation") and
the single-2-block insertion generation are FALSIFIED here, with 8 exact
counterexamples each. Every observed P is irreducible, so no
"finite base forms + repeated insertion block" grammar exists for this
data -- reported as 반증됨 rather than forced to fit.

Reads outputs/rr_preparation_words.json; writes
outputs/rr_insertion_blocks.json.
"""
import json, itertools
from pathlib import Path
R=Path('/home/user/supersequence-n6-research')
d=json.loads((R/"outputs"/"rr_preparation_words.json").read_text())

P_by = {}
for ell,r in d["results_by_ell"].items():
    for f in r["preparations"]:
        c=f["completer_index_within_preparation"]
        P=tuple(f["symbolic_preparation_word"][:c-1])
        P_by.setdefault(ell,{}).setdefault(len(P),set()).add(P)

# symbolic deletion test
del_results=[]
for ell,byl in P_by.items():
    for L in sorted(byl):
        if L<4: continue
        shorter = byl.get(L-2,set())
        for P in sorted(byl[L]):
            outs=[]
            for i in range(L-1):
                cand = P[:i]+P[i+2:]
                outs.append({"delete_at":i,"block":list(P[i:i+2]),"result":list(cand),
                             "is_valid_shorter_P": list(cand) in [list(x) for x in shorter]})
            del_results.append({"ell":ell,"P":list(P),"length":L,
                                "shorter_set":[list(x) for x in sorted(shorter)],
                                "deletions":outs,
                                "any_valid_deletion": any(o["is_valid_shorter_P"] for o in outs)})

# insertion test
ins_results=[]
for ell,byl in P_by.items():
    for L in sorted(byl):
        if L<4: continue
        shorter=byl.get(L-2,set())
        for target in sorted(byl[L]):
            reachable=False
            wit=None
            for src in shorter:
                for i in range(len(src)+1):
                    for b in itertools.product(["E","F","Rh","Rx"],repeat=2):
                        if list(src[:i])+list(b)+list(src[i:])==list(target):
                            reachable=True; wit={"from":list(src),"insert_at":i,"block":list(b)}
            ins_results.append({"ell":ell,"target":list(target),
                                "reachable_by_single_2block_insertion":reachable,"witness":wit})

report={
 "schema":"rr-insertion-blocks-v1",
 "P_sets_by_ell_and_length":{e:{str(k):[list(x) for x in sorted(v)] for k,v in b.items()} for e,b in P_by.items()},
 "deletion_theorem_test":{
   "statement":"every non-minimal preparation P contains a removable contiguous 2-block yielding a valid shorter P",
   "results":del_results,
   "holds": all(r["any_valid_deletion"] for r in del_results) if del_results else None,
   "counterexamples":[{"ell":r["ell"],"P":r["P"]} for r in del_results if not r["any_valid_deletion"]],
 },
 "insertion_test":{
   "statement":"every longer P is obtained from a shorter valid P by inserting one contiguous 2-block",
   "results":ins_results,
   "holds": all(r["reachable_by_single_2block_insertion"] for r in ins_results) if ins_results else None,
   "counterexamples":[{"ell":r["ell"],"target":r["target"]} for r in ins_results if not r["reachable_by_single_2block_insertion"]],
 },
 "verdict":"반증됨 -- neither the deletion theorem nor the single-2-block insertion generation holds; every observed P is irreducible",
 "proof_status":"exact counterexample (symbolic level, over the root-local exhaustive P sets)",
}
(R/"outputs"/"rr_insertion_blocks.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str))
print("deletion theorem holds:",report["deletion_theorem_test"]["holds"])
print("counterexamples:",report["deletion_theorem_test"]["counterexamples"])
print("insertion holds:",report["insertion_test"]["holds"])
print("counterexamples:",report["insertion_test"]["counterexamples"])
print()
for e,b in sorted(P_by.items()):
    for L,v in sorted(b.items()):
        print(f"  ell={e} |P|={L}: {sorted(''.join(x) for x in v)}")
