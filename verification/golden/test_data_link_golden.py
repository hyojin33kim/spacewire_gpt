import unittest
from golden_model.data_link.model import *

class TestDataLink(unittest.TestCase):
    def test_credit(self):
        m=DataLinkModel(); self.assertTrue(m.receive_fct()); self.assertEqual(m.tx_credit,8)
        self.assertTrue(m.send_nchar()); self.assertEqual(m.tx_credit,7)
        m.tx_credit=0; self.assertFalse(m.send_nchar())
    def test_credit_errors(self):
        m=DataLinkModel(link_state=LinkState.RUN,tx_credit=56); self.assertFalse(m.receive_fct()); self.assertEqual(m.last_error,"CREDIT")
        m=DataLinkModel(link_state=LinkState.RUN,rx_credit=0); self.assertFalse(m.receive_nchar()); self.assertEqual(m.last_error,"CREDIT")
    def test_priority(self):
        m=DataLinkModel(link_state=LinkState.RUN,tx_credit=8)
        self.assertEqual(m.select_tx(broadcast=True,fct=True,nchar=True),"BROADCAST_CODE")
        self.assertEqual(m.select_tx(fct=True,nchar=True),"FCT")
        self.assertEqual(m.select_tx(nchar=True),"NCHAR")
        m.tx_credit=0; self.assertEqual(m.select_tx(nchar=True),"NULL")
    def test_init_sequence(self):
        m=DataLinkModel(); self.assertEqual(m.step_init(timer_elapsed=True),LinkState.ERROR_WAIT)
        self.assertEqual(m.step_init(timeout=True),LinkState.READY)
        self.assertEqual(m.step_init(LinkStart=True),LinkState.STARTED)
        self.assertEqual(m.step_init(sentNull=True,gotNull=True),LinkState.CONNECTING)
        self.assertEqual(m.step_init(sentFCT=True,gotFCT=True),LinkState.RUN)
    def test_run_error_and_recovery(self):
        m=DataLinkModel(link_state=LinkState.RUN,tx_packet_open=True,rx_packet_open=True)
        m.step_init(parity_error=True); self.assertEqual(m.link_state,LinkState.ERROR_RESET); self.assertEqual(m.recovery_state,RecoveryState.RECOVERY)
        r=m.recover(); self.assertTrue(r["discard_tx_remainder"]); self.assertTrue(r["append_eep"])
    def test_fct_issue(self):
        m=DataLinkModel(); self.assertTrue(m.send_fct(8)); self.assertEqual(m.rx_credit,8)
        self.assertFalse(m.send_fct(7))
    def test_optional_profile(self):
        self.assertFalse(accept_broadcast_request(LinkState.READY)); self.assertTrue(accept_broadcast_request(LinkState.RUN))

if __name__=="__main__": unittest.main()
