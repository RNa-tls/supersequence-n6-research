"""Scheduling-only tests: no proof generation and no repository writes."""
import copy
from concurrent.futures import Future
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_bulk_resource_guard_j171 as R


GOOD=dict(ac=1,battery_percent=100,available_ram=12*1024**3)


class ImmediatePool:
    def __init__(self,**kw):pass
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def submit(self,fn,spec):
        f=Future();f.set_result(fn(spec));return f


class ResourceTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertIsNone(R.hold_reason(GOOD))
        self.assertIsNone(R.hold_reason(dict(GOOD,ac=0,battery_percent=35)))
        self.assertEqual(R.hold_reason(dict(GOOD,ac=0,battery_percent=34)),'BATTERY_BELOW_35_PERCENT_NO_AC')
        self.assertIsNone(R.hold_reason(dict(GOOD,ac=1,battery_percent=1)))
        self.assertIsNone(R.hold_reason(dict(GOOD,ac=0,battery_percent=255)))
        self.assertEqual(R.hold_reason(dict(GOOD,available_ram=6*1024**3-1)),'AVAILABLE_RAM_BELOW_6_GIB')

    def simulate(self,readings):
        targets=[dict(cell=f'1|{i}|0|0|0|0',bound=80,status='PLANNED',attempts=[],
                      possible_required_predecessors=[],prior_fallback=0) for i in (1,2)]
        manifest=dict(driver_sha256='hash',targets=targets,accepted=[],certified=6,remaining=29)
        outputs=[];calls=[]
        def job(spec):
            calls.append(copy.deepcopy(spec))
            return dict(id=spec['id'],cell=spec['cell'],bound=spec['bound'],target=spec['bound']+1,
                        status='DEFERRED',nodes=spec['cap']+1,detail='node cap reached')
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            for obj,name,value in [(R.W,'ROOT',Path(d)),(R.W,'load',lambda p:copy.deepcopy(manifest)),
                (R.W,'sha',lambda p:'hash'),(R.W,'atomic',lambda p,v:None),(R.W,'job',job),
                (R.W,'checkpoint',lambda m,rows:outputs.append(copy.deepcopy(m))),
                (R.cf,'ProcessPoolExecutor',ImmediatePool)]:stack.enter_context(patch.object(obj,name,value))
            stack.enter_context(patch.object(R,'resources',side_effect=readings))
            R.run(100,2)
        return calls,outputs[-1]

    def test_hold_before_any_dispatch(self):
        calls,m=self.simulate([dict(GOOD,ac=0,battery_percent=34)])
        self.assertEqual(calls,[]);self.assertEqual(m['status'],'RESOURCE_BLOCKED')
        self.assertTrue(all(not t['attempts'] for t in m['targets']))

    def test_hold_drains_started_job_without_marking_unstarted_as_cap_hit(self):
        calls,m=self.simulate([GOOD,dict(GOOD,available_ram=0)])
        self.assertEqual(len(calls),1);self.assertEqual(m['status'],'RESOURCE_BLOCKED')
        self.assertEqual(m['targets'][0]['attempts'][0]['nodes'],101)
        self.assertEqual(m['targets'][1]['attempts'],[])
        self.assertEqual(m['pending_at_resource_hold'],['1|2|0|0|0|0'])

    def test_independent_caps_and_complete_pass(self):
        calls,m=self.simulate([GOOD,GOOD])
        self.assertEqual([c['cap'] for c in calls],[100,100])
        self.assertEqual(m['status'],'PASS_FINISHED');self.assertEqual(m['certified'],6)
        self.assertEqual([t['attempts'][0]['nodes'] for t in m['targets']],[101,101])


if __name__=='__main__':unittest.main()
