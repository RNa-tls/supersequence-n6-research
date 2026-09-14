"""Preserve both Windows as-run and committed LF artifact SHA-256 values.
Does not replace or weaken a hash: explicitly proves only CRLF conversion occurred.
"""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
REF='f410148fbd86aabcc5bdce384b0e9d59e8d7d7a8'

def main():
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',REF,'--','r150'],cwd=ROOT,text=True).splitlines()
    rows=[]
    for rel in paths:
        disk=(ROOT/rel).read_bytes();blob=subprocess.check_output(['git','show',REF+':'+rel],cwd=ROOT)
        assert disk.replace(b'\r\n',b'\n')==blob,rel
        rows.append(dict(file=rel,as_run_sha256=sha256(disk).hexdigest(),committed_blob_sha256=sha256(blob).hexdigest(),
                         byte_identical=disk==blob,only_CRLF_difference=disk!=blob,committed_bytes=len(blob)))
    out=ROOT/'r150/certs/release_provenance.json';assert not out.exists()
    out.write_text(json.dumps(dict(proof_commit=REF,remote_branch='codex/round150-feas-audit',files=rows,
        purpose='As-run final150 hashes refer to local bytes. This sidecar gives corresponding immutable Git blob hashes, retaining both explicitly.',
        no_proof_or_count_change=True),indent=2)+'\n',encoding='utf8',newline='\n')

if __name__=='__main__':main()
