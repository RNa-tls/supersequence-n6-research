"""Run the unchanged master checks and add archived producer-hash consistency.
Set R150_MASTER_ROOT to a byte-exact LF checkout. Historical files are not changed.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys

HOME=Path(__file__).resolve().parents[2]
ROOT=Path(os.environ.get('R150_MASTER_ROOT',str(HOME))).resolve()

def main():
    captured={};original=Path.write_text
    def redirect(p,data,*args,**kw):
        if p.resolve()==ROOT/'r148/certs/master_verifier_148.json':
            captured.update(json.loads(data));return len(data)
        raise RuntimeError('Unexpected master write: '+str(p))
    Path.write_text=redirect
    try:
        module=runpy.run_path(str(ROOT/'r148/src/verifier148.py'))
        with contextlib.redirect_stdout(io.StringIO()):module['main']([])
    finally:Path.write_text=original
    bins=json.loads((ROOT/'r147/certs/binaries_147.json').read_text())
    producer=bins['phase2_build']['exe_sha256'];bad=[]
    for file in ('chain_cells_147.json','heavy_cells_147.json'):
        for key,row in json.loads((ROOT/'r147/tables'/file).read_text()).items():
            if row.get('exe_sha256')!=producer:bad.append([file,key])
    captured['checks'].append(dict(check='R150_historical_producer_hash_matches_1101_table_records',ok=not bad,
                                   detail=dict(checked=1101,mismatches=bad)))
    captured['failed']=[c['check'] for c in captured['checks'] if not c['ok']]
    captured['certified']=not captured['failed']
    captured['root']=str(ROOT)
    captured['note']='Artifact master, not a fresh exhaustive capacity search. New hash check does not authenticate an unavailable old binary; it detects inconsistent archival provenance.'
    output=Path(os.environ.get('R150_MASTER_OUTPUT',str(HOME/'r150/certs/master150.json')))
    output.write_text(json.dumps(captured,indent=2)+'\n',encoding='utf8')
    for c in captured['checks']:print(('PASS' if c['ok'] else 'FAIL')+' '+c['check'])
    return int(not captured['certified'])

if __name__=='__main__':sys.exit(main())
