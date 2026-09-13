"""Regression controls for the component-allocation proof boundary."""
import itertools
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from verify_round143_component_convolution_codex import allocators, exact_deficit_round
from verify_round143_coupled_extraction_codex import NEG


class ComponentConvolution(unittest.TestCase):
    def test_actual_deficit_congruence(self):
        for upper,D in itertools.product(range(30),range(15)):
            choices=[p for p in range(1,upper+1) if (p+D)%5==0]
            self.assertEqual(exact_deficit_round(upper,D),max(choices,default=0))

    def test_backward_forward_and_literal_product(self):
        # Deliberately nonmonotone exact A/Q and exact D data.
        pathrows={(0,0,0,0,0,0):5,(1,0,0,0,0,1):9,(0,0,0,0,1,0):10}
        cyclerows={(0,0,0,0,0,0):20,(2,0,0,0,0,0):10,
                   (1,0,0,0,0,1):7,(0,0,1,0,0,0):6}
        p=lambda *k:pathrows.get(k,0)
        c=lambda *k:cyclerows.get(k,0)
        back,forward=allocators(p,c)
        for d in (1,2):
            for A,E,B,D in itertools.product(range(4),range(2),range(2),range(3)):
                budget=(A,0,E,0,B,D)
                brute=NEG
                for pk,pv in pathrows.items():
                    for selection in itertools.product(cyclerows,repeat=d):
                        total=tuple(sum(col) for col in zip(pk,*selection))
                        if total==budget:
                            brute=max(brute,pv+sum(cyclerows[k] for k in selection))
                self.assertEqual(back(d,budget),brute)
                self.assertEqual(forward(d,budget),brute)

    def test_closing_does_not_charge_an_extra_old_orbit(self):
        # Audited positive controls: ordinary 5-port path + 10-port E/A cycle.
        p=lambda *k:5 if k==(0,0,0,0,0,0) else 0
        c=lambda *k:10 if k==(2,0,0,0,0,0) else 0
        back,forward=allocators(p,c)
        self.assertEqual(back(1,(2,0,0,0,0,0)),15)
        self.assertEqual(forward(1,(2,0,0,0,0,0)),15)
        # Incorrectly charging closing b would falsely make this infeasible.
        self.assertEqual(back(1,(2,0,0,0,1,0)),NEG)


if __name__=='__main__':
    unittest.main()
