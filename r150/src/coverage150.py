"""Recompute row-domain maxima and source/capacity dependencies, not capacities."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from audit_feas150 import SOURCES, save

ROOT=Path(__file__).resolve().parents[2]

def main():
    rows=[]
    for t in range(5):
        for k in range(t+1):
            for zcost in range(t-k+1):
                for heavy in range(t-k-zcost+1):
                    bs=t-k-zcost-heavy
                    for G in range(5*k+1):
                        for c in range(G+1):
                            for d in range(G-c+1):
                                twiceg=G-c-d
                                if twiceg%2:continue
                                a=G-c-zcost
                                if not 0<=a<=twiceg:continue
                                for bb in range(min(zcost,twiceg-a)+1):
                                    for s in range(bs+1):
                                        for hj in ([0] if heavy==0 else range(1,heavy+1)):
                                            rows.append(dict(t=t,b=bs-s,d=5*k-G+5*s,a=a,bb=bb,e=zcost-bb,h=heavy))
    maxima={x:max(r[x] for r in rows) for x in ('b','d','a','bb','e','h')}
    assert maxima==dict(b=4,d=20,a=20,bb=3,e=3,h=4),maxima
    prod={}
    for name in ('chain_cells_147.json','heavy_cells_147.json'):
        prod.update(json.loads((ROOT/'r147/tables'/name).read_text()))
    cells=json.loads((ROOT/'r147/tables/loadbearing_cells_147.json').read_text())['cells']
    assert len(cells)==len(set(map(tuple,cells)))==905
    missing=[c for c in cells if '|'.join(map(str,c)) not in prod];assert not missing
    ranges=[max(c[i] for c in cells) for i in range(6)]
    hashes=[]
    for rel in SOURCES:
        raw=(ROOT/rel).read_bytes();blob=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)
        hashes.append(dict(file=rel,worktree_sha256=sha256(raw).hexdigest(),git_blob_sha256=sha256(blob).hexdigest(),
                           only_CRLF_difference=raw.replace(b'\r\n',b'\n')==blob))
    save('coverage.json',dict(row_counts_with_s=dict(Counter(r['t'] for r in rows)),row_total=len(rows),
        t_le_4_maxima=maxima,declared_limits=[5,40,24,24,24,6],load_bearing_cells=905,
        load_bearing_budget_maxima=ranges,all_stored_capacity_cells=len(prod),
        dependence='All 905 explicit load-bearing chain/heavy cells use production A feas(); B repeats the same condition. Historical marked/piece capacities use the same lemma too.',
        no_per_prune_trace_available=True,source_hashes=hashes,ok=True))
    print(maxima,len(rows),dict(Counter(r['t'] for r in rows)))

if __name__=='__main__':main()
