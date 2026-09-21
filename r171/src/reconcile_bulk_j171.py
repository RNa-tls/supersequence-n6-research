"""Recover finished deferred jobs after a push failure; never regenerate work."""
from bulk_j171 import *

def main():
    m=load(MAN);assert m['driver_sha256']==sha(DRIVER)
    recovered=[]
    for p in sorted((ROOT/BASE/'jobs').glob('*.json')):
        r=json.loads(p.read_text());t=next(t for t in m['targets'] if t['cell']==r['cell'])
        if any(x['id']==r['id'] for x in t['attempts']):continue
        assert r['status']=='DEFERRED','Non-deferred orphan requires separate verification, not adoption.'
        assert r['driver_sha256']==m['driver_sha256'] and r['versions']==m['versions']
        assert r['bound']==t['bound'] and r['target']==t['bound']+1
        assert r['nodes']==r['cap']+1 and 'node cap' in r['detail']
        dep=validate_dag(r['predecessor_refs'])
        assert canonical([(text(k),v) for k,v in sorted(dep.items())])==r['predecessor_set_sha256']
        assert r['id'].endswith('_e0') and not m['accepted']
        t['attempts'].append(dict(id=r['id'],cap=r['cap'],nodes=r['nodes'],status='DEFERRED',environment_count=0))
        t['status']='DEFERRED';recovered.append(r['id'])
    assert not any(t['status']=='GENERATING' for t in m['targets'])
    m['status']='RECOVERED_PUSH_INTERRUPTION';atomic(MAN,m)
    atomic(BASE+'push_interruption_recovery.json',dict(reason='GitHub DNS failure; child pool drained before driver exit.',
        recovered_jobs=recovered,new_search_started=False,certified=m['certified'],remaining=m['remaining']))
    print('RECOVERED',recovered)

if __name__=='__main__':main()
