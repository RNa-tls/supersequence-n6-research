"""Preserve interrupted job records and reconcile only hash-validated results.

No partial EXTREE search state exists: interrupted jobs restart at their roots.
This command never launches a worker and refuses while any Python worker exists
other than its own interpreter.
"""
import datetime
import os
import subprocess
import bulk_j171 as W


def main():
    raw=subprocess.check_output(['powershell','-NoProfile','-Command',
        "@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} | Select-Object -ExpandProperty ProcessId) -join ','"],text=True).strip()
    assert {int(x) for x in raw.split(',') if x} <= {os.getpid()}, raw
    m=W.load(W.MAN)
    assert m['driver_sha256']==W.sha(W.DRIVER)
    f,refs,dep,env,base=W.initial()
    refs,dep=W.add_accepted(refs,m['accepted'])
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest=W.BASE+'interruptions/'+stamp+'/'
    assert not (W.ROOT/dest).exists()
    (W.ROOT/dest).mkdir(parents=True)
    original=(W.ROOT/W.MAN).read_bytes()
    (W.ROOT/dest/'manifest_before.json').write_bytes(original)
    records=[]
    for path in sorted((W.ROOT/W.BASE/'jobs').glob('*c20000000_e2.json')):
        r=W.json.loads(path.read_text())
        t=next(t for t in m['targets'] if t['cell']==r['cell'])
        assert r['driver_sha256']==m['driver_sha256'] and r['versions']==env['versions']
        assert r['bound']==f['J'][r['cell']] and r['target']==r['bound']+1
        assert [tuple(x) for x in r['predecessor_refs']]==refs
        assert r['predecessor_set_sha256']==W.canonical([(W.text(k),v) for k,v in sorted(dep.items())])
        registered=any(a['id']==r['id'] for a in t['attempts'])
        if r['status']=='GENERATING':
            assert not registered and t['status']=='GENERATING'
            before_hash=W.sha(str(path.relative_to(W.ROOT)))
            record=dict(id=r['id'],status='INTERRUPTED',nodes=None,
                original_sha256=before_hash,original_size=path.stat().st_size,
                modified_ns=path.stat().st_mtime_ns,
                preserved_path=dest+path.name,
                restart_semantics='Restart from root; no partial proof-tree checkpoint exists.')
            # Exact bytes are retained under a new, unique name. No proof is deleted.
            path.rename(W.ROOT/record['preserved_path'])
            assert W.sha(record['preserved_path'])==before_hash
            t.setdefault('interruptions',[]).append(record)
            t['status']='PLANNED';records.append(record)
        else:
            assert r['status']=='DEFERRED' and r['nodes']==r['cap']+1
            assert 'node cap' in r['detail'] and registered
    assert len(records)==3
    assert not any(t['status']=='GENERATING' for t in m['targets'])
    m['status']='INTERRUPTION_RECONCILED_READY_TO_RESTART'
    W.atomic(W.MAN,m)
    report=dict(termination_cause='UNKNOWN',live_python_workers=0,
        interrupted=records,certified=m['certified'],remaining=m['remaining'],
        manifest_before_sha256=W.hashlib.sha256(original).hexdigest(),
        manifest_after_sha256=W.sha(W.MAN),preserved_manifest=dest+'manifest_before.json',
        driver_unchanged=True,accepted_DAG_validated=True,
        lost_generation_node_count='UNKNOWN; excluded from exact completed-attempt totals',
        new_search_started=False)
    W.atomic(dest+'audit.json',report)
    print(W.json.dumps(report,indent=1))


if __name__=='__main__':main()
