from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class LinkState(str, Enum):
    ERROR_RESET="ErrorReset"; ERROR_WAIT="ErrorWait"; READY="Ready"
    STARTED="Started"; CONNECTING="Connecting"; RUN="Run"
class RecoveryState(str, Enum):
    NORMAL="Normal"; RECOVERY="Recovery"

PRIORITY=("BROADCAST_CODE","FCT","NCHAR","NULL")

@dataclass
class DataLinkModel:
    link_state: LinkState=LinkState.ERROR_RESET
    recovery_state: RecoveryState=RecoveryState.NORMAL
    tx_credit: int=0
    rx_credit: int=0
    gotFCT: bool=False
    sentNull: bool=False
    sentFCT: bool=False
    tx_packet_open: bool=False
    rx_packet_open: bool=False
    last_error: str|None=None

    def enter_error_reset(self, error: str|None=None):
        if self.link_state is LinkState.RUN and error is not None:
            self.recovery_state=RecoveryState.RECOVERY
            self.last_error=error
        self.link_state=LinkState.ERROR_RESET
        self.tx_credit=0; self.rx_credit=0; self.gotFCT=False

    def receive_fct(self):
        if self.tx_credit+8>56:
            self.enter_error_reset("CREDIT")
            return False
        self.tx_credit+=8; self.gotFCT=True; return True

    def send_nchar(self):
        if self.tx_credit<=0: return False
        self.tx_credit-=1; return True

    def receive_nchar(self):
        if self.rx_credit<=0:
            self.enter_error_reset("CREDIT")
            return False
        self.rx_credit-=1; return True

    def can_send_fct(self, rx_fifo_free: int) -> bool:
        return rx_fifo_free>=8 and self.rx_credit<=48

    def send_fct(self, rx_fifo_free: int) -> bool:
        if not self.can_send_fct(rx_fifo_free): return False
        self.rx_credit+=8; self.sentFCT=True; return True

    def select_tx(self, *, broadcast=False, fct=False, nchar=False):
        if broadcast and self.link_state is LinkState.RUN: return "BROADCAST_CODE"
        if fct: return "FCT"
        if nchar and self.link_state is LinkState.RUN and self.tx_credit>0: return "NCHAR"
        return "NULL"

    def step_init(self, **e):
        s=self.link_state
        err=e.get("LinkDisabled") or e.get("disconnect") or e.get("parity_error") or e.get("esc_error")
        if s is LinkState.RUN and e.get("credit_error"): err=True
        if err:
            self.enter_error_reset(next((k.upper() for k in ("disconnect","parity_error","esc_error","credit_error") if e.get(k)), "DISABLED"))
            return self.link_state
        if s is LinkState.ERROR_RESET and e.get("timer_elapsed") and not e.get("LinkDisabled",False):
            self.link_state=LinkState.ERROR_WAIT
        elif s is LinkState.ERROR_WAIT:
            if e.get("illegal_item"): self.enter_error_reset("PROTOCOL")
            elif e.get("timeout"): self.link_state=LinkState.READY
        elif s is LinkState.READY:
            if e.get("illegal_item"): self.enter_error_reset("PROTOCOL")
            elif e.get("LinkStart") or (e.get("AutoStart") and e.get("gotNull")): self.link_state=LinkState.STARTED
        elif s is LinkState.STARTED:
            if e.get("illegal_item"): self.enter_error_reset("PROTOCOL")
            elif e.get("sentNull") and e.get("gotNull"): self.link_state=LinkState.CONNECTING
            elif e.get("timeout"): self.enter_error_reset("START_TIMEOUT")
        elif s is LinkState.CONNECTING:
            if e.get("illegal_item"): self.enter_error_reset("PROTOCOL")
            elif e.get("sentFCT") and e.get("gotFCT"): self.link_state=LinkState.RUN
            elif e.get("timeout"): self.enter_error_reset("CONNECT_TIMEOUT")
        return self.link_state

    def recover(self):
        result={"discard_tx_remainder":self.tx_packet_open,
                "append_eep":self.rx_packet_open,
                "recorded_error":self.last_error}
        self.tx_packet_open=False; self.rx_packet_open=False
        self.recovery_state=RecoveryState.NORMAL
        return result

def accept_broadcast_request(state: LinkState) -> bool:
    return state is LinkState.RUN
