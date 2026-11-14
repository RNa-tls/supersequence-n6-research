#!/usr/bin/env python3
"""Round X -- sha256 (first 16 hex digits) of every certificate file under rX/certs, as a Markdown list."""
import hashlib, os, sys
root = sys.argv[1] if len(sys.argv) > 1 else "rX/certs"
for d, _, fs in sorted(os.walk(root)):
    for f in sorted(fs):
        p = os.path.join(d, f); h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        print("* `%s` `%s…` (%d bytes)" % (os.path.relpath(p, root), h[:16], os.path.getsize(p)))
