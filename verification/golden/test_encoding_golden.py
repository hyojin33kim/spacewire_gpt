import unittest

from golden_model.encoding.model import (
    ControlChar,
    ReceiverSemanticState,
    broadcast_code,
    controlled_reset_delay_valid,
    disconnect_threshold_valid,
    ds_decode_valid,
    ds_encode,
    first_null_bits,
    initial_rate_valid,
    maximum_rate_valid,
    minimum_rate_setting_valid,
    null_code,
    odd_parity_for_previous_payload,
    required_first_null_detection_bits,
)


class TestEncodingGolden(unittest.TestCase):
    def test_control_codes(self):
        self.assertEqual(null_code(), (ControlChar.ESC, ControlChar.FCT))
        self.assertEqual(broadcast_code(0b10101101), (ControlChar.ESC, 0b10101101))

    def test_concrete_parity_vectors(self):
        self.assertEqual(odd_parity_for_previous_payload([0,0,1,1,1,0,1,0], 1), 0)  # 0x5C -> ESC
        self.assertEqual(odd_parity_for_previous_payload([1,1], 1), 0)                  # ESC -> FCT
        self.assertEqual(odd_parity_for_previous_payload([0]*8, 0), 1)
        self.assertEqual(odd_parity_for_previous_payload([1,0,0,0,0,0,0,0], 0), 0)

    def test_first_null_vectors(self):
        self.assertEqual(first_null_bits(), (0,1,1,1,0,1,0,0))
        self.assertEqual(required_first_null_detection_bits(), (0,1,1,1,0,1,0,0,0))

    def test_ds_encode_decode_figure_vector(self):
        bits = [0,1,0,0,1,1,0,1,1,0]
        levels = ds_encode(bits, 0, 0)
        self.assertEqual([d for d, _ in levels], [0,1,0,0,1,1,0,1,1,0])
        self.assertEqual([s for _, s in levels], [1,1,1,0,0,1,1,1,0,0])
        self.assertEqual(ds_decode_valid(levels, 0, 0), bits)

    def test_ds_decoder_does_not_invent_simultaneous_transition_data(self):
        with self.assertRaises(ValueError):
            ds_decode_valid([(1,1)], 0, 0)

    def test_controlled_reset_delay_range(self):
        self.assertTrue(controlled_reset_delay_valid(100.0, 10.0))
        self.assertTrue(controlled_reset_delay_valid(500.0, 10.0))
        self.assertFalse(controlled_reset_delay_valid(99.0, 10.0))
        self.assertFalse(controlled_reset_delay_valid(501.0, 10.0))

    def test_gotnull_lifetime_and_delivery_gate(self):
        rx = ReceiverSemanticState()
        rx.set_rx_enable(True)
        self.assertFalse(rx.can_deliver_received_item(False))
        self.assertTrue(rx.observe_first_null_detection([0,1,1,1,0,1,0,0,0]))
        self.assertTrue(rx.can_deliver_received_item(False))
        self.assertFalse(rx.can_deliver_received_item(True))
        rx.set_rx_enable(False)
        self.assertFalse(rx.got_null)

    def test_esc_error_vectors(self):
        rx = ReceiverSemanticState(rx_enabled=True, got_null=True)
        self.assertTrue(rx.esc_error(ControlChar.ESC, ControlChar.ESC))
        self.assertTrue(rx.esc_error(ControlChar.ESC, ControlChar.EOP))
        self.assertTrue(rx.esc_error(ControlChar.ESC, ControlChar.EEP))
        self.assertFalse(rx.esc_error(ControlChar.ESC, ControlChar.FCT))
        self.assertFalse(rx.esc_error(ControlChar.ESC, 0x55))

    def test_disconnect(self):
        self.assertTrue(disconnect_threshold_valid(850.0))
        self.assertFalse(disconnect_threshold_valid(727.0))
        self.assertFalse(disconnect_threshold_valid(1001.0))
        rx = ReceiverSemanticState()
        rx.set_rx_enable(True)
        self.assertFalse(rx.disconnect(2000.0, 850.0))
        rx.arm_disconnect_after_first_edge(True)
        self.assertFalse(rx.disconnect(850.0, 850.0))
        self.assertTrue(rx.disconnect(851.0, 850.0))

    def test_rate_constraints(self):
        self.assertTrue(initial_rate_valid(9.0))
        self.assertTrue(initial_rate_valid(10.0))
        self.assertTrue(initial_rate_valid(11.0))
        self.assertFalse(initial_rate_valid(11.1))
        self.assertTrue(minimum_rate_setting_valid(2.0, True))
        self.assertTrue(minimum_rate_setting_valid(5.0, False))
        self.assertFalse(minimum_rate_setting_valid(11.1, False))
        self.assertTrue(maximum_rate_valid(100.0, 10.0, True))
        self.assertFalse(maximum_rate_valid(9.0, 10.0, True))


if __name__ == "__main__":
    unittest.main()
