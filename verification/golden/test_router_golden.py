import unittest

from golden_model.router.model import *


class TestRouterGolden(unittest.TestCase):
    def test_path_and_logical_vectors(self):
        r = RouterModel((1, 2, 3, 7))
        d = r.route(0)
        self.assertEqual(d.outputs, (0,))
        self.assertTrue(d.consume_header)                                      # TV-RTR-001

        self.assertEqual(r.route(3).outputs, (3,))                             # 002
        x = r.route(6)
        self.assertTrue(x.discard and x.invalid_address_error)                 # 003

        r.table[49] = RouteEntry((7,), True)
        d = r.route(49)
        self.assertEqual(d.outputs, (7,))
        self.assertFalse(d.consume_header)                                     # 004

        r.table[49] = RouteEntry((7,), True, delete=True)
        self.assertTrue(r.route(49).consume_header)                            # 005

        x = r.route(255)
        self.assertTrue(x.discard)                                             # 006
        self.assertTrue(x.invalid_address_error)                               # 031

        self.assertFalse(r.legacy_path_adaptive_supported)                     # 008
        self.assertTrue(r.configuration_port_path_only)

    def test_adaptive_and_multicast_vectors(self):
        r = RouterModel(
            (1, 2, 3),
            {49: RouteEntry((2, 3), True, adaptive=True)},
            adaptive_enabled=True,
        )
        self.assertEqual(
            r.route(49, ready_ports=[3], busy_ports=[2]).outputs, (3,)
        )                                                                      # TV-RTR-007

        r = RouterModel(
            (1, 2, 3),
            {50: RouteEntry((1, 2, 3), True, multicast=True)},
            multicast_enabled=True,
        )
        self.assertEqual(
            r.route(50, enabled_ports=[1, 2, 3], ready_ports=[1, 2, 3]).outputs,
            (1, 2, 3),
        )                                                                      # 009
        self.assertTrue(
            r.route(50, enabled_ports=[1, 2, 3], ready_ports=[1, 3]).wait
        )                                                                      # 010
        self.assertEqual(
            r.route(50, enabled_ports=[1, 3], ready_ports=[1, 3]).outputs,
            (1, 3),
        )                                                                      # 011

    def test_reset_vectors(self):
        r = RouterModel()
        r.adaptive_enabled = True
        r.multicast_enabled = True
        r.table[49] = RouteEntry((1,), True)
        r.interrupt_active.add(7)
        r.interrupt_timer_running.add(7)
        r.timecode_register = 22
        r.reset()
        self.assertFalse(r.table[49].valid)
        self.assertFalse(r.adaptive_enabled)
        self.assertFalse(r.multicast_enabled)                                  # TV-RTR-012
        self.assertEqual(r.interrupt_active, set())
        self.assertEqual(r.timecode_register, 0)                               # 029

    def test_timeout_vectors(self):
        r = RouterModel()
        x = r.stuck_packet(
            started=True, ended=False, idle_time=101, timeout=100, enabled=True
        )
        self.assertTrue(x["stuck"])
        self.assertTrue(x["send_EEP"])                                         # TV-RTR-013
        self.assertTrue(x["send_EEP_to_output_port"])
        self.assertTrue(x["error"])                                            # 034

        x = r.stuck_packet(
            started=True, ended=False, idle_time=101, timeout=100, enabled=False
        )
        self.assertFalse(x["stuck"])                                           # 033

    def test_timecode_vectors(self):
        r = RouterModel((1, 2, 3, 4), timecode_register=5)
        self.assertEqual(r.receive_timecode(6, 2)["relay"], (1, 3, 4))          # 014
        self.assertEqual(r.receive_timecode(9, 2)["relay"], ())                 # 015

        r = RouterModel((1, 2, 3), timecode_register=63)
        x = r.receive_timecode(0, 2)
        self.assertEqual(x["relay"], (1, 3))
        self.assertEqual(x["new_register"], 0)                                 # 030

    def test_interrupt_vectors(self):
        r = RouterModel((1, 2, 3))
        self.assertEqual(r.receive_interrupt(7, 2)["relay"], (1, 3))            # 016
        self.assertEqual(r.receive_interrupt(7, 2)["relay"], ())                # 017
        self.assertEqual(r.receive_interrupt_ack(7, 1)["relay"], (2, 3))        # 018

        r = RouterModel((1, 2, 3))
        r.interrupt_rx_enabled = {1, 3}
        x = r.receive_interrupt(7, 2)
        self.assertTrue(x["discard"])
        self.assertEqual(x["relay"], ())                                        # 024

        r = RouterModel((1, 2, 3))
        r.interrupt_tx_enabled = {3}
        self.assertEqual(r.receive_interrupt(7, 2)["relay"], (3,))              # 025

        r.interrupt_timeout(7)
        self.assertNotIn(7, r.interrupt_active)                                 # 026

        r = RouterModel((1, 2, 3))
        x = r.receive_interrupt_ack(7, 1)
        self.assertTrue(x["ignored"])
        self.assertEqual(x["relay"], ())                                        # 027

        r = RouterModel((1, 2, 3))
        r.interrupt_active.add(7)
        r.ack_rx_enabled = {2, 3}
        x = r.receive_interrupt_ack(7, 1)
        self.assertTrue(x["discard"])
        self.assertIn(7, r.interrupt_active)                                    # 028

    def test_wormhole_vectors(self):
        r = RouterModel((1, 2, 3), {49: RouteEntry((2,), True)})
        d = r.begin_packet(1, 49)
        self.assertEqual(d.outputs, (2,))
        self.assertEqual(r.output_owner[2], 1)                                 # TV-RTR-019

        # A second input targeting the locked output must wait.
        r.table[50] = RouteEntry((2,), True)
        self.assertTrue(r.begin_packet(3, 50).wait)                             # 020

        x = r.transfer_nchar(1, 0x55, ready_ports=[])
        self.assertTrue(x["wait"])
        self.assertFalse(x["sent"])                                             # 021

        freed = r.end_packet(1)
        self.assertEqual(freed, (2,))
        self.assertNotIn(2, r.output_owner)                                    # 023

        r = RouterModel(
            (1, 2, 3),
            {50: RouteEntry((2, 3), True, multicast=True)},
            multicast_enabled=True,
        )
        self.assertEqual(r.begin_packet(1, 50).outputs, (2, 3))
        x = r.transfer_nchar(1, 0xAA, ready_ports=[2])
        self.assertFalse(x["sent"])
        self.assertEqual(x["outputs"], ())                                      # 022

    def test_fair_reference_scheduler(self):
        a = FairRoundRobin()
        seq = [a.choose(1, [1, 2, 3]) for _ in range(6)]
        self.assertEqual(seq, [1, 2, 3, 1, 2, 3])                              # 032


if __name__ == "__main__":
    unittest.main()
