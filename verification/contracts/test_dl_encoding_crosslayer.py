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
    """Executable model of approved RTL-IF-X2/X3 ownership rules only."""

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
            if kind == "DATA":
                self.packet_open = True
            else:
                self.packet_open = False

    def accept(self, kind, same_edge_commit=False):
        if self.pending is not None:
            raise AssertionError("only one accepted-but-uncommitted item is allowed")
        if kind in NCHARS and (not self.fifo or self.fifo[0] != kind):
            raise AssertionError("accepted N-Char must be current FIFO head")
        if same_edge_commit:
            self._apply_commit(kind)
            return
        self.pending = kind

    def commit(self, kind):
        if self.pending != kind:
            raise AssertionError("phantom, stale, duplicate, or kind-mismatched commit")
        self._apply_commit(kind)
        self.pending = None

    def link_error(self, same_edge_commit_kind=None):
        # RTL-IF-X3: an already asserted matching commit wins before recovery.
        if same_edge_commit_kind is not None:
            self.commit(same_edge_commit_kind)

        if self.pending is None:
            return

        kind = self.pending
        self.pending = None

        if kind not in NCHARS:
            return

        if not self.packet_open:
            # Cancel reservation; FIFO head remains for retry.
            return

        # Pending N-Char belongs to unsent current-packet remainder.
        if not self.fifo or self.fifo[0] != kind:
            raise AssertionError("reserved item lost before recovery")
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


class TestCrossLayerStaticContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.enc = load_yaml(ENC)
        cls.dl = load_yaml(DL)

    def test_canonical_tx_request_and_commit_names_match(self):
        enc_if = self.enc["data_link_to_encoding_tx"]
        dl_if = self.dl["datalink_to_encoding_tx"]
        self.assertEqual(
            enc_if["request_fields"],
            [
                "enc_tx_item_valid",
                "enc_tx_item_ready",
                "enc_tx_item_kind",
                "enc_tx_item_data_7_0",
            ],
        )
        self.assertEqual(dl_if["request_signals"], enc_if["request_fields"])
        self.assertEqual(
            enc_if["commit_feedback"]["fields"],
            dl_if["commit_feedback_required"],
        )

    def test_raw_esc_is_encoding_internal_only(self):
        enc_if = self.enc["data_link_to_encoding_tx"]
        dl_if = self.dl["datalink_to_encoding_tx"]
        self.assertIn("raw_ESC", enc_if["prohibited_external_request_kind"])
        self.assertEqual(enc_if["internal_symbol_ownership"]["ESC"], "Encoding_internal_only")
        self.assertIn("raw_ESC", dl_if["prohibited_request_kind"])
        self.assertEqual(dl_if["raw_ESC_owner"], "Encoding_internal_only")

    def test_single_pending_item_rule_matches(self):
        self.assertEqual(
            self.enc["data_link_to_encoding_tx"]["pending_acceptance"]["max_items"], 1
        )
        self.assertEqual(
            self.dl["datalink_to_encoding_tx"]["pending_rule"][
                "max_accepted_but_uncommitted_items"
            ],
            1,
        )

    def test_rx_data_signal_name_is_identical_across_boundary(self):
        enc_outputs = self.enc["data_link_control"]["outputs"]
        dl_inputs = self.dl["encoding_to_datalink_rx"]["signals"]
        self.assertIn("enc_rx_item_data_7_0", enc_outputs)
        self.assertIn("enc_rx_item_data_7_0", dl_inputs)
        self.assertNotIn("enc_rx_data_7_0", dl_inputs)

    def test_fifo_reservation_contract_is_explicit(self):
        q = self.dl["fifo_contract"]["tx_fifo"]["dequeue_contract"]
        self.assertTrue(q["reservation_blocks_reissue"])
        self.assertIn("reserve", q["accept"])
        self.assertIn("pop exactly one", q["commit"])


class TestCrossLayerDirectedSequences(unittest.TestCase):
    def test_normal_data_accept_reserve_commit_pop_credit(self):
        m = TxBoundaryModel(["DATA", "EOP"], tx_credit=8)
        m.accept("DATA")
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertEqual(m.tx_credit, 8)
        self.assertFalse(m.packet_open)
        m.commit("DATA")
        self.assertEqual(m.fifo, ["EOP"])
        self.assertEqual(m.tx_credit, 7)
        self.assertTrue(m.packet_open)

    def test_same_edge_accept_commit_has_no_persistent_pending_state(self):
        m = TxBoundaryModel(["DATA"], tx_credit=1)
        m.accept("DATA", same_edge_commit=True)
        self.assertIsNone(m.pending)
        self.assertEqual(m.fifo, [])
        self.assertEqual(m.tx_credit, 0)
        self.assertTrue(m.packet_open)

    def test_normal_eop_commit_closes_packet(self):
        m = TxBoundaryModel(["EOP"], tx_credit=4, packet_open=True)
        m.accept("EOP")
        m.commit("EOP")
        self.assertEqual(m.fifo, [])
        self.assertEqual(m.tx_credit, 3)
        self.assertFalse(m.packet_open)

    def test_pending_eop_error_discards_only_eop_and_preserves_next_packet(self):
        m = TxBoundaryModel(["EOP", "DATA", "EOP"], packet_open=True)
        m.accept("EOP")
        m.link_error()
        self.assertEqual(m.discarded, ["EOP"])
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertFalse(m.packet_open)

    def test_same_edge_eop_commit_and_error_uses_post_commit_packet_state(self):
        m = TxBoundaryModel(["EOP", "DATA", "EOP"], packet_open=True)
        m.accept("EOP")
        m.link_error(same_edge_commit_kind="EOP")
        self.assertEqual(m.discarded, [])
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertFalse(m.packet_open)

    def test_first_data_pending_error_cancels_reservation_and_retains_data(self):
        m = TxBoundaryModel(["DATA", "EOP"], packet_open=False)
        m.accept("DATA")
        m.link_error()
        self.assertEqual(m.fifo, ["DATA", "EOP"])
        self.assertEqual(m.discarded, [])
        self.assertFalse(m.packet_open)

    def test_duplicate_or_stale_commit_is_rejected(self):
        m = TxBoundaryModel(["DATA"], tx_credit=2)
        m.accept("DATA")
        m.commit("DATA")
        with self.assertRaises(AssertionError):
            m.commit("DATA")

    def test_old_epoch_commit_after_precommit_cancel_is_rejected(self):
        m = TxBoundaryModel(["DATA"], packet_open=False)
        m.accept("DATA")
        m.link_error()
        with self.assertRaises(AssertionError):
            m.commit("DATA")


if __name__ == "__main__":
    unittest.main()
