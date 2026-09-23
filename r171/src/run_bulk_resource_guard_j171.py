"""Resource-aware scheduling; unchanged proof builder, J, and dual verifiers.

Stop admitting work on low resources, drain in-flight jobs, retain all results.
A resource hold is not a cap hit or a mathematical conclusion.
"""
import argparse
import ctypes
import concurrent.futures as cf
import bulk_j171 as W
from run_bulk_transport_j171 import retry_git


def resources():
    class Power(ctypes.Structure):
        _fields_=[('ac',ctypes.c_ubyte),('flag',ctypes.c_ubyte),('percent',ctypes.c_ubyte),
                  ('reserved',ctypes.c_ubyte),('seconds',ctypes.c_uint32),('full_seconds',ctypes.c_uint32)]
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_uint32),('load',ctypes.c_uint32)]+[(n,ctypes.c_uint64) for n in
            ('total','available','total_page','available_page','total_virtual','available_virtual','extended')]
    p=Power();m=Memory();m.length=ctypes.sizeof(m)
    assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return dict(ac=p.ac,battery_percent=p.percent,available_ram=m.available)


def hold_reason(r):
    if r['ac']==0 and r['battery_percent']!=255 and r['battery_percent']<35:
        return 'BATTERY_BELOW_35_PERCENT_NO_AC'
    if r['available_ram']<6*1024**3:return 'AVAILABLE_RAM_BELOW_6_GIB'
    return None


def run(cap,workers):
    assert cap>0 and 1<=workers<=2
    W.git=retry_git
    m=W.load(W.MAN);assert m['driver_sha256']==W.sha(W.DRIVER)
    assert not any(t['status']=='GENERATING' for t in m['targets'])
    pending=[t for t in m['targets'] if t['status']!='CERTIFIED' and not any(
        a['cap']>=cap and a['environment_count']==len(m['accepted']) for a in t['attempts'])]
    pending.sort(key=lambda t:(-len(t['possible_required_predecessors']),t['prior_fallback'],W.key(t['cell'])))
    m['resource_orchestration']=dict(source_sha256=W.sha('r171/src/run_bulk_resource_guard_j171.py'),
        cap=cap,workers=workers,min_available_ram=6*1024**3,min_battery_without_ac=35,
        proof_driver_unchanged=True,automatic_restart=False)
    m['status']='RUNNING';W.atomic(W.MAN,m)
    blocked=None;dirty=[]
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        active={}
        while pending or active:
            while pending and len(active)<workers and blocked is None:
                observation=resources();reason=hold_reason(observation)
                if reason:
                    blocked=dict(reason=reason,resources=observation)
                    m['resource_hold']=blocked;W.atomic(W.MAN,m)
                    print('RESOURCE_HOLD; draining active jobs',blocked,flush=True);break
                t=pending.pop(0);n=len(m['accepted'])
                ident=t['cell'].replace('|','_')+f'_c{cap}_e{n}'
                assert not (W.ROOT/W.BASE/'jobs'/f'{ident}.json').exists()
                spec=dict(id=ident,cell=t['cell'],bound=t['bound'],cap=cap,
                    accepted=list(m['accepted']),driver_sha256=m['driver_sha256'])
                t['status']='GENERATING';W.atomic(W.MAN,m)
                active[pool.submit(W.job,spec)]=(t,n)
                print('START',t['cell'],cap,'predecessor additions',n,flush=True)
            if not active:break
            done,_=cf.wait(active,timeout=30,return_when=cf.FIRST_COMPLETED)
            if not done:print('HEARTBEAT active',len(active),'waiting',len(pending),'certified',m['certified'],flush=True)
            for future in done:
                t,n=active.pop(future)
                try:r=future.result()
                except BaseException as e:
                    m['status']='VERIFICATION_FAILURE';m['error']=repr(e);W.atomic(W.MAN,m);raise
                assert r['status'] in ('DEFERRED','CERTIFIED'),r
                assert r['bound']==t['bound'] and r['target']==t['bound']+1
                if r['status']=='DEFERRED':assert r['nodes']==cap+1 and 'node cap' in r['detail']
                t['status']=r['status'];t['attempts'].append(dict(id=r['id'],cap=cap,
                    nodes=r['nodes'],status=r['status'],environment_count=n))
                if r['status']=='CERTIFIED':m['accepted'].append(r);m['certified']+=1;m['remaining']-=1
                assert m['certified']==6+len(m['accepted']) and m['certified']+m['remaining']==35
                dirty.append(r);W.atomic(W.MAN,m)
                print('RESULT',r['cell'],r['status'],r['nodes'],'total',m['certified'],flush=True)
                if r['status']=='CERTIFIED' or len(dirty)>=2:W.checkpoint(m,dirty);dirty=[]
    m['status']='RESOURCE_BLOCKED' if blocked else 'PASS_FINISHED'
    m['pending_at_resource_hold']=[t['cell'] for t in pending] if blocked else []
    W.atomic(W.MAN,m)
    W.checkpoint(m,dirty)
    print(m['status'],m['certified'],'/35',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cap',type=int,required=True)
    p.add_argument('--workers',type=int,default=2);a=p.parse_args();run(a.cap,a.workers)
