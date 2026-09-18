import unittest
from golden_model.network.model import *

class TestNetwork(unittest.TestCase):
    def test_packets(self):
        self.assertEqual(Packet((1,2,3),PacketEnd.EOP).end,PacketEnd.EOP)
        self.assertFalse(packets_interleaved([1,1,2,2]))
        self.assertTrue(packets_interleaved([1,2,1]))
    def test_timecode(self):
        r=TimeCodeRegister(5); x=r.receive(6); self.assertTrue(x["valid"]); self.assertEqual(r.value,6)
        r=TimeCodeRegister(63); self.assertTrue(r.receive(0)["valid"])
        r=TimeCodeRegister(5); x=r.receive(9); self.assertFalse(x["valid"]); self.assertEqual(r.value,9); self.assertFalse(x["notify_host"])
        self.assertEqual(timecode_broadcast_code(12)["type"],0)
    def test_interrupts(self):
        self.assertEqual(interrupt_code(0),{"type":2,"value":0,"IID":0,"ack":False})
        self.assertEqual(interrupt_code(17,True)["value"],49)
        with self.assertRaises(ValueError): interrupt_code(32)
        self.assertFalse(ack_configuration_valid(sources=2,acknowledgers=1,mode=InterruptMode.ACK))
        self.assertTrue(ack_configuration_valid(sources=1,acknowledgers=1,mode=InterruptMode.ACK))
    def test_features_selected(self):
        p=NetworkFeatureProfile(); self.assertTrue(p.time_code and p.distributed_interrupt and p.source_multicast)

if __name__=="__main__": unittest.main()
