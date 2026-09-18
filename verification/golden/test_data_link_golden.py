import unittest

from golden_model.data_link.model import *


class TestDataLinkGolden(unittest.TestCase):
    def test_credit_vectors(self):
        m = DataLinkModel()
        self.assertTrue(m.receive_fct())
        self.assertEqual(m.tx_credit, 8)                       # TV-DL-001
        self.assertTrue(m.send_nchar())
        self.assertEqual(m.tx_credit, 7)                       # TV-DL-002
        m.tx_credit = 0
        self.assertFalse(m.send_nchar())                       # TV-DL-003

        m = DataLinkModel(link_state=LinkState.RUN, tx_credit=56)
        self.assertFalse(m.receive_fct())
        self.assertEqual(m.last_error, "CREDIT")               # TV-DL-004

        m = DataLinkModel(link_state=LinkState.RUN, rx_credit=0)
        self.assertFalse(m.receive_nchar())
        self.assertEqual(m.last_error, "CREDIT")               # TV-DL-005

        m = DataLinkModel()
        self.assertTrue(m.send_fct(8))
        self.assertEqual(m.rx_credit, 8)                        # TV-DL-021
        self.assertFalse(DataLinkModel().send_fct(7))           # TV-DL-022

    def test_priority_vectors(self):
        m = DataLinkModel(link_state=LinkState.RUN, tx_credit=8)
        self.assertEqual(
            m.select_tx(broadcast=True, fct=True, nchar=True),
            ItemKind.BROADCAST_CODE,
        )                                                       # TV-DL-006
        self.assertEqual(m.select_tx(fct=True, nchar=True), ItemKind.FCT)    # 007
        self.assertEqual(m.select_tx(nchar=True), ItemKind.NCHAR)            # 008
        m.tx_credit = 0
        self.assertEqual(m.select_tx(nchar=True), ItemKind.NULL)             # 009

        m.link_state = LinkState.STARTED
        self.assertEqual(
            m.select_tx(broadcast=True, fct=True, nchar=True), ItemKind.NULL
        )                                                       # TV-DL-040
        m.link_state = LinkState.CONNECTING
        self.assertEqual(
            m.select_tx(broadcast=True, fct=True, nchar=True), ItemKind.FCT
        )                                                       # TV-DL-041

    def test_initialisation_nominal_vectors(self):
        m = DataLinkModel()
        self.assertEqual(m.step_init(timer_elapsed=True), LinkState.ERROR_WAIT)  # 010
        self.assertEqual(m.step_init(timeout=True), LinkState.READY)             # 011
        self.assertEqual(m.step_init(LinkStart=True), LinkState.STARTED)          # 012

        m = DataLinkModel(link_state=LinkState.READY)
        self.assertEqual(
            m.step_init(AutoStart=True, gotNull=True), LinkState.STARTED
        )                                                                       # 013

        m = DataLinkModel(link_state=LinkState.STARTED)
        self.assertEqual(
            m.step_init(sentNull=True, gotNull=True), LinkState.CONNECTING
        )                                                                       # 014
        self.assertEqual(
            m.step_init(sentFCT=True, gotFCT=True), LinkState.RUN
        )                                                                       # 015

    def test_initialisation_error_vectors(self):
        m = DataLinkModel(link_state=LinkState.RUN)
        self.assertEqual(m.step_init(parity_error=True), LinkState.ERROR_RESET)
        self.assertEqual(m.recovery_state, RecoveryState.RECOVERY)              # 016

        m = DataLinkModel(link_state=LinkState.RUN)
        self.assertEqual(m.step_init(credit_error=True), LinkState.ERROR_RESET)
        self.assertEqual(m.recovery_state, RecoveryState.RECOVERY)              # 017

        self.assertEqual(
            DataLinkModel(link_state=LinkState.STARTED).step_init(timeout=True),
            LinkState.ERROR_RESET,
        )                                                                       # 018
        self.assertEqual(
            DataLinkModel(link_state=LinkState.CONNECTING).step_init(timeout=True),
            LinkState.ERROR_RESET,
        )                                                                       # 019

        self.assertEqual(
            DataLinkModel(link_state=LinkState.ERROR_WAIT).step_init(gotFCT=True),
            LinkState.ERROR_RESET,
        )                                                                       # 029
        self.assertEqual(
            DataLinkModel(link_state=LinkState.READY).step_init(gotNChar=True),
            LinkState.ERROR_RESET,
        )                                                                       # 030
        self.assertEqual(
            DataLinkModel(link_state=LinkState.STARTED).step_init(gotBC=True),
            LinkState.ERROR_RESET,
        )                                                                       # 031
        self.assertEqual(
            DataLinkModel(link_state=LinkState.CONNECTING).step_init(gotNChar=True),
            LinkState.ERROR_RESET,
        )                                                                       # 032

    def test_reset_and_recovery_vectors(self):
        m = DataLinkModel(tx_credit=24, rx_credit=32, pending_broadcast=3)
        m.enter_error_reset("TEST")
        self.assertEqual((m.tx_credit, m.rx_credit), (0, 0))                    # 020
        self.assertIsNone(m.pending_broadcast)                                  # 037

        m = DataLinkModel(
            link_state=LinkState.RUN,
            tx_packet_open=True,
            rx_packet_open=True,
            last_error="PARITY",
        )
        m.recovery_state = RecoveryState.RECOVERY
        r = m.recover()
        self.assertTrue(r["discard_tx_remainder"])
        self.assertTrue(r["append_eep"])                                        # 024
        self.assertFalse(r["extra_eep_after_closed_packet"])                    # 042 ref

    def test_directional_service_vectors(self):
        m = DataLinkModel(link_state=LinkState.RUN, tx_credit=1, rx_credit=1)
        e = m.send_nchar_from_network(0x55)
        self.assertEqual(e.direction, Direction.NETWORK_TO_ENCODING)
        self.assertEqual(m.tx_credit, 0)                                        # 025

        e = m.receive_nchar_from_encoding(0x55)
        self.assertEqual(e.direction, Direction.ENCODING_TO_NETWORK)
        self.assertEqual(m.rx_credit, 0)                                        # 026

        e = m.send_broadcast_from_network(7)
        self.assertEqual(e.direction, Direction.NETWORK_TO_ENCODING)            # 027
        e = m.receive_broadcast_from_encoding(7)
        self.assertEqual(e.direction, Direction.ENCODING_TO_NETWORK)            # 028

        self.assertFalse(accept_broadcast_request(LinkState.READY))              # 023,038
        self.assertTrue(accept_broadcast_request(LinkState.RUN))                 # 039

    def test_timing_vectors(self):
        self.assertTrue(error_reset_delay_valid(5.82))                           # 033
        self.assertFalse(error_reset_delay_valid(7.23))                          # 034
        self.assertTrue(state_timeout_valid(14.33))                              # 035
        self.assertFalse(state_timeout_valid(14.34))                             # 036


if __name__ == "__main__":
    unittest.main()
