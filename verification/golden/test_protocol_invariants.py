import unittest

from golden_model.data_link.model import *
from golden_model.network.model import *
from golden_model.router.model import RouteEntry, RouterModel, FairRoundRobin


class TestProtocolInvariants(unittest.TestCase):
    def test_data_link_credit_invariants(self):
        m = DataLinkModel(link_state=LinkState.RUN, tx_credit=56, rx_credit=56)
        self.assertTrue(0 <= m.tx_credit <= 56)          # INV-DL-001
        self.assertTrue(0 <= m.rx_credit <= 56)          # INV-DL-002
        m.tx_credit = 0
        self.assertFalse(m.send_nchar())                 # INV-DL-003
        self.assertFalse(DataLinkModel(rx_credit=56).can_send_fct(8))
        self.assertFalse(DataLinkModel(rx_credit=0).can_send_fct(7))
        self.assertTrue(DataLinkModel(rx_credit=0).can_send_fct(8))  # INV-DL-004
        m = DataLinkModel(tx_credit=12, rx_credit=24)
        m.enter_error_reset("TEST")
        self.assertEqual((m.tx_credit, m.rx_credit), (0, 0))          # INV-DL-006

    def test_data_link_priority_direction_and_error_invariants(self):
        m = DataLinkModel(link_state=LinkState.RUN, tx_credit=8, rx_credit=8)
        self.assertEqual(
            m.select_tx(broadcast=True, fct=True, nchar=True),
            ItemKind.BROADCAST_CODE,
        )                                                   # INV-DL-005
        self.assertEqual(
            m.send_nchar_from_network(1).direction,
            Direction.NETWORK_TO_ENCODING,
        )
        self.assertEqual(
            m.receive_nchar_from_encoding(1).direction,
            Direction.ENCODING_TO_NETWORK,
        )                                                   # INV-DL-007
        m = DataLinkModel(link_state=LinkState.RUN)
        m.step_init(disconnect=True)
        self.assertEqual(m.link_state, LinkState.ERROR_RESET)
        self.assertEqual(m.recovery_state, RecoveryState.RECOVERY)   # INV-DL-008

    def test_network_packet_and_timecode_invariants(self):
        self.assertFalse(packets_interleaved([1, 1, 2, 2]))
        self.assertTrue(packets_interleaved([1, 2, 1]))      # INV-NET-001
        with self.assertRaises(ValueError):
            timecode_broadcast_code(64)                      # INV-NET-002
        r = TimeCodeRegister(63)
        self.assertTrue(r.receive(0)["valid"])                # INV-NET-003
        r = TimeCodeRegister(5)
        x = r.receive(9)
        self.assertEqual(r.value, 9)
        self.assertFalse(x["notify_host"])                    # INV-NET-004

    def test_network_broadcast_and_interrupt_invariants(self):
        self.assertEqual(
            select_broadcast({
                BroadcastKind.INTERRUPT,
                BroadcastKind.INTERRUPT_ACK,
                BroadcastKind.TIME_CODE,
            }),
            BroadcastKind.TIME_CODE,
        )                                                    # INV-NET-005
        for iid in (0, 31):
            self.assertEqual(interrupt_code(iid)["IID"], iid)
            self.assertEqual(interrupt_code(iid, ack=True)["IID"], iid)
        with self.assertRaises(ValueError):
            interrupt_code(32)                               # INV-NET-006
        self.assertEqual(
            reserved_broadcast_action(0b01, entity="router"),
            "DELETE_NOT_FORWARD",
        )
        self.assertEqual(
            reserved_broadcast_action(0b11, entity="node"),
            "DISCARD",
        )                                                    # INV-NET-007

    def test_router_address_and_allocation_invariants(self):
        r = RouterModel((1, 2, 3), {49: RouteEntry((2,), True)})
        self.assertTrue(r.route(2).consume_header)            # INV-RTR-001
        self.assertFalse(r.route(49).consume_header)          # INV-RTR-002
        self.assertTrue(r.route(255).discard)                 # INV-RTR-003
        self.assertEqual(r.begin_packet(1, 49).outputs, (2,))
        r.table[50] = RouteEntry((2,), True)
        self.assertTrue(r.begin_packet(3, 50).wait)           # INV-RTR-004
        self.assertEqual(r.output_owner[2], 1)
        self.assertEqual(r.transfer_nchar(1, 0x55)["outputs"], (2,))
        self.assertEqual(r.output_owner[2], 1)
        r.end_packet(1)
        self.assertNotIn(2, r.output_owner)                   # INV-RTR-005

    def test_router_multicast_fairness_interrupt_invariants(self):
        r = RouterModel(
            (1, 2, 3),
            {50: RouteEntry((2, 3), True, multicast=True)},
            multicast_enabled=True,
        )
        r.begin_packet(1, 50)
        x = r.transfer_nchar(1, 0xAA, ready_ports=[2])
        self.assertFalse(x["sent"])
        self.assertEqual(x["outputs"], ())                    # INV-RTR-006

        rr = FairRoundRobin()
        self.assertEqual(
            [rr.choose(1, [1, 2, 3]) for _ in range(6)],
            [1, 2, 3, 1, 2, 3],
        )                                                    # INV-RTR-007

        r = RouterModel((1, 2, 3))
        self.assertEqual(r.receive_interrupt(7, 1)["relay"], (2, 3))
        self.assertEqual(r.receive_interrupt(7, 1)["relay"], ())  # INV-RTR-008
        self.assertIn(7, r.interrupt_active)
        r.receive_interrupt_ack(7, 2)
        self.assertNotIn(7, r.interrupt_active)
        r.receive_interrupt(8, 1)
        r.interrupt_timeout(8)
        self.assertNotIn(8, r.interrupt_active)               # INV-RTR-009


if __name__ == "__main__":
    unittest.main()
