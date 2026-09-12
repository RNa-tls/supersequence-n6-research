"""Independent literal cycle replay plus small exhaustive tuple oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from run_round143_general_prefix_codex import replay,WORDS,INDEX
from verify_round143_general_ports_small_codex import geometry

ROOT=Path(__file__).resolve().parents[1]


def replay_cycle(entries,A,Q,R,H,b,D):
    state=replay(entries);last=WORDS[entries[-1]];first=WORDS[entries[0]]
    ep=last[-1:]+last[:-1]
    w=next(w for w in range(1,7) if ep[w:]==first[:6-w])
    assert w>=2
    ca=w==2 and first==last[1:]+last[:1]
    cb=w==3 and first==last[2:]+last[:2]
    assert not(w==2 and not ca),'A non-E opening is required'
    if A:assert ca
    elif Q:assert cb
    state['A']+=ca;state['Qs']+=cb;state['H']+=max(0,w-3)
    assert state['A']==A and state['Qs']==Q
    assert A+Q<=state['R']<=R and state['H']<=H and state['b']<=b and state['D']<=D
    state.update(closing_weight=w,closing_A=ca,closing_B=cb)
    return state


def brute(query,geo):
    A,Q,R,H,B,D,P=query;hexa,orbits,edges=geo;first=WORDS[0];answer=set()
    relevant={p:[e for e in el if max(0,e[1]-3)<=H] for p,el in edges.items()}
    def visit(path,opened,covered,b,a,q,r,h):
        if 5*len(opened)>P+D:return
        if len(path)==P:
            for t,w,free,ca,cq in relevant[path[-1]]:
                if t!=first or free or (A and not ca) or (not A and Q and not cq):continue
                if a+ca==A and q+cq==Q and h+max(0,w-3)<=H and r>=A+Q:
                    answer.add(tuple(INDEX[x] for x in path))
            return
        for t,w,free,ca,cq in relevant[path[-1]]:
            if t in path:continue
            aa=a+ca;qq=q+cq;rr=r+(hexa[t] in covered);hh=h+max(0,w-3)
            bb=b+(not free and orbits[t] in opened)
            if aa>A or qq>Q or rr>R or hh>H or bb>B:continue
            visit(path+(t,),opened|{orbits[t]},covered|{hexa[t]},bb,aa,qq,rr,hh)
    visit((first,),{orbits[first]},{hexa[first]},0,0,0,0,0)
    return answer


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='outputs/rr_round143_cycle_controls_codex.json');args=ap.parse_args()
    binaries=[ROOT/'outputs/round143_cycle_runs_check.exe',ROOT/'outputs/round143_cycle_ports_check.exe']
    table=ROOT/'outputs/rr_round143_general_suffix_v1.txt';geo=geometry();checks=[]
    queries=[(0,0,0,0,0,0,5),(0,0,0,0,0,0,20),(2,0,2,0,0,0,10),
             (1,0,1,0,0,0,5),(0,1,1,0,0,0,5),(0,0,0,1,0,0,5)]
    with tempfile.TemporaryDirectory(prefix='r143_cycles_') as folder:
        folder=Path(folder)
        for n,query in enumerate(queries):
            A,Q,R,H,b,D,P=query;expected=brute(query,geo);reports=[]
            for side,exe in enumerate(binaries):
                for bounded in (False,True):
                    output=folder/f'{n}_{side}_{bounded}.jsonl'
                    command=[str(exe),str(b),str(D),'0',str(A),str(Q),str(R),str(H),str(P),str(output)]
                    if bounded:command.append(str(table))
                    proc=subprocess.run(command,check=True,capture_output=True,text=True);meta=json.loads(proc.stdout)
                    paths=[]
                    for line in output.read_text().splitlines():
                        record=json.loads(line);p=record['entries'] if isinstance(record,dict) else record
                        replay_cycle(p,A,Q,R,H,b,D);paths.append(tuple(p))
                    assert len(paths)==len(set(paths))==meta['exported_prefixes']
                    assert meta['completed'] and not meta['capped'] and set(paths)==expected,(query,side,bounded)
                    reports.append(dict(side=side,bounded=bounded,nodes=meta['nodes'],exports=len(paths)))
            checks.append(dict(query=query,oracle_cycles=len(expected),runs=reports))
        # P=0 is the independently counted capacity mode. Its complete grids
        # must agree; closing A/B costs are included but b/D/R are unchanged.
        grids=[];summaries=[]
        for side,exe in enumerate(binaries):
            output=folder/f'capacity_{side}.jsonl'
            command=[str(exe),'0','0','0','2','0','2','0','0',str(output)]
            meta=json.loads(subprocess.check_output(command,text=True));grid={}
            for line in output.read_text().splitlines():
                row=json.loads(line);s=replay_cycle(row['entries'],2,0,2,0,0,0)
                grid[s['b'],s['D']]=s['P']
            assert meta['completed'] and not meta['capped'];grids.append(grid);summaries.append(meta)
        assert grids[0]==grids[1] and summaries[0]['accepted_cycles']==summaries[1]['accepted_cycles']
    out=dict(schema='round143-independent-cycle-controls-v1',verified=True,controls=checks,
             cycle_capacity_grid=[dict(b=b,D=d,P=p) for (b,d),p in sorted(grids[0].items())],capacity_summaries=summaries,
             source_sha256={rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in
                ['src/round143_cycle_runs_codex.c','src/round143_cycle_ports_independent.c','src/verify_round143_cycle_controls_codex.py']},
             scope='Small complete literal oracle and paired cycle-grid check; no threshold closure asserted')
    (ROOT/args.output).write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,controls=len(checks),cycle_counts=[c['oracle_cycles'] for c in checks],grid=out['cycle_capacity_grid'])))


if __name__=='__main__':main()
