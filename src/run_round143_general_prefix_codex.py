"""Frozen paired generic one-beta-path exact-P decisions, never scalar caps."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from run_round143_sigma_batch_codex import ZIG
from verify_round143_coupled_codex import WORDS,orbit,hexagon,validate_capacity_file
from prepare_round143_general_bounds_codex import build

ROOT=Path(__file__).resolve().parents[1]
FIELDS=('A','Qs','R','H','b','D','P')
INDEX={p:i for i,p in enumerate(WORDS)}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(entries):
    assert entries and len(set(entries))==len(entries)
    words=[WORDS[i] for i in entries];assert words[0]==tuple(range(6))
    opened={orbit(words[0])};covered={hexagon(words[0])}
    a=q=r=h=b=0;kinds=[];details=[]
    for source,target in zip(words,words[1:]):
        end=source[-1:]+source[:-1]
        weight=next(w for w in range(1,7) if end[w:]==target[:6-w])
        assert weight>=2
        E=source[1:5]+source[:1]+source[5:]
        isA=weight==2 and target==source[1:]+source[:1]
        isB=weight==3 and target==source[2:]+source[:2]
        free=target==E
        assert free==(weight==2 and not isA)
        oldq=orbit(target) in opened;oldh=hexagon(target) in covered
        a+=isA;q+=isB;r+=oldh;h+=max(0,weight-3);b+=not free and oldq
        kinds.append('E' if free else ('A' if isA else ('B' if isB else 'HEAVY' if weight>3 else 'W3')))
        details.append(dict(weight=weight,oldq=oldq,oldh=oldh))
        opened.add(orbit(target));covered.add(hexagon(target))
    return dict(A=a,Qs=q,R=r,H=h,b=b,D=5*len(opened)-len(entries),P=len(entries),O=len(opened),kinds=kinds,details=details)


def normalized(entries):
    remap={v:i for i,v in enumerate(WORDS[entries[0]])}
    return [INDEX[tuple(remap[v] for v in WORDS[j])] for j in entries]


def readpaths(path,query):
    paths=[];controls=[]
    with path.open() as stream:
        for line in stream:
            row=json.loads(line);entries=row['entries'] if isinstance(row,dict) else row
            result=replay(entries)
            for f,v in zip(FIELDS,query):
                assert result[f]==v if f in ('A','Qs','P') else result[f]<=v,(f,result,query)
            paths.append(tuple(entries))
    assert len(paths)==len(set(paths)),'Duplicate exact port path'
    return set(paths)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--queries',help='A:Qs:R:H:b:D:P comma separated, or ALL')
    ap.add_argument('--cap',type=int,default=0);ap.add_argument('--table',required=True)
    ap.add_argument('--output',required=True);ap.add_argument('--control-no-bounds',action='store_true')
    args=ap.parse_args();dest=ROOT/args.output;folder=dest.with_suffix('')
    assert not dest.exists() and not folder.exists(),'Use fresh output paths'
    table=ROOT/args.table;manifest=json.loads(table.with_suffix('.json').read_text());cells=[]
    assert sha(table)==manifest['table_sha256']
    for rel,digest in manifest['input_sha256'].items():
        assert sha(ROOT/rel)==digest,rel
        if rel== 'outputs/rr_round143_t4_combined_codex.json':continue
        new,_=validate_capacity_file(ROOT/rel);cells+=new
    rows,checked=build(cells,manifest['queries'])
    assert table.read_text()==''.join(' '.join(map(str,r))+'\n' for r in rows)
    assert checked==manifest['independent_convolution_cells']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
    assert head==remote,'Commit, push and verify before any paired run'
    sources=['src/round143_general_runs_codex.c','src/round143_general_ports_independent.c',
             'src/run_round143_general_prefix_codex.py','src/prepare_round143_general_bounds_codex.py',
             'src/verify_round143_coupled_extraction_codex.py','src/verify_round143_coupled_codex.py']
    provenance=[];binaries=[]
    for rel in sources:
        raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
        assert raw==(ROOT/rel).read_bytes(),rel
        digest=hashlib.sha256(raw).hexdigest();item=dict(path=rel,committed_lf_sha256=digest,runtime_sha256=sha(ROOT/rel))
        if rel.endswith('.c'):
            exe=ROOT/'outputs'/('round143_generic_'+Path(rel).stem+'_'+digest[:12]+'.exe')
            argv=[str(ZIG),'cc','-O3','-std=c11',str(ROOT/rel),'-o',str(exe)]
            if not exe.exists():subprocess.run(argv,cwd=ROOT,check=True)
            binaries.append(exe);item.update(binary_sha256=sha(exe),compile_argv=argv)
        provenance.append(item)
    folder.mkdir()
    queries=manifest['queries'] if args.queries in (None,'ALL') else [tuple(map(int,x.split(':'))) for x in args.queries.split(',')]
    data=dict(schema='round143-paired-general-exact-P-v1',source_commit=head,source_provenance=provenance,
              argv=sys.argv,compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
              bound_manifest=table.with_suffix('.json').relative_to(ROOT).as_posix(),bound_manifest_sha256=sha(table.with_suffix('.json')),
              table_sha256=sha(table),scope='NECESSARY ONE-BETA-PATH PREFIXES; not capacity maxima, not literal cover feasibility',rows=[])
    for query in queries:
        A,Q,R,H,b,D,P=query;runs=[];sets=[]
        for side,exe in enumerate(binaries):
            export=folder/('_'.join(map(str,query))+f'_{side}.jsonl')
            argv=[str(exe),str(b),str(D),str(args.cap),str(A),str(Q),str(R),str(H),str(P),str(export)]
            if not args.control_no_bounds:argv.append(str(table))
            start=time.perf_counter();proc=subprocess.run(argv,cwd=ROOT,check=True,capture_output=True,text=True)
            result=json.loads(proc.stdout)
            result.update(argv=argv,seconds=time.perf_counter()-start,stdout_sha256=hashlib.sha256(proc.stdout.encode()).hexdigest(),
                          export_file=export.relative_to(ROOT).as_posix(),export_sha256=sha(export))
            assert result['suffix_bound_enabled']==(not args.control_no_bounds)
            paths=readpaths(export,query)
            assert len(paths)==result['exported_prefixes']
            result['independently_replayed_exports']=len(paths);runs.append(result);sets.append(paths)
        complete=all(r['completed'] and not r['capped'] for r in runs)
        if complete:assert sets[0]==sets[1],query
        status='UNKNOWN_CAP' if not complete else ('NO_EXACT_P_PREFIX' if not sets[0] else 'EXACT_P_PREFIXES_COMPLETE')
        data['rows'].append(dict(zip(FIELDS,query))|dict(complete=complete,status=status,producer=runs[0],independent=runs[1],
            canonical_exports_sha256=hashlib.sha256(json.dumps(sorted(sets[0]),separators=(',',':')).encode()).hexdigest() if complete else None))
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n',newline='\n');os.replace(temp,dest)
        print(json.dumps(dict(query=query,status=status,nodes=[r['nodes'] for r in runs],exports=[len(s) for s in sets])),flush=True)


if __name__=='__main__':main()
