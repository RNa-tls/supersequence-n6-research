"""Independent small-domain checks and second N*(b,0,8) implementation."""
import hashlib,itertools,json,subprocess,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def independent_rows():
    out=[]
    for typ,ab,short in [('A',1,3),('A',2,3),('B',2,4)]:
        for e,free,x,H in itertools.product(range(7),range(short+1),range(3),range(3)):
            if free>ab+e:continue
            if 871+e+x+H-free>871:continue
            out.append((typ,ab,ab+e-free,x,H,e))
    return sorted(out)

def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/round139-g2-k2-multidefect'],text=True).split()[0]==head
    initial=json.loads((ROOT/'outputs/rr_round139_initial_codex.json').read_text())
    actual=sorted((r['type'],r['F'],r['delta'],r['x'],r['H'],r['e']) for r in initial['resources']['rows'])
    assert independent_rows()==actual
    results=[]
    for b in [0,1,2]:
        exe=ROOT/'outputs/verify_round139_b2_capacity_codex.exe';argv=[str(exe),str(b),'20000000000'];t=time.perf_counter()
        p=subprocess.run(argv,capture_output=True,text=True);d=json.loads(p.stdout)
        assert p.returncode==0 and not d['capped'];assert d['passes']==[62,77,92][b]
        results.append(dict(argv=argv,seconds=time.perf_counter()-t,result=d,executable_sha256=sha(exe)))
        print('b',b,'passes',d['passes'],'nodes',d['nodes'],flush=True)
    sources=['src/verify_round139_b2_capacity_codex.c','src/verify_round139_marked_return_codex.c','src/verify_round139_multidefect_codex.py']
    data=dict(commit=head,resources_verified=True,independent_b2=results,
              committed_source_sha256={f:hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+f])).hexdigest() for f in sources},
              compiler='zig cc 0.16.0 -O3',input_sha256={'initial':sha(ROOT/'outputs/rr_round139_initial_codex.json')})
    (ROOT/'outputs/rr_round139_independent_codex.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
