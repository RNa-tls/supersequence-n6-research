"""Paired nonpure-cycle capacities; preserve independently replayed grids."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from run_round143_sigma_batch_codex import ZIG,sha
from verify_round143_cycle_controls_codex import replay_cycle
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cells',required=True,help='A:Qs:R:H:b:D comma separated')
    ap.add_argument('--cap',type=int,default=0);ap.add_argument('--output',required=True);a=ap.parse_args()
    dest=ROOT/a.output;folder=dest.with_suffix('');assert not dest.exists() and not folder.exists()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
    assert head==remote
    sources=['src/round143_cycle_runs_codex.c','src/round143_cycle_ports_independent.c',
             'src/run_round143_cycle_capacities_codex.py','src/verify_round143_cycle_controls_codex.py',
             'src/run_round143_general_prefix_codex.py']
    provenance=[];binaries=[]
    for rel in sources:
        raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT);assert raw==(ROOT/rel).read_bytes()
        digest=hashlib.sha256(raw).hexdigest();item=dict(path=rel,committed_lf_sha256=digest,runtime_sha256=sha(ROOT/rel))
        if rel.endswith('.c'):
            exe=ROOT/'outputs'/('round143_'+Path(rel).stem+'_'+digest[:12]+'.exe')
            argv=[str(ZIG),'cc','-O3','-std=c11',str(ROOT/rel),'-o',str(exe)]
            if not exe.exists():subprocess.run(argv,cwd=ROOT,check=True)
            binaries.append(exe);item.update(binary_sha256=sha(exe),compile_argv=argv)
        provenance.append(item)
    folder.mkdir()
    data=dict(schema='round143-paired-cycle-capacity-v1',source_commit=head,source_provenance=provenance,argv=sys.argv,
              compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
              scope='Nonpure beta cycles; A/B closing preferred when present; exact A/Q; upper R/H/b/D; all prefix ports distinct',rows=[])
    for query in [tuple(map(int,x.split(':'))) for x in a.cells.split(',')]:
        A,Q,R,H,b,D=query;assert R>=A+Q;runs=[];grids=[]
        for side,exe in enumerate(binaries):
            export=folder/('_'.join(map(str,query))+f'_{side}.jsonl')
            argv=[str(exe),str(b),str(D),str(a.cap),str(A),str(Q),str(R),str(H),'0',str(export)]
            start=time.perf_counter();proc=subprocess.run(argv,cwd=ROOT,check=True,capture_output=True,text=True);r=json.loads(proc.stdout)
            assert r['proof_query']=='CYCLE_CAPACITY' and not r['suffix_bound_enabled']
            grid={}
            for line in export.read_text().splitlines():
                record=json.loads(line);check=replay_cycle(record['entries'],A,Q,R,H,b,D)
                key=check['b'],check['D'];assert key not in grid
                assert record['P']==check['P'] and record['b']==key[0] and record['D']==key[1]
                grid[key]=check['P']
            assert len(grid)==r['exported_prefixes'] and max(grid.values(),default=0)==r['max_passes']
            r.update(argv=argv,seconds=time.perf_counter()-start,stdout_sha256=hashlib.sha256(proc.stdout.encode()).hexdigest(),
                     export_file=export.relative_to(ROOT).as_posix(),export_sha256=sha(export),independently_replayed_grid_witnesses=len(grid))
            runs.append(r);grids.append(grid)
        complete=all(r['completed'] and not r['capped'] for r in runs)
        if complete:
            assert grids[0]==grids[1] and runs[0]['accepted_cycles']==runs[1]['accepted_cycles']
        data['rows'].append(dict(zip(('A','Qs','R','H','b','D'),query))|dict(producer=runs[0],independent=runs[1],complete=complete,
            status='VERIFIED_CYCLE_CAPACITY' if complete else 'UNKNOWN_CAP',
            exact_resource_grid=[dict(b=bb,D=dd,maximum=p) for (bb,dd),p in sorted(grids[0].items())] if complete else None))
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n',newline='\n');os.replace(temp,dest)
        print(json.dumps(dict(query=query,complete=complete,maxima=[r['max_passes'] for r in runs],nodes=[r['nodes'] for r in runs])),flush=True)


if __name__=='__main__':main()
