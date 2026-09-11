"""Paired exact-P necessary queries, optionally using certified suffix bounds.

These are not capacity maxima or literal cover searches. Export every exact-P
prefix only when a complete enumeration finishes; caps never prove absence.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from verify_round143_coupled_codex import replay, validate_capacity_file
from run_round143_sigma_batch_codex import ZIG

ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--queries',required=True,help='A:b:D:P comma separated')
    ap.add_argument('--cap',type=int,default=0)
    ap.add_argument('--table',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--control-no-bounds',action='store_true')
    a=ap.parse_args()
    dest=ROOT/a.output
    assert not dest.exists(),'New output required'
    folder=dest.with_suffix('')
    assert not folder.exists(),'New witness folder required'
    table=ROOT/a.table
    manifest=json.loads(table.with_suffix('.json').read_text())
    assert sha(table)==manifest['table_sha256']
    cells={}
    for name,digest in manifest['input_sha256'].items():
        assert sha(ROOT/name)==digest
        verified,_=validate_capacity_file(ROOT/name)
        for c in verified:
            key=(c['A'],c['b'],c['D'])
            if key in cells:
                assert cells[key]==c['upper']
            cells[key]=c['upper']
    expected=''.join('%d %d %d %d\n'%(*key,v) for key,v in sorted(cells.items()))
    assert table.read_text()==expected
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
    assert head==remote
    sources=['src/round143_marked_runs_codex.c','src/round143_marked_ports_independent.c',
             Path(__file__).relative_to(ROOT).as_posix(),'src/verify_round143_coupled_codex.py',
             'src/prepare_round143_suffix_bounds_codex.py']
    binaries=[];provenance=[]
    for rel in sources:
        raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
        assert raw==(ROOT/rel).read_bytes(),rel
        digest=hashlib.sha256(raw).hexdigest()
        item=dict(path=rel,committed_lf_sha256=digest,runtime_sha256=sha(ROOT/rel))
        if rel.endswith('.c'):
            exe=ROOT/'outputs'/('round143_prefix_'+Path(rel).stem+'_'+digest[:12]+'.exe')
            argv=[str(ZIG),'cc','-O3','-std=c11',str(ROOT/rel),'-o',str(exe)]
            if not exe.exists():
                subprocess.run(argv,cwd=ROOT,check=True)
            binaries.append(exe)
            item.update(binary_sha256=sha(exe),compile_argv=argv)
        provenance.append(item)
    folder.mkdir()
    out=dict(schema='round143-paired-exact-P-v1',source_commit=head,source_provenance=provenance,
             argv=sys.argv,compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
             table_sha256=sha(table),bound_manifest_sha256=sha(table.with_suffix('.json')),
             proof_scope='EXACT (A,b,D,P) NECESSARY PREFIXES, NOT CAPACITY MAXIMA; no literal cover claim',rows=[])
    for A,b,D,P in [tuple(map(int,x.split(':'))) for x in a.queries.split(',')]:
        runs=[];path_sets=[]
        for index,exe in enumerate(binaries):
            exported=folder/f'A{A}_b{b}_D{D}_P{P}_{index}.jsonl'
            argv=[str(exe),str(b),str(D),str(a.cap),'SIGMA:'+str(A),str(P),str(exported)]
            if not a.control_no_bounds:
                argv.append(str(table))
            started=time.perf_counter()
            pr=subprocess.run(argv,capture_output=True,text=True,check=True,cwd=ROOT)
            r=json.loads(pr.stdout)
            r.update(argv=argv,seconds=time.perf_counter()-started,
                     stdout_sha256=hashlib.sha256(pr.stdout.encode()).hexdigest(),
                     exported_file=exported.relative_to(ROOT).as_posix(),export_sha256=sha(exported))
            assert r['suffix_bound_enabled']==(not a.control_no_bounds)
            paths=set();count=0
            with exported.open() as stream:
                for line in stream:
                    record=json.loads(line)
                    entries=record['entries'] if isinstance(record,dict) else record
                    check=replay(entries)
                    assert check['P']==P and check['A']==A and check['b']<=b and check['D']<=D
                    paths.add(tuple(entries));count+=1
            assert count==len(paths),'Duplicate exported path'
            assert count==r.get('extrema',r.get('exported_prefixes'))
            r['independently_replayed_exports']=count
            runs.append(r);path_sets.append(paths)
        complete=all(r['completed'] and not r['capped'] for r in runs)
        if complete:
            assert path_sets[0]==path_sets[1]
        result='UNKNOWN_CAP' if not complete else ('NO_EXACT_P_PREFIX' if not path_sets[0] else 'EXACT_P_PREFIXES_COMPLETE')
        canonical=sorted(path_sets[0]) if complete else None
        out['rows'].append(dict(A=A,b=b,D=D,P=P,complete=complete,status=result,
            producer=runs[0],independent=runs[1],
            canonical_exports_sha256=hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest() if complete else None))
        temporary=dest.with_suffix('.tmp')
        temporary.write_text(json.dumps(out,indent=2)+'\n',newline='\n')
        os.replace(temporary,dest)
        print(json.dumps(dict(A=A,b=b,D=D,P=P,status=result,nodes=[r['nodes'] for r in runs],
                              suffix_prunes=[r['suffix_bound_prunes'] for r in runs],exports=[len(s) for s in path_sets])),flush=True)


if __name__=='__main__':
    main()
