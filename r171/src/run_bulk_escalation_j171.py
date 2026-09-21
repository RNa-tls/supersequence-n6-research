"""Next bounded pass using the unchanged production driver and transport retries."""
import argparse
from run_bulk_transport_j171 import W, retry_git

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cap',type=int,required=True);p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    assert a.cap>0 and 1<=a.workers<=3
    W.git=retry_git
    W.atomic(W.BASE+f'escalation_{a.cap}_policy.json',dict(cap=a.cap,workers=a.workers,
        driver_sha256=W.sha(W.DRIVER),transport_sha256=W.sha('r171/src/run_bulk_transport_j171.py'),
        wrapper_sha256=W.sha('r171/src/run_bulk_escalation_j171.py'),
        semantics='Independent per-cell cap; stop a completed tree for A/B; caps defer. No helper added.'))
    W.run(a.cap,a.workers)
