import unittest
from golden_model.router.model import *

class TestRouter(unittest.TestCase):
    def test_path(self):
        r=RouterModel((1,2,3))
        self.assertEqual(r.route(0),RouteDecision((0,),True,False,False,False))
        self.assertEqual(r.route(3).outputs,(3,))
        self.assertTrue(r.route(7).discard)
    def test_logical(self):
        r=RouterModel((1,2,3,7),{49:RouteEntry((7,),True)})
        d=r.route(49); self.assertEqual(d.outputs,(7,)); self.assertFalse(d.consume_header)
        r.table[49]=RouteEntry((7,),True,delete=True); self.assertTrue(r.route(49).consume_header)
        self.assertTrue(r.route(255).discard)
    def test_adaptive(self):
        r=RouterModel((1,2,3),{49:RouteEntry((2,3),True,adaptive=True)},adaptive_enabled=True)
        self.assertEqual(r.route(49,ready_ports=[3],busy_ports=[2]).outputs,(3,))
    def test_multicast(self):
        r=RouterModel((1,2,3),{50:RouteEntry((1,2,3),True,multicast=True)},multicast_enabled=True)
        self.assertEqual(r.route(50,enabled_ports=[1,2,3],ready_ports=[1,2,3]).outputs,(1,2,3))
        self.assertTrue(r.route(50,enabled_ports=[1,2,3],ready_ports=[1,3]).wait)
        self.assertEqual(r.route(50,enabled_ports=[1,3],ready_ports=[1,3]).outputs,(1,3))
    def test_reset(self):
        r=RouterModel(); r.adaptive_enabled=True; r.multicast_enabled=True; r.table[49]=RouteEntry((1,),True)
        r.reset(); self.assertFalse(r.table[49].valid); self.assertFalse(r.adaptive_enabled); self.assertFalse(r.multicast_enabled)
    def test_timeout(self):
        r=RouterModel(); x=r.stuck_packet(started=True,ended=False,idle_time=101,timeout=100); self.assertTrue(x["send_EEP"])
    def test_timecode_relay(self):
        r=RouterModel((1,2,3,4),timecode_register=5)
        self.assertEqual(r.receive_timecode(6,2)["relay"],(1,3,4))
        self.assertEqual(r.receive_timecode(9,2)["relay"],())
    def test_interrupt_relay(self):
        r=RouterModel((1,2,3))
        self.assertEqual(r.receive_interrupt(7,2)["relay"],(1,3))
        self.assertEqual(r.receive_interrupt(7,2)["relay"],())
        self.assertEqual(r.receive_interrupt_ack(7,1)["relay"],(2,3))
    def test_fair_reference_scheduler(self):
        a=FairRoundRobin(); seq=[a.choose(1,[1,2,3]) for _ in range(6)]
        self.assertEqual(seq,[1,2,3,1,2,3])

if __name__=="__main__": unittest.main()
