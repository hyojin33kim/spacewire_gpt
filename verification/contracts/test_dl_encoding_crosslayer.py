import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
ENC = ROOT / "rtl_contract" / "5.4_encoding_rtl_contract.yaml"
DL = ROOT / "rtl_contract" / "5.5_data_link_rtl_contract.yaml"
NCHARS = {"DATA", "EOP", "EEP"}


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TxBoundaryModel:
    def __init__(self, fifo, tx_credit=8, packet_open=False):
        self.fifo = list(fifo)
        self.tx_credit = tx_credit
        self.packet_open = packet_open
        self.pending = None
        self.discarded = []

    def _apply_commit(self, kind):
        if kind in NCHARS:
            if not self.fifo or self.fifo[0] != kind:
                raise AssertionError("commit must match current FIFO head")
            self.fifo.pop(0)
            self.tx_credit -= 1
            if self.tx_credit < 0:
                raise AssertionError("credit underflow")
            self.packet_open = kind == "DATA"

    def accept(self, kind, same_edge_commit=False):
        if self.pending is not None:
            raise AssertionError("only one pending item")
        if kind in NCHARS and (not self.fifo or self.fifo[0] != kind):
            raise AssertionError("accepted N-Char must be FIFO head")
        if same_edge_commit:
            self._apply_commit(kind)
        else:
            self.pending = kind

    def commit(self, kind):
        if self.pending != kind:
            raise AssertionError("phantom/stale/duplicate/kind-mismatched commit")
        self._apply_commit(kind)
        self.pending = None

    def link_error(self, same_edge_commit_kind=None):
        if same_edge_commit_kind is not None:
            self.commit(same_edge_commit_kind)
        if self.pending is None:
            return
        kind = self.pending
        self.pending = None
        if kind not in NCHARS or not self.packet_open:
            return
        if not self.fifo or self.fifo[0] != kind:
            raise AssertionError("reserved item lost")
        self.discarded.append(self.fifo.pop(0))
        if kind in {"EOP", "EEP"}:
            self.packet_open = False
            return
        while self.fifo:
            x = self.fifo.pop(0)
            self.discarded.append(x)
            if x in {"EOP", "EEP"}:
                self.packet_open = False
                return


class TestDLENCContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.enc = load_yaml(ENC)
        cls.dl = load_yaml(DL)

    def test_boundary_names_and_raw_esc_owner(self):
        enc_if = self.enc["data_link_to_encoding_tx"]
        dl_if = self.dl["datalink_to_encoding_tx"]
        self.assertEqual(enc_if["request_fields"], dl_if["request_signals"])
        self.assertEqual(enc_if["commit_feedback"]["fields"], dl_if["commit_feedback_required"])
        self.assertIn("raw_ESC", enc_if["prohibited_external_request_kind"])
        self.assertIn("raw_ESC", dl_if["prohibited_request_kind"])
        self.assertEqual(dl_if["raw_ESC_owner"], "Encoding_internal_only")
        self.assertIn("enc_rx_item_data_7_0", self.enc["data_link_control"]["outputs"])
        self.assertIn("enc_rx_item_data_7_0", self.dl["encoding_to_datalink_rx"]["signals"])

    def test_single_pending_and_fifo_reservation(self):
        self.assertEqual(self.enc["data_link_to_encoding_tx"]["pending_acceptance"]["max_items"], 1)
        self.assertEqual(self.dl["datalink_to_encoding_tx"]["pending_rule"]["max_accepted_but_uncommitted_items"], 1)
        q = self.dl["fifo_contract"]["tx_fifo"]["dequeue_contract"]
        self.assertTrue(q["reservation_blocks_reissue"])

    def test_normal_data_accept_commit(self):
        m = TxBoundaryModel(["DATA", "EOP"], tx_credit=8)
        m.accept("DATA")
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertEqual(m.tx_credit, 8)
        m.commit("DATA")
        self.assertEqual(m.fifo, ["EOP"])
        self.assertEqual(m.tx_credit, 7)
        self.assertTrue(m.packet_open)

    def test_pending_eop_error_preserves_next_packet(self):
        m = TxBoundaryModel(["EOP", "DATA", "EOP"], packet_open=True)
        m.accept("EOP")
        m.link_error()
        self.assertEqual(m.discarded, ["EOP"])
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertFalse(m.packet_open)

    def test_same_edge_eop_commit_error_uses_post_commit_state(self):
        m = TxBoundaryModel(["EOP", "DATA", "EOP"], packet_open=True)
        m.accept("EOP")
        m.link_error(same_edge_commit_kind="EOP")
        self.assertEqual(m.discarded, [])
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertFalse(m.packet_open)

    def test_first_data_pending_error_retries_without_loss(self):
        m = TxBoundaryModel(["DATA", "EOP"], packet_open=False)
        m.accept("DATA")
        m.link_error()
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        with self.assertRaises(AssertionError):
            m.commit("DATA")

    def test_duplicate_commit_rejected(self):
        m = TxBoundaryModel(["DATA"], tx_credit=2)
        m.accept("DATA")
        m.commit("DATA")
        with self.assertRaises(AssertionError):
            m.commit("DATA")


if __name__ == "__main__":
    unittest.main()
