#!/usr/bin/env python3
"""Round Omega (copy of rZ/src/cert_hashes.py) -- sha256 (first 16 hex digits) of every file under rOmega/certs (recursively), for the report."""
import hashlib, os
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certs')
for d, _, fs in sorted(os.walk(root)):
    for f in sorted(fs):
        p = os.path.join(d, f); rel = os.path.relpath(p, root)
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        print(f"{h[:16]}  {os.path.getsize(p):>9}  {rel}")
