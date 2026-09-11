import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from prepare_round143_suffix_bounds_codex import upper
from verify_round143_coupled_codex import replay


class SuffixBound(unittest.TestCase):
    def test_unknown_is_not_zero(self):
        self.assertIsNone(upper([],0,0,0))
        self.assertEqual(upper([],2,0,1),0)
        self.assertEqual(upper([dict(A=0,b=0,D=0,upper=20)],0,0,0),20)

    def test_literal_split_controls(self):
        x=json.loads((ROOT/'outputs/rr_round143_suffix_bounds_v1.json').read_text())
        self.assertTrue(x['all_suffix_identities_verified'])
        self.assertEqual(x['nonE_splits'],1672)
        self.assertEqual(x['old_orbit_boundary_splits'],80)

    def test_bounds_preserve_complete_exact_prefix_sets(self):
        binaries=[ROOT/'outputs/round143_compilecheck_producer.exe',
                  ROOT/'outputs/round143_compilecheck_independent.exe']
        if not all(p.exists() for p in binaries):
            self.skipTest('Compile both C engines to the explicit compilecheck paths first')
        table=ROOT/'outputs/rr_round143_suffix_bounds_v1.txt'
        for A,b,D,P in ((0,0,0,20),(0,0,0,21),(1,0,1,9),(2,0,2,13),(2,0,2,14),(3,0,3,17)):
            sets=[]
            with tempfile.TemporaryDirectory(prefix='r143_suffix_') as temporary:
                for j,exe in enumerate(binaries):
                    for enabled in (False,True):
                        destination=Path(temporary)/f'{j}_{enabled}.jsonl'
                        argv=[str(exe),str(b),str(D),'0',f'SIGMA:{A}',str(P),str(destination)]
                        if enabled:
                            argv.append(str(table))
                        result=json.loads(subprocess.check_output(argv,text=True,cwd=ROOT))
                        self.assertFalse(result['capped'])
                        self.assertEqual(result['suffix_bound_enabled'],enabled)
                        paths=set()
                        for line in destination.read_text().splitlines():
                            x=json.loads(line)
                            entries=x['entries'] if isinstance(x,dict) else x
                            checked=replay(entries)
                            self.assertEqual(checked['P'],P)
                            self.assertEqual(checked['A'],A)
                            paths.add(tuple(entries))
                        sets.append(paths)
            self.assertTrue(all(s==sets[0] for s in sets))


if __name__=='__main__':
    unittest.main()
