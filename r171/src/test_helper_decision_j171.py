"""Only the new observation wrapper; no endpoint/regression re-audit."""
import unittest
from helper_decision_j171 import G, Meter

class ObservationOnly(unittest.TestCase):
    def test_complete_trace_unchanged(self):
        for cell, bound, cert in [((0,0,0,0,0,0),120,{}),
                                  ((0,0,0,0,0,0),120,{(0,0,0,0,0,0):120})]:
            a=G.Engine(cert,1000);b=Meter(cert,1000,bound+1,cert)
            self.assertEqual(a.build(cell,bound),b.build(cell,bound))
            self.assertEqual(a.nodes,b.nodes)
            self.assertEqual(b.new_p,0)
    def test_cap_unchanged(self):
        cell=(1,4,5,1,0,0);a=G.Engine({},40);b=Meter({},40,122,{})
        self.assertEqual(a.build(cell,121),b.build(cell,121))
        self.assertEqual(a.nodes,b.nodes)
        self.assertEqual(a.nodes,41)

if __name__=='__main__':unittest.main()
