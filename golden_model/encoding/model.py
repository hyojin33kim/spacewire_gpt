"""SpaceWire Encoding semantic Golden Model.

Baseline: semantic-encoding-v0.1
This model represents protocol-observable behavior only. It intentionally does
not encode RTL cycle timing, CDC, synchronizer, pipeline, or counter choices.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence


SEMANTIC_BASELINE = "semantic-encoding-v0.1"


class ControlChar(str, Enum):
    FCT = "FCT"
    EOP = "EOP"
    EEP = "EEP"
    ESC = "ESC"


CONTROL_TYPE = {
    ControlChar.FCT: 0b00,
    ControlChar.EOP: 0b10,
    ControlChar.EEP: 0b01,
    ControlChar.ESC: 0b11,
}


def bits_lsb(value: int, width: int) -> list[int]:
    if value < 0 or value >= (1 << width):
        raise ValueError(f"value {value} does not fit {width} bits")
    return [(value >> i) & 1 for i in range(width)]


def odd_parity_for_previous_payload(previous_payload_bits: Sequence[int], current_dc_flag: int) -> int:
    """Return current parity bit per §5.4.3.4.

    The current parity bit covers the previous character payload bits plus the
    current parity bit and current data/control flag.
    """
    if current_dc_flag not in (0, 1):
        raise ValueError("current_dc_flag must be 0 or 1")
    if len(previous_payload_bits) not in (2, 8):
        raise ValueError("previous payload must be 2 control bits or 8 data bits")
    if any(b not in (0, 1) for b in previous_payload_bits):
        raise ValueError("payload bits must be binary")
    ones_without_parity = sum(previous_payload_bits) + current_dc_flag
    return 0 if ones_without_parity % 2 == 1 else 1


def data_symbol(value: int, parity_bit: int) -> list[int]:
    """Return [P, C, B0..B7]."""
    if parity_bit not in (0, 1):
        raise ValueError("parity_bit must be binary")
    return [parity_bit, 0, *bits_lsb(value, 8)]


def control_symbol(char: ControlChar, parity_bit: int) -> list[int]:
    """Return [P, C, T0, T1], with type encoded per the Standard.

    For control values whose two bits differ, the enum's numeric value is
    retained as the semantic type; bit-order interpretation remains governed by
    the source figure/convention and is not needed by current frozen vectors.
    """
    if parity_bit not in (0, 1):
        raise ValueError("parity_bit must be binary")
    t = CONTROL_TYPE[char]
    return [parity_bit, 1, t & 1, (t >> 1) & 1]


def null_code() -> tuple[ControlChar, ControlChar]:
    return (ControlChar.ESC, ControlChar.FCT)


def broadcast_code(value: int) -> tuple[ControlChar, int]:
    if value < 0 or value > 0xFF:
        raise ValueError("broadcast code value must be one byte")
    return (ControlChar.ESC, value)


FIRST_NULL_BITS = (0, 1, 1, 1, 0, 1, 0, 0)
FIRST_NULL_DETECTION_BITS = (0, 1, 1, 1, 0, 1, 0, 0, 0)


def first_null_bits() -> tuple[int, ...]:
    return FIRST_NULL_BITS


def required_first_null_detection_bits() -> tuple[int, ...]:
    return FIRST_NULL_DETECTION_BITS


def ds_encode(serial_bits: Sequence[int], initial_data: int = 0, initial_strobe: int = 0) -> list[tuple[int, int]]:
    """Encode a serial bit stream into Data/Strobe levels after each bit."""
    if initial_data not in (0, 1) or initial_strobe not in (0, 1):
        raise ValueError("initial Data/Strobe must be binary")
    d = initial_data
    s = initial_strobe
    out: list[tuple[int, int]] = []
    for bit in serial_bits:
        if bit not in (0, 1):
            raise ValueError("serial bits must be binary")
        if bit == d:
            s ^= 1
        else:
            d = bit
        out.append((d, s))
    return out


def ds_decode_valid(levels: Sequence[tuple[int, int]], initial_data: int = 0, initial_strobe: int = 0) -> list[int]:
    """Recover bits from a valid normal-operation DS waveform.

    Exactly one of Data/Strobe must transition at each encoded bit boundary.
    Simultaneous transitions are tolerated by a receiver but are not normal
    SpaceWire data symbols, so they are rejected by this *valid-waveform*
    semantic decoder rather than assigned invented data.
    """
    prev_d, prev_s = initial_data, initial_strobe
    bits: list[int] = []
    for d, s in levels:
        if d not in (0, 1) or s not in (0, 1):
            raise ValueError("Data/Strobe levels must be binary")
        transitions = int(d != prev_d) + int(s != prev_s)
        if transitions != 1:
            raise ValueError("not a normal valid DS bit boundary")
        bits.append(d)
        prev_d, prev_s = d, s
    return bits


def controlled_reset_delay_valid(delay_ns: float, fastest_supported_rate_mbps: float) -> bool:
    """DEC-ENC-002: T_fastest <= delay <= 500 ns."""
    if fastest_supported_rate_mbps <= 0:
        raise ValueError("rate must be positive")
    t_fastest_ns = 1000.0 / fastest_supported_rate_mbps
    return t_fastest_ns <= delay_ns <= 500.0


def disconnect_threshold_valid(threshold_ns: float) -> bool:
    """§5.4.8.c allowed implementation threshold range."""
    return 727.0 < threshold_ns <= 1000.0


@dataclass
class ReceiverSemanticState:
    rx_enabled: bool = False
    got_null: bool = False
    disconnect_armed: bool = False

    def set_rx_enable(self, enabled: bool) -> None:
        self.rx_enabled = bool(enabled)
        if not self.rx_enabled:
            self.got_null = False
            self.disconnect_armed = False

    def observe_first_null_detection(self, bits: Sequence[int], parity_context_ok: bool = True) -> bool:
        if self.rx_enabled and parity_context_ok and tuple(bits) == FIRST_NULL_DETECTION_BITS:
            self.got_null = True
        return self.got_null

    def parity_error_active(self) -> bool:
        return self.rx_enabled and self.got_null

    def esc_error_active(self) -> bool:
        return self.got_null

    def esc_error(self, first: ControlChar, second: ControlChar | int) -> bool:
        if not self.esc_error_active() or first is not ControlChar.ESC:
            return False
        return second in (ControlChar.ESC, ControlChar.EOP, ControlChar.EEP)

    def can_deliver_received_item(self, parity_error: bool) -> bool:
        return self.got_null and not parity_error

    def arm_disconnect_after_first_edge(self, link_has_left_error_reset: bool) -> None:
        if self.rx_enabled and link_has_left_error_reset:
            self.disconnect_armed = True

    def disconnect(self, elapsed_since_last_edge_ns: float, selected_threshold_ns: float) -> bool:
        if not disconnect_threshold_valid(selected_threshold_ns):
            raise ValueError("disconnect threshold outside §5.4.8.c range")
        return self.disconnect_armed and elapsed_since_last_edge_ns > selected_threshold_ns


def initial_rate_valid(rate_mbps: float) -> bool:
    return 9.0 <= rate_mbps <= 11.0


def minimum_rate_setting_valid(rate_mbps: float, two_mbps_operation_required: bool = True) -> bool:
    if two_mbps_operation_required:
        return rate_mbps == 2.0
    return 2.0 < rate_mbps <= 11.0


def maximum_rate_valid(max_rate_mbps: float, initial_rate_mbps: float, decodes_correctly: bool) -> bool:
    return initial_rate_valid(initial_rate_mbps) and max_rate_mbps >= initial_rate_mbps and decodes_correctly
