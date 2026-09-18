from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LinkState(str, Enum):
    ERROR_RESET = "ErrorReset"
    ERROR_WAIT = "ErrorWait"
    READY = "Ready"
    STARTED = "Started"
    CONNECTING = "Connecting"
    RUN = "Run"


class RecoveryState(str, Enum):
    NORMAL = "Normal"
    RECOVERY = "Recovery"


class Direction(str, Enum):
    NETWORK_TO_ENCODING = "NETWORK_TO_ENCODING"
    ENCODING_TO_NETWORK = "ENCODING_TO_NETWORK"


class ItemKind(str, Enum):
    NCHAR = "NCHAR"
    BROADCAST_CODE = "BROADCAST_CODE"
    FCT = "FCT"
    NULL = "NULL"


@dataclass(frozen=True)
class ServiceEvent:
    direction: Direction
    kind: ItemKind
    value: int | str | None = None


PRIORITY = (
    ItemKind.BROADCAST_CODE,
    ItemKind.FCT,
    ItemKind.NCHAR,
    ItemKind.NULL,
)

ERROR_RESET_DELAY_US = (5.82, 7.22)
STATE_TIMEOUT_US = (11.64, 14.33)


def error_reset_delay_valid(delay_us: float) -> bool:
    return ERROR_RESET_DELAY_US[0] <= delay_us <= ERROR_RESET_DELAY_US[1]


def state_timeout_valid(delay_us: float) -> bool:
    return STATE_TIMEOUT_US[0] <= delay_us <= STATE_TIMEOUT_US[1]


