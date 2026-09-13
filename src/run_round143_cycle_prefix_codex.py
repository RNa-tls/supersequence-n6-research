"""Paired complete nonpure-cycle exact-P decisions with closing-aware bounds."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from run_round143_general_prefix_codex import FIELDS, sha, ZIG
from verify_round143_cycle_controls_codex import replay_cycle
from verify_round143_coupled_codex import validate_capacity_file
from prepare_round143_general_bounds_codex import build

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--queries',help='A:Qs:R:H:b:D:P comma separated')
    ap.add_argument('--pair-ledger')
    ap.add_argument('--cap',type=int,default=0)
    ap.add_argument('--table',default='outputs/rr_round143_general_suffix_v1.txt')
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    assert bool(args.queries)!=bool(args.pair_ledger)
    dest=ROOT/args.output;folder=dest.with_suffix('')
    assert not dest.exists() and not folder.exists()
    if args.pair_ledger:
        data=json.loads((ROOT/args.pair_ledger).read_text())
        queries=sorted({tuple(p['cycle']) for r in data['rows']
                        for p in r.get('remaining_component_pairs',r.get('component_exact_P_pairs',[]))})
    else:
        queries=[tuple(map(int,x.split(':'))) for x in args.queries.split(',')]
    assert all(len(q)==7 and q[-1]>0 for q in queries)
    table=ROOT/args.table;manifest=json.loads(table.with_suffix('.json').read_text());cells=[]
    assert sha(table)==manifest['table_sha256']
    for rel,digest in manifest['input_sha256'].items():
        assert sha(ROOT/rel)==digest
        if rel=='outputs/rr_round143_t4_combined_codex.json':continue
        new,_=validate_capacity_file(ROOT/rel);cells+=new
    rows,n=build(cells,manifest['queries'])
    assert table.read_text()==''.join(' '.join(map(str,r))+'\n' for r in rows)
    assert n==manifest['independent_convolution_cells']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
    assert head==remote
    sources=['src/round143_cycle_runs_codex.c','src/round143_cycle_ports_independent.c',
             'src/run_round143_cycle_prefix_codex.py','src/verify_round143_cycle_controls_codex.py',
             'src/run_round143_general_prefix_codex.py','src/prepare_round143_general_bounds_codex.py',
             'src/verify_round143_coupled_codex.py','src/verify_round143_coupled_extraction_codex.py']
    provenance=[];binaries=[]
    for rel in sources:
        raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
        assert raw==(ROOT/rel).read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        item=dict(path=rel,committed_lf_sha256=digest,runtime_sha256=sha(ROOT/rel))
        if rel.endswith('.c'):
            exe=ROOT/'outputs'/('round143_'+Path(rel).stem+'_'+digest[:12]+'.exe')
            command=[str(ZIG),'cc','-O3','-std=c11',str(ROOT/rel),'-o',str(exe)]
            if not exe.exists():subprocess.run(command,cwd=ROOT,check=True)
            binaries.append(exe);item.update(binary_sha256=sha(exe),compile_argv=command)
        provenance.append(item)
    folder.mkdir()
    data=dict(schema='round143-paired-cycle-exact-P-v1',source_commit=head,source_provenance=provenance,
              argv=sys.argv,compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
              pair_ledger=args.pair_ledger,pair_ledger_sha256=sha(ROOT/args.pair_ledger) if args.pair_ledger else None,
              bound_manifest=table.with_suffix('.json').relative_to(ROOT).as_posix(),
              bound_manifest_sha256=sha(table.with_suffix('.json')),table_sha256=sha(table),
              scope='Nonpure beta cycle exact-P necessary decisions; not scalar capacity maxima',rows=[])
    for query in queries:
        A,Q,R,H,b,D,P=query;runs=[];sets=[]
        for side,exe in enumerate(binaries):
            export=folder/('_'.join(map(str,query))+f'_{side}.jsonl')
            command=[str(exe),str(b),str(D),str(args.cap),str(A),str(Q),str(R),str(H),str(P),str(export),str(table)]
            start=time.perf_counter();proc=subprocess.run(command,cwd=ROOT,check=True,capture_output=True,text=True)
            run=json.loads(proc.stdout)
            assert run['proof_query']=='EXACT_CYCLE_P_NOT_CAPACITY' and run['suffix_bound_enabled']
            paths=[]
            for line in export.read_text().splitlines():
                record=json.loads(line);entries=record['entries'] if isinstance(record,dict) else record
                replay_cycle(entries,A,Q,R,H,b,D);assert len(entries)==P
                paths.append(tuple(entries))
            assert len(paths)==len(set(paths))==run['exported_prefixes']
            sets.append(set(paths));run.update(argv=command,seconds=time.perf_counter()-start,
                stdout_sha256=hashlib.sha256(proc.stdout.encode()).hexdigest(),
                export_file=export.relative_to(ROOT).as_posix(),export_sha256=sha(export),
                independently_replayed_exports=len(paths))
            runs.append(run)
        complete=all(r['completed'] and not r['capped'] for r in runs)
        if complete:assert sets[0]==sets[1],query
        status='UNKNOWN_CAP' if not complete else 'NO_EXACT_P_CYCLE' if not sets[0] else 'EXACT_P_CYCLES_COMPLETE'
        data['rows'].append(dict(zip(FIELDS,query))|dict(complete=complete,status=status,
            producer=runs[0],independent=runs[1],canonical_exports_sha256=
            hashlib.sha256(json.dumps(sorted(sets[0]),separators=(',',':')).encode()).hexdigest() if complete else None))
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n',newline='\n');os.replace(temp,dest)
        print(json.dumps(dict(query=query,status=status,nodes=[r['nodes'] for r in runs],exports=[len(s) for s in sets])),flush=True)


if __name__=='__main__':main()
