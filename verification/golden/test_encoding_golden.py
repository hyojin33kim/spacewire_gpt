import unittest

from golden_model.encoding.model import (
    CONTROL_TYPE,
    ControlChar,
    EncodingServiceState,
    ReceiveErrorKind,
    ReceiverSemanticState,
    broadcast_code,
    broadcast_fields,
    control_symbol,
    controlled_reset_delay_valid,
    data_symbol,
    disconnect_indication,
    disconnect_threshold_valid,
    ds_decode_valid,
    ds_encode,
    first_null_bits,
    got_null_indication,
    initial_rate_valid,
    maximum_rate_valid,
    minimum_rate_setting_valid,
    null_code,
    odd_parity_for_previous_payload,
    parity_valid,
    receive_error_indication,
    required_first_null_detection_bits,
)


class TestEncodingGolden(unittest.TestCase):
    def test_character_and_control_vectors(self):
        # TV-ENC-CHAR-001/002
        self.assertEqual(data_symbol(0x00, 1)[1:], [0,0,0,0,0,0,0,0,0])
        self.assertEqual(data_symbol(0xA5, 1), [1,0,1,0,1,0,0,1,0,1])
        # TV-ENC-CTRL-001..004 + Figure 5-12 transmitted order
        self.assertEqual(CONTROL_TYPE[ControlChar.FCT], 0b00)
        self.assertEqual(CONTROL_TYPE[ControlChar.EOP], 0b10)
        self.assertEqual(CONTROL_TYPE[ControlChar.EEP], 0b01)
        self.assertEqual(CONTROL_TYPE[ControlChar.ESC], 0b11)
        self.assertEqual(control_symbol(ControlChar.FCT, 0), [0,1,0,0])
        self.assertEqual(control_symbol(ControlChar.EOP, 0), [0,1,0,1])
        self.assertEqual(control_symbol(ControlChar.EEP, 0), [0,1,1,0])
        self.assertEqual(control_symbol(ControlChar.ESC, 0), [0,1,1,1])
        # TV-ENC-CODE-001/002
        self.assertEqual(null_code(), (ControlChar.ESC, ControlChar.FCT))
        self.assertEqual(broadcast_code(0b10101101), (ControlChar.ESC, 0b10101101))
        self.assertEqual(broadcast_fields(0b10101101), (0b10, 0b101101))

    def test_parity_vectors(self):
        # TV-ENC-PARITY-001..004
        p1 = odd_parity_for_previous_payload([0,0,1,1,1,0,1,0], 1)
        p2 = odd_parity_for_previous_payload([1,1], 1)
        p3 = odd_parity_for_previous_payload([0]*8, 0)
        p4 = odd_parity_for_previous_payload([1,0,0,0,0,0,0,0], 0)
        self.assertEqual((p1,p2,p3,p4), (0,0,1,0))
        self.assertTrue(parity_valid([0,0,1,1,1,0,1,0], p1, 1))
        # TV-ENC-PARITY-005: one covered-bit flip makes odd parity invalid
        self.assertFalse(parity_valid([1,0,1,1,1,0,1,0], p1, 1))

    def test_ds_vectors(self):
        bits = [0,1,0,0,1,1,0,1,1,0]
        levels = ds_encode(bits, 0, 0)
        # TV-ENC-DS-001
        self.assertEqual([d for d, _ in levels], [0,1,0,0,1,1,0,1,1,0])
        self.assertEqual([s for _, s in levels], [1,1,1,0,0,1,1,1,0,0])
        self.assertEqual(ds_decode_valid(levels, 0, 0), bits)
        # TV-ENC-DS-002 is represented by reset state D=0/S=0
        self.assertEqual(ds_encode([], 0, 0), [])
        # TV-ENC-DS-003: DEC-ENC-002 interval at 10 Mbps -> 100..500 ns
        self.assertTrue(controlled_reset_delay_valid(100.0, 10.0))
        self.assertTrue(controlled_reset_delay_valid(500.0, 10.0))
        self.assertFalse(controlled_reset_delay_valid(99.0, 10.0))
        self.assertFalse(controlled_reset_delay_valid(501.0, 10.0))
        # TV-ENC-DS-004: no data meaning is invented for simultaneous transition
        with self.assertRaises(ValueError):
            ds_decode_valid([(1,1)], 0, 0)

    def test_null_vectors(self):
        # TV-ENC-NULL-001/002
        self.assertEqual(first_null_bits(), (0,1,1,1,0,1,0,0))
        self.assertEqual(required_first_null_detection_bits(), (0,1,1,1,0,1,0,0,0))
        rx = ReceiverSemanticState()
        rx.set_rx_enable(True)
        self.assertTrue(rx.observe_first_null_detection([0,1,1,1,0,1,0,0,0], True))
        # TV-ENC-NULL-003
        rx.set_rx_enable(False)
        self.assertFalse(rx.got_null)
        # TV-ENC-NULL-004
        rx = ReceiverSemanticState(rx_enabled=True, got_null=False)
        self.assertFalse(rx.can_deliver_received_item(False))
        # TV-ENC-NULL-005
        self.assertFalse(rx.observe_first_null_detection([0,1,1,1,0,1,0,0,0], False))

    def test_error_vectors(self):
        rx = ReceiverSemanticState(rx_enabled=True, got_null=True)
        # TV-ENC-ERR-001..005
        self.assertTrue(rx.esc_error(ControlChar.ESC, ControlChar.ESC))
        self.assertTrue(rx.esc_error(ControlChar.ESC, ControlChar.EOP))
        self.assertTrue(rx.esc_error(ControlChar.ESC, ControlChar.EEP))
        self.assertFalse(rx.esc_error(ControlChar.ESC, ControlChar.FCT))
        self.assertFalse(rx.esc_error(ControlChar.ESC, 0x55))
        # TV-ENC-ERR-006/007
        rx.got_null = False
        self.assertFalse(rx.parity_error_active())
        rx.got_null = True
        self.assertTrue(rx.parity_error_active())

    def test_disconnect_vectors(self):
        # TV-ENC-DISC-005 configuration range
        self.assertTrue(disconnect_threshold_valid(850.0))
        self.assertFalse(disconnect_threshold_valid(727.0))
        self.assertFalse(disconnect_threshold_valid(1001.0))
        rx = ReceiverSemanticState()
        rx.set_rx_enable(True)
        # TV-ENC-DISC-001
        self.assertFalse(rx.disconnect(2000.0, 850.0))
        # TV-ENC-DISC-002
        rx.arm_disconnect_after_first_edge(True)
        self.assertTrue(rx.disconnect_armed)
        # TV-ENC-DISC-003/004
        self.assertFalse(rx.disconnect(850.0, 850.0))
        self.assertTrue(rx.disconnect(851.0, 850.0))

    def test_rate_vectors(self):
        # TV-ENC-RATE-001..003
        for rate in (9.0,10.0,11.0):
            self.assertTrue(initial_rate_valid(rate))
        self.assertFalse(initial_rate_valid(11.1))
        # TV-ENC-RATE-004
        self.assertTrue(minimum_rate_setting_valid(2.0, True))
        self.assertTrue(minimum_rate_setting_valid(5.0, False))
        self.assertFalse(minimum_rate_setting_valid(11.1, False))
        # TV-ENC-RATE-005
        self.assertTrue(maximum_rate_valid(100.0, 10.0, True))
        self.assertFalse(maximum_rate_valid(9.0, 10.0, True))
        self.assertFalse(maximum_rate_valid(100.0, 10.0, False))
        # TV-ENC-RATE-006 is a capability statement: the model imposes no equality constraint
        self.assertTrue(initial_rate_valid(10.0) and initial_rate_valid(11.0))

    def test_interface_vectors(self):
        svc = EncodingServiceState()
        # TV-ENC-IF-001/002
        svc.set_tx_enable(True)
        svc.set_rx_enable(True)
        self.assertTrue(svc.tx_enabled)
        self.assertTrue(svc.receiver.rx_enabled)
        # TV-ENC-IF-003/004/005
        self.assertEqual(receive_error_indication(ReceiveErrorKind.PARITY).parameter, "parity_error")
        self.assertEqual(receive_error_indication(ReceiveErrorKind.ESC).parameter, "ESC_error")
        self.assertEqual(got_null_indication().name, "gotNull")
        self.assertEqual(disconnect_indication().name, "DISCONNECT")


if __name__ == "__main__":
    unittest.main()
