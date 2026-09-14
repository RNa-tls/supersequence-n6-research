"""Run the historical 18 mutations in the disposable clean worktree.
Use master150 as the verifier; preserve the old script and proof artifacts.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[2]

def main():
    clean=Path(sys.argv[1]).resolve()
    old_result=clean/'r148/certs/mutation_148.json'
    if old_result.exists():
        (ROOT/'r150/certs/legacy_mutation_unmodified_master.json').write_bytes(old_result.read_bytes())
    module=runpy.run_path(str(clean/'r148/src/mutation148.py'))
    module['main'].__globals__['VER']=ROOT/'r150/src/master150.py'
    os.environ['R150_MASTER_ROOT']=str(clean)
    os.environ['R150_MASTER_OUTPUT']=str(ROOT/'r150/build/master_mutation_latest.json')
    os.environ['PYTHONUTF8']='1'
    tracked=[p for p in (clean/'r147').rglob('*') if p.is_file() and p.suffix in ('.json','.c','.py','.h')]
    before={str(p):sha256(p.read_bytes()).hexdigest() for p in tracked}
    rc=module['main']()
    result=json.loads(old_result.read_text())
    assert rc==0 and result['ok'],result
    assert all(sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in before.items())
    result['restored_r147_files_sha256']=before
    result['verifier']='r150/src/master150.py; old 18 mutations unchanged'
    out=ROOT/'r150/certs/master_mutations150.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return rc

if __name__=='__main__':sys.exit(main())