@dataclass
class DataLinkModel:
    link_state: LinkState = LinkState.ERROR_RESET
    recovery_state: RecoveryState = RecoveryState.NORMAL
    tx_credit: int = 0
    rx_credit: int = 0
    gotFCT: bool = False
    sentNull: bool = False
    sentFCT: bool = False
    tx_packet_open: bool = False
    rx_packet_open: bool = False
    last_error: str | None = None
    pending_broadcast: int | None = None

    # Selected GOLDEN-FULL-REFERENCE-V0.1 profile.
    tx_credit_max: int = 56
    rx_credit_max: int = 56

    def port_reset(self) -> None:
        self.link_state = LinkState.ERROR_RESET
        self.recovery_state = RecoveryState.NORMAL
        self.tx_credit = 0
        self.rx_credit = 0
        self.gotFCT = False
        self.sentNull = False
        self.sentFCT = False
        self.tx_packet_open = False
        self.rx_packet_open = False
        self.last_error = None
        self.pending_broadcast = None

    def enter_error_reset(self, error: str | None = None) -> None:
        was_run = self.link_state is LinkState.RUN
        if was_run and error is not None:
            self.recovery_state = RecoveryState.RECOVERY
            self.last_error = error
        self.link_state = LinkState.ERROR_RESET
        self.tx_credit = 0
        self.rx_credit = 0
        self.gotFCT = False
        # Selected SHOULD in 5.5.7.2.b / 5.5.9.
        self.pending_broadcast = None

    def receive_fct(self) -> bool:
        if self.tx_credit + 8 > self.tx_credit_max:
            self.enter_error_reset("CREDIT")
            return False
        self.tx_credit += 8
        self.gotFCT = True
        return True

    def send_nchar(self) -> bool:
        if self.tx_credit <= 0:
            return False
        self.tx_credit -= 1
        return True

    def receive_nchar(self) -> bool:
        if self.rx_credit <= 0:
            self.enter_error_reset("CREDIT")
            return False
        self.rx_credit -= 1
        return True

    def can_send_fct(self, rx_fifo_free: int) -> bool:
        return rx_fifo_free >= 8 and self.rx_credit <= self.rx_credit_max - 8

    def send_fct(self, rx_fifo_free: int) -> bool:
        if not self.can_send_fct(rx_fifo_free):
            return False
        self.rx_credit += 8
        self.sentFCT = True
        return True

    def select_tx(self, *, broadcast: bool = False, fct: bool = False, nchar: bool = False):
        if self.link_state is LinkState.STARTED:
            return ItemKind.NULL
        if self.link_state is LinkState.CONNECTING:
            return ItemKind.FCT if fct else ItemKind.NULL
        if self.link_state is not LinkState.RUN:
            return None
        if broadcast:
            return ItemKind.BROADCAST_CODE
        if fct:
            return ItemKind.FCT
        if nchar and self.tx_credit > 0:
            return ItemKind.NCHAR
        return ItemKind.NULL

    # Directionally typed service behavior. This is the explicit resolution of
    # the ambiguous word "received" in 5.5.7.7.a.3.
    def send_nchar_from_network(self, value: int | str) -> ServiceEvent | None:
        if self.link_state is not LinkState.RUN or not self.send_nchar():
            return None
        return ServiceEvent(Direction.NETWORK_TO_ENCODING, ItemKind.NCHAR, value)

    def send_broadcast_from_network(self, value: int) -> ServiceEvent | None:
        if self.link_state is not LinkState.RUN:
            return None
        return ServiceEvent(Direction.NETWORK_TO_ENCODING, ItemKind.BROADCAST_CODE, value)

    def receive_nchar_from_encoding(self, value: int | str) -> ServiceEvent | None:
        if self.link_state is not LinkState.RUN:
            return None
        if not self.receive_nchar():
            return None
        return ServiceEvent(Direction.ENCODING_TO_NETWORK, ItemKind.NCHAR, value)

    def receive_broadcast_from_encoding(self, value: int) -> ServiceEvent | None:
        if self.link_state is not LinkState.RUN:
            return None
        return ServiceEvent(Direction.ENCODING_TO_NETWORK, ItemKind.BROADCAST_CODE, value)

    def step_init(self, **e) -> LinkState:
        s = self.link_state

        # Rev.1 LinkDisabled is recognized globally; link errors are relevant
        # once the receiver/status logic has qualified them.
        link_error = any(e.get(k, False) for k in ("disconnect", "parity_error", "esc_error"))
        if e.get("LinkDisabled", False) or link_error or (s is LinkState.RUN and e.get("credit_error", False)):
            cause = next(
                (k.upper() for k in ("disconnect", "parity_error", "esc_error", "credit_error") if e.get(k)),
                "DISABLED",
            )
            self.enter_error_reset(cause)
            return self.link_state

        illegal_rx = any(e.get(k, False) for k in ("gotNChar", "gotBC"))
        got_fct = bool(e.get("gotFCT", False))

        if s is LinkState.ERROR_RESET:
            if e.get("timer_elapsed", False):
                self.link_state = LinkState.ERROR_WAIT

        elif s is LinkState.ERROR_WAIT:
            if got_fct or illegal_rx:
                self.enter_error_reset("PROTOCOL")
            elif e.get("timeout", False):
                self.link_state = LinkState.READY

        elif s is LinkState.READY:
            if got_fct or illegal_rx:
                self.enter_error_reset("PROTOCOL")
            elif e.get("LinkStart", False) or (e.get("AutoStart", False) and e.get("gotNull", False)):
                self.link_state = LinkState.STARTED

        elif s is LinkState.STARTED:
            if got_fct or illegal_rx:
                self.enter_error_reset("PROTOCOL")
            elif e.get("sentNull", False) and e.get("gotNull", False):
                self.sentNull = True
                self.link_state = LinkState.CONNECTING
            elif e.get("timeout", False):
                self.enter_error_reset("START_TIMEOUT")

        elif s is LinkState.CONNECTING:
            if illegal_rx:
                self.enter_error_reset("PROTOCOL")
            elif e.get("sentFCT", False) and got_fct:
                self.sentFCT = True
                self.gotFCT = True
                self.link_state = LinkState.RUN
            elif e.get("timeout", False):
                self.enter_error_reset("CONNECT_TIMEOUT")

        # In Run, gotFCT/gotNChar/gotBC are normal protocol activity.
        return self.link_state

    def recover(self, *, last_rx_was_data: bool | None = None) -> dict[str, object]:
        append_eep = self.rx_packet_open if last_rx_was_data is None else last_rx_was_data
        result = {
            "discard_tx_remainder": self.tx_packet_open,
            "append_eep": append_eep,
            # 5.5.8.4.a.3 is CAN: when the last character was EOP/EEP an
            # extra EEP is legal but not required. Reference trace chooses no.
            "extra_eep_after_closed_packet": False,
            "recorded_error": self.last_error,
        }
        self.tx_packet_open = False
        self.rx_packet_open = False
        self.recovery_state = RecoveryState.NORMAL
        return result

    def status(self) -> dict[str, object]:
        return {
            "link_state": self.link_state,
            "last_error": self.last_error,
            "tx_credit": self.tx_credit,
            "rx_credit": self.rx_credit,
        }


def accept_broadcast_request(state: LinkState) -> bool:
    # Selected SHOULD: requests outside Run are discarded rather than queued.
    return state is LinkState.RUN
