"""Retry only Git transport; never alter generation, verification or job hashes."""
import subprocess, time
import bulk_j171 as W

original_git=W.git

def retry_git(*args):
    for attempt in range(4):
        try:return original_git(*args)
        except subprocess.CalledProcessError:
            if not args or args[0] not in ('push','ls-remote') or attempt==3:raise
            delay=(5,15,30)[attempt]
            print('TRANSPORT_RETRY',args[0],attempt+1,'delay',delay,flush=True)
            time.sleep(delay)

if __name__=='__main__':
    W.git=retry_git
    W.atomic(W.BASE+'transport_policy.json',dict(path='r171/src/run_bulk_transport_j171.py',
        sha256=W.sha('r171/src/run_bulk_transport_j171.py'),
        retries=3,delays_seconds=[5,15,30],search_driver_unchanged=W.sha(W.DRIVER),
        fake_remote_success=False))
    W.run(5000000,3)
