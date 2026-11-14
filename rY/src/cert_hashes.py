#!/usr/bin/env python3
"""Round Y -- sha256 (first 16 hex digits) of every file in rY/certs, for the report."""
import hashlib, os, sys
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certs')
for f in sorted(os.listdir(root)):
    p = os.path.join(root, f)
    if os.path.isfile(p):
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        print(f"{h[:16]}  {os.path.getsize(p):>9}  {f}")
