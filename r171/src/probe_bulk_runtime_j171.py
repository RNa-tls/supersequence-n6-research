"""Small Windows process-launch diagnostic, unrelated to proof search."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys


if __name__=='__main__':
    if '--child' in sys.argv:
        with concurrent.futures.ProcessPoolExecutor(3) as pool:
            assert list(pool.map(abs,[-1,-2,-3]))==[1,2,3]
        print('PROCESS_POOL_ACCEPT',flush=True)
    else:
        root=Path(__file__).resolve().parents[2]
        results=[]
        for label,flags in [('DETACHED',subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP),
                            ('NO_WINDOW',subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)]:
            p=subprocess.run([sys.executable,__file__,'--child'],stdin=subprocess.DEVNULL,
                capture_output=True,text=True,creationflags=flags,timeout=30)
            results.append(dict(mode=label,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        out=root/'r171/certs/bulk_j171/runtime_probe.json'
        out.write_text(json.dumps(results,indent=1)+'\n')
        print(json.dumps(results,indent=1))
