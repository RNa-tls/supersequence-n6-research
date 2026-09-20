"""Integrity/provenance record for the new Round171 audit, not a proof replay."""
import hashlib, json, subprocess, sys
from pathlib import Path
from joint_endpoint_codex import ROOT, save, sha, load

def main():
    p=subprocess.run([sys.executable,'-m','unittest','discover','-s','r171/src',
                      '-p','test_joint_endpoint_codex.py','-v'],cwd=ROOT,capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    subprocess.run([sys.executable,'-m','py_compile',
                    'r171/src/joint_endpoint_codex.py','r171/src/check_joint_endpoint_codex.py',
                    'r171/src/test_joint_endpoint_codex.py','r171/src/freeze_joint_codex.py'],cwd=ROOT,check=True)
    files=sorted(str(x.relative_to(ROOT)).replace('\\','/') for x in (ROOT/'r171').rglob('*')
                 if x.is_file() and 'codex' in x.name.lower() and x.suffix in ('.py','.json','.md')
                 and x.name!='joint_integrity_codex_171.json')
    hashes={f:sha(f) for f in files}
    e=load('r171/certs/joint_endpoint_codex_171.json')
    for f,h in e['inputs'].items():assert sha(f)==h
    semantic=hashlib.sha256(json.dumps(e,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert semantic==load('r171/certs/joint_endpoint_execution_codex_171.json')['content_sha256']
    # This checkout contains preserved data; changes here must be only new audit files.
    tracked=subprocess.run(['git','diff','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    assert not tracked,tracked
    report=dict(base_commit='0029fe2905d01db805d162230b54e9a1e2d2b161',
                base_parent='0333d1e5f74e4e6af6a49fdce09232e808d574eb',
                recovered_remote_branch='round153-equality-coexistence',
                audit_branch='codex/round171-joint-audit',
                existing_tracked_artifacts_modified=False,proof_generation_started=False,
                local_live_jobs_at_recovery='No Python/EXTREE/r171 worker observed; no assertion about remote hosts.',
                endpoint_canonical_content_sha256=semantic,files_sha256=hashes,
                regression=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),py_compile=True,
                verdict='JOINT_SAFE_VECTOR_PARTIAL')
    save('r171/certs/joint_integrity_codex_171.json',report)
    print('Integrity manifest and regression evidence written; historical files unchanged.')

if __name__=='__main__':main()
