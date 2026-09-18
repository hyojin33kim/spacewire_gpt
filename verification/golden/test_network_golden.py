import unittest

from golden_model.network.model import *


class TestNetworkGolden(unittest.TestCase):
    def test_packet_vectors(self):
        p = Packet((1, 2, 3), PacketEnd.EOP)
        self.assertEqual(p.end, PacketEnd.EOP)                                # TV-NET-001

        empty = Packet((), PacketEnd.EEP)
        self.assertEqual(empty.end, PacketEnd.EEP)                            # TV-NET-002
        self.assertEqual(first_router_packet_action(empty), "DISCARD")         # TV-NET-029

        self.assertFalse(packets_interleaved([1, 1, 2, 2]))
        self.assertTrue(packets_interleaved([1, 2, 1]))                        # TV-NET-003

    def test_timecode_vectors(self):
        r = TimeCodeRegister(5)
        x = r.receive(6)
        self.assertTrue(x["valid"])
        self.assertEqual(r.value, 6)
        self.assertTrue(x["notify_host"])                                      # TV-NET-004

        r = TimeCodeRegister(63)
        self.assertTrue(r.receive(0)["valid"])                                 # TV-NET-005

        r = TimeCodeRegister(5)
        x = r.receive(9)
        self.assertFalse(x["valid"])
        self.assertEqual(r.value, 9)
        self.assertFalse(x["notify_host"])                                     # TV-NET-006

        self.assertEqual(timecode_broadcast_code(12)["type"], 0)

        r = TimeCodeRegister(22)
        r.reset()
        self.assertEqual(r.value, 0)                                           # TV-NET-017

        self.assertTrue(redundant_timecode_master_valid(["TC0", "TC0"]))        # 018
        self.assertFalse(redundant_timecode_master_valid(["TC0", "TC1"]))      # 019

    def test_interrupt_vectors(self):
        self.assertEqual(
            interrupt_code(0),
            {"type": 2, "value": 0, "IID": 0, "ack": False},
        )                                                                       # TV-NET-007
        self.assertEqual(interrupt_code(31)["IID"], 31)                         # 008
        self.assertEqual(interrupt_code(17, True)["value"], 49)                 # 009
        with self.assertRaises(ValueError):
            interrupt_code(32)                                                  # 010

        self.assertFalse(
            ack_configuration_valid(
                sources=2, acknowledgers=1, mode=InterruptMode.ACK
            )
        )                                                                       # 011
        self.assertTrue(
            ack_configuration_valid(
                sources=1, acknowledgers=1, mode=InterruptMode.ACK
            )
        )

        self.assertTrue(
            interrupt_repeat_interval_valid(
                mode=InterruptMode.INTERRUPT,
                interval=11,
                worst_interrupt_propagation=10,
            )
        )                                                                       # 020

        self.assertTrue(
            interrupt_repeat_interval_valid(
                mode=InterruptMode.ACK,
                interval=31,
                worst_interrupt_propagation=10,
                max_ack_generation=10,
                worst_ack_propagation=10,
            )
        )                                                                       # 021

        self.assertTrue(
            ack_generation_delay_valid(
                delay=11,
                worst_interrupt_propagation=10,
                max_ack_generation=20,
            )
        )                                                                       # 022

    def test_broadcast_priority_and_reserved_types(self):
        self.assertEqual(
            select_broadcast(
                {
                    BroadcastKind.INTERRUPT,
                    BroadcastKind.INTERRUPT_ACK,
                    BroadcastKind.TIME_CODE,
                }
            ),
            BroadcastKind.TIME_CODE,
        )                                                                       # TV-NET-014
        self.assertEqual(
            reserved_broadcast_action(0b01, entity="router"),
            "DELETE_NOT_FORWARD",
        )                                                                       # 015
        self.assertEqual(
            reserved_broadcast_action(0b11, entity="node"),
            "DISCARD",
        )                                                                       # 016

    def test_services_and_selected_features(self):
        p = NetworkFeatureProfile()
        self.assertTrue(p.time_code)                                             # TV-NET-012
        self.assertTrue(p.distributed_interrupt)                                 # TV-NET-013
        self.assertTrue(p.test_port_loopback)                                    # TV-NET-024

        packet = Packet((1, 2), PacketEnd.EOP)
        s = send_packet_request("EP0", packet)
        self.assertEqual(s.primitive, "SEND_PACKET.request")                    # 025

        r = TimeCodeRegister(5)
        self.assertIsNotNone(timecode_indication("EP0", r, 6))                  # 026
        r = TimeCodeRegister(5)
        self.assertIsNone(timecode_indication("EP0", r, 9))                     # 027

        a = interrupt_ack_request("EP0", 7)
        self.assertEqual(a.payload["ack"], True)
        self.assertEqual(a.payload["IID"], 7)                                   # 028

        copies = source_multicast(packet, ("A", "B"))
        self.assertEqual(len(copies), 2)                                        # 023


if __name__ == "__main__":
    unittest.main()
