from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RouteEntry:
    ports: tuple[int, ...] = ()
    valid: bool = False
    delete: bool = False
    adaptive: bool = False
    multicast: bool = False


@dataclass
class RouteDecision:
    outputs: tuple[int, ...] = ()
    consume_header: bool = False
    discard: bool = False
    wait: bool = False
    invalid_address_error: bool = False


@dataclass
class RouterModel:
    external_ports: tuple[int, ...] = (1, 2, 3, 4)
    table: dict[int, RouteEntry] = field(default_factory=dict)
    adaptive_enabled: bool = False
    multicast_enabled: bool = False
    rr_cursor: dict[int, int] = field(default_factory=dict)
    interrupt_active: set[int] = field(default_factory=set)
    interrupt_timer_running: set[int] = field(default_factory=set)
    timecode_register: int = 0
    legacy_path_adaptive_supported: bool = False
    configuration_port_path_only: bool = True

    interrupt_rx_enabled: set[int] | None = None
    interrupt_tx_enabled: set[int] | None = None
    ack_rx_enabled: set[int] | None = None
    ack_tx_enabled: set[int] | None = None

    output_owner: dict[int, int] = field(default_factory=dict)
    input_outputs: dict[int, tuple[int, ...]] = field(default_factory=dict)

    def __post_init__(self):
        ports = set(self.external_ports)
        if self.interrupt_rx_enabled is None:
            self.interrupt_rx_enabled = set(ports)
        if self.interrupt_tx_enabled is None:
            self.interrupt_tx_enabled = set(ports)
        if self.ack_rx_enabled is None:
            self.ack_rx_enabled = set(ports)
        if self.ack_tx_enabled is None:
            self.ack_tx_enabled = set(ports)

    def reset(self):
        for a in range(32, 256):
            self.table[a] = RouteEntry()
        self.adaptive_enabled = False
        self.multicast_enabled = False
        self.interrupt_active.clear()
        self.interrupt_timer_running.clear()
        self.timecode_register = 0
        self.output_owner.clear()
        self.input_outputs.clear()

    def route(
        self,
        header: int,
        *,
        enabled_ports=None,
        ready_ports=None,
        busy_ports=None,
    ) -> RouteDecision:
        enabled = set(self.external_ports if enabled_ports is None else enabled_ports)
        existing = {0, *self.external_ports}
        # Port 0 is the internal configuration port and is part of routing
        # availability even though it is not an external SpaceWire/FIFO port.
        ready = set((enabled | {0}) if ready_ports is None else ready_ports)
        busy = set(self.output_owner) | set(() if busy_ports is None else busy_ports)
        if not 0 <= header <= 255:
            raise ValueError("header")

        # Path address.
        if header <= 31:
            if header not in existing:
                return RouteDecision(discard=True, invalid_address_error=True)
            if header in busy or header not in ready:
                return RouteDecision(wait=True)
            return RouteDecision((header,), consume_header=True)

        # 255 is reserved; 5.6.8.5 note says discard/register invalid address.
        if header == 255:
            return RouteDecision(discard=True, invalid_address_error=True)

        entry = self.table.get(header, RouteEntry())
        if not entry.valid or not entry.ports or any(p not in existing for p in entry.ports):
            return RouteDecision(discard=True, invalid_address_error=True)

        candidates = tuple(p for p in entry.ports if p in enabled)

        if entry.multicast and self.multicast_enabled:
            if not candidates:
                return RouteDecision(discard=True)
            if any(p in busy for p in candidates) or not set(candidates).issubset(ready):
                return RouteDecision(wait=True)
            return RouteDecision(candidates, consume_header=entry.delete)

        if entry.adaptive and self.adaptive_enabled:
            free = [p for p in candidates if p not in busy and p in ready]
            if not free:
                return RouteDecision(wait=True)
            # Deterministic reference trace only. Normative compliance is fairness.
            idx = self.rr_cursor.get(header, 0) % len(free)
            p = free[idx]
            self.rr_cursor[header] = idx + 1
            return RouteDecision((p,), consume_header=entry.delete)

        p = entry.ports[0]
        if p not in enabled:
            return RouteDecision(discard=True)
        if p in busy or p not in ready:
            return RouteDecision(wait=True)
        return RouteDecision((p,), consume_header=entry.delete)

    # Wormhole allocation and packet lock. Output ownership is held until EOP/EEP
    # or explicit error termination.
    def begin_packet(
        self,
        input_port: int,
        header: int,
        *,
        enabled_ports=None,
        ready_ports=None,
    ) -> RouteDecision:
        decision = self.route(
            header,
            enabled_ports=enabled_ports,
            ready_ports=ready_ports,
        )
        if decision.discard or decision.wait or not decision.outputs:
            return decision
        for p in decision.outputs:
            self.output_owner[p] = input_port
        self.input_outputs[input_port] = decision.outputs
        return decision

    def transfer_nchar(
        self,
        input_port: int,
        value: int | str,
        *,
        ready_ports=None,
    ) -> dict[str, object]:
        outputs = self.input_outputs.get(input_port, ())
        if not outputs:
            return {"sent": False, "wait": True, "outputs": (), "value": value}
        ready = set(outputs if ready_ports is None else ready_ports)
        if not set(outputs).issubset(ready):
            # Multicast atomicity: no subset receives the N-Char.
            return {"sent": False, "wait": True, "outputs": (), "value": value}
        return {"sent": True, "wait": False, "outputs": outputs, "value": value}

    def end_packet(self, input_port: int) -> tuple[int, ...]:
        outputs = self.input_outputs.pop(input_port, ())
        for p in outputs:
            if self.output_owner.get(p) == input_port:
                del self.output_owner[p]
        return outputs

    def terminate_packet_on_error(self, input_port: int) -> tuple[int, ...]:
        return self.end_packet(input_port)

    def stuck_packet(
        self,
        *,
        started: bool,
        ended: bool,
        idle_time: float,
        timeout: float,
        enabled: bool = True,
    ) -> dict[str, object]:
        stuck = enabled and started and not ended and idle_time > timeout
        return {
            "stuck": stuck,
            "discard": stuck,
            "send_EEP": stuck,
            "send_EEP_to_output_port": stuck,
            "error": stuck,
        }

    def receive_timecode(self, value: int, ingress: int, output_ports=None):
        if not 0 <= value < 64:
            raise ValueError("time-code")
        valid = value == ((self.timecode_register + 1) & 0x3F)
        self.timecode_register = value
        ports = self.external_ports if output_ports is None else tuple(output_ports)
        relay = tuple(p for p in ports if p != ingress) if valid else ()
        return {"valid": valid, "relay": relay, "new_register": value}

    def receive_interrupt(self, iid: int, ingress: int, output_ports=None):
        if not 0 <= iid <= 31:
            raise ValueError("IID")
        if ingress not in self.interrupt_rx_enabled:
            return {"discard": True, "relay": (), "active_after": iid in self.interrupt_active}
        if iid in self.interrupt_active:
            return {"discard": True, "relay": (), "active_after": True}
        self.interrupt_active.add(iid)
        self.interrupt_timer_running.add(iid)
        ports = self.external_ports if output_ports is None else tuple(output_ports)
        relay = tuple(
            p for p in ports
            if p != ingress and p in self.interrupt_tx_enabled
        )
        return {"discard": False, "relay": relay, "active_after": True}

    def receive_interrupt_ack(self, iid: int, ingress: int, output_ports=None):
        if not 0 <= iid <= 31:
            raise ValueError("IID")
        if ingress not in self.ack_rx_enabled:
            return {"ignored": False, "discard": True, "relay": (), "active_after": iid in self.interrupt_active}
        if iid not in self.interrupt_active:
            return {"ignored": True, "discard": False, "relay": (), "active_after": False}
        self.interrupt_active.remove(iid)
        self.interrupt_timer_running.discard(iid)
        ports = self.external_ports if output_ports is None else tuple(output_ports)
        relay = tuple(p for p in ports if p != ingress and p in self.ack_tx_enabled)
        return {"ignored": False, "discard": False, "relay": relay, "active_after": False}

    def interrupt_timeout(self, iid: int):
        self.interrupt_active.discard(iid)
        self.interrupt_timer_running.discard(iid)


class FairRoundRobin:
    """Deterministic reference scheduler; exact RR order is not normative."""

    def __init__(self):
        self.last: dict[int, int] = {}

    def choose(self, output: int, contenders: list[int]):
        if not contenders:
            return None
        ordered = sorted(contenders)
        last = self.last.get(output, ordered[-1])
        later = [x for x in ordered if x > last]
        winner = later[0] if later else ordered[0]
        self.last[output] = winner
        return winner
