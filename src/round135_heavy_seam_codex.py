"""Independent extremal-chain enumeration and exact weight-4 seam test."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
from research_round135_contraction_codex import geometry,sha
from research_alpha_gap_codex import ROOT

def chains(g,target,dcap):
    hids={h:i for i,h in enumerate(sorted(set(g.h)))}
    qids={q:i for i,q in enumerate(sorted(set(g.q)))}
    hb=[1<<hids[h] for h in g.h];qb=[1<<qids[q] for q in g.q]
    nodes=0;out=[]
    def dfs(path,hm,qm,run,closedD):
        nonlocal nodes
        nodes+=1;v=path[-1]
        if len(path)==target:
            if closedD+5-run<=dcap:out.append(dict(path=path,hm=hm,qm=qm,deficit=closedD+5-run))
            return
        for t,w in g.joint[g.s(v,-1)]:
            if w>3 or hm&hb[t]:continue
            if w==2:
                assert g.q[t]==g.q[v]
                dfs(path+[t],hm|hb[t],qm,run+1,closedD)
            elif g.q[t]!=g.q[v] and not qm&qb[t] and closedD+5-run<=dcap:
                dfs(path+[t],hm|hb[t],qm|qb[t],1,closedD+5-run)
    dfs([0],hb[0],qb[0],1,0)
    return dict(target=target,deficit_cap=dcap,nodes=nodes,rows=out)

def main():
    p=argparse.ArgumentParser();p.add_argument('--join',action='store_true');a=p.parse_args()
    start=time.perf_counter();g=geometry(6)
    left=chains(g,46,4);right=chains(g,66,9)
    result=dict(schema='codex/round135-heavy-extrema/1',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=sha(__file__),driver_sha256=sha(__file__),binary_sha256=sha(sys.executable),
                full_argv=[sys.executable,*sys.argv],node_cap=None,chains=[left,right])
    print('CHAINS',[(x['target'],x['nodes'],len(x['rows'])) for x in [left,right]],flush=True)
    if a.join:
        attempts=0;hits=[];qfail=hfail=0
        cache={}
        for AA,BB in [(left,right),(right,left)]:
            for ai,A in enumerate(AA['rows']):
                end=g.s(A['path'][-1],-1)
                Ah={g.h[v] for v in A['path']};Aq={g.q[v] for v in A['path']}
                for t,w in g.joint[end]:
                    if w!=4:continue
                    if t not in cache:
                        label=g.words[t]
                        cache[t]=[g.idx[tuple(label[z] for z in word)] for word in g.words]
                    mp=cache[t]
                    for bi,B in enumerate(BB['rows']):
                        attempts+=1;bp=[mp[v] for v in B['path']]
                        if Aq&{g.q[v] for v in bp}:qfail+=1;continue
                        if Ah&{g.h[v] for v in bp}:hfail+=1;continue
                        ps=[(v,6) for v in A['path']+bp];rep=g.replay(ps);assert rep
                        hits.append(dict(left_target=AA['target'],left_index=ai,right_index=bi,seam_target=t,replay=rep))
        result['seams']=dict(attempts=attempts,orbit_collision=qfail,hex_collision=hfail,hits=hits,
                             verdict='SAT' if hits else 'UNSAT_COMPLETE')
        print('SEAMS',attempts,'hits',len(hits),flush=True)
    result['seconds']=time.perf_counter()-start
    result['deterministic_digest']=hashlib.sha256(json.dumps({k:v for k,v in result.items() if k!='seconds'},sort_keys=True).encode()).hexdigest()
    (ROOT/'outputs/rr_round135_heavy_seams_codex.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
