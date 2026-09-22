"""Launch one bounded pass with durable logs; never automatically restart it."""
import argparse
import datetime
import os
import subprocess
import sys
import bulk_j171 as W


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cap',type=int,required=True)
    p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    assert a.cap>0 and 1<=a.workers<=3
    processes=subprocess.check_output(['powershell','-NoProfile','-Command',
        "@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} | Select-Object -ExpandProperty ProcessId) -join ','"],text=True).strip()
    assert {int(x) for x in processes.split(',') if x}<={os.getpid()},processes
    m=W.load(W.MAN);assert m['driver_sha256']==W.sha(W.DRIVER)
    assert not any(t['status']=='GENERATING' for t in m['targets'])
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base=W.BASE+'runs/'+stamp+'/'
    (W.ROOT/base).mkdir(parents=True,exist_ok=False)
    command=[sys.executable,'-u','r171/src/run_bulk_escalation_j171.py','--cap',str(a.cap),'--workers',str(a.workers)]
    with (W.ROOT/base/'stdout.log').open('ab') as out,(W.ROOT/base/'stderr.log').open('ab') as err:
        child=subprocess.Popen(command,cwd=W.ROOT,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
            creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True)
    record=dict(pid=child.pid,command=command,started_utc=stamp,
        manifest_before_sha256=W.sha(W.MAN),driver_sha256=W.sha(W.DRIVER),
        wrapper_sha256=W.sha('r171/src/run_bulk_escalation_j171.py'),
        launcher_sha256=W.sha('r171/src/launch_bulk_detached_j171.py'),
        stdout=base+'stdout.log',stderr=base+'stderr.log',automatic_restart=False,
        cap=a.cap,workers=a.workers)
    W.atomic(base+'launch.json',record)
    print(W.json.dumps(record,indent=1))
