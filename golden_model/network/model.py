from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PacketEnd(str, Enum):
    EOP = "EOP"
    EEP = "EEP"


@dataclass(frozen=True)
class Packet:
    data: tuple[int, ...]
    end: PacketEnd

    def __post_init__(self):
        if any(not 0 <= x <= 255 for x in self.data):
            raise ValueError("data character out of range")
        # CR-NET-001: zero-data-character packets are accepted according to
        # 5.6.2.1.d and its explicit empty-packet note.


def packets_interleaved(stream_packet_ids: list[int]) -> bool:
    closed: set[int] = set()
    current = None
    for pid in stream_packet_ids:
        if pid != current:
            if pid in closed:
                return True
            if current is not None:
                closed.add(current)
            current = pid
    return False


def first_router_packet_action(packet: Packet) -> str:
    # 5.6.2.1.d NOTE: empty packets are discarded by the first routing switch.
    return "DISCARD" if len(packet.data) == 0 else "ROUTE"


class BroadcastKind(str, Enum):
    TIME_CODE = "TIME_CODE"
    INTERRUPT_ACK = "INTERRUPT_ACK"
    INTERRUPT = "INTERRUPT"


BROADCAST_PRIORITY = (
    BroadcastKind.TIME_CODE,
    BroadcastKind.INTERRUPT_ACK,
    BroadcastKind.INTERRUPT,
)


def select_broadcast(candidates: set[BroadcastKind]) -> BroadcastKind | None:
    for kind in BROADCAST_PRIORITY:
        if kind in candidates:
            return kind
    return None


def reserved_broadcast_action(type_bits: int, *, entity: str) -> str:
    if type_bits not in (0b01, 0b11):
        return "PROCESS"
    if entity == "router":
        return "DELETE_NOT_FORWARD"
    if entity == "node":
        return "DISCARD"
    raise ValueError("entity must be router or node")


@dataclass
class TimeCodeRegister:
    value: int = 0

    def reset(self) -> None:
        self.value = 0

    def receive(self, received: int) -> dict[str, object]:
        if not 0 <= received < 64:
            raise ValueError("time-code must be 6-bit")
        valid = received == ((self.value + 1) & 0x3F)
        self.value = received
        return {
            "valid": valid,
            "notify_host": valid,
            "new_register": self.value,
        }


def timecode_broadcast_code(value: int) -> dict[str, int]:
    if not 0 <= value < 64:
        raise ValueError("time-code must be 6-bit")
    return {"type": 0b00, "value": value}


def redundant_timecode_master_valid(register_ids: list[str]) -> bool:
    return bool(register_ids) and len(set(register_ids)) == 1


class InterruptMode(str, Enum):
    INTERRUPT = "interrupt"
    ACK = "interrupt_with_acknowledgement"


def interrupt_code(iid: int, ack: bool = False) -> dict[str, object]:
    if not 0 <= iid <= 31:
        raise ValueError("IID")
    return {
        "type": 0b10,
        "value": ((1 if ack else 0) << 5) | iid,
        "IID": iid,
        "ack": ack,
    }


def ack_configuration_valid(*, sources: int, acknowledgers: int, mode: InterruptMode) -> bool:
    if mode is InterruptMode.ACK:
        return sources == 1 and acknowledgers == 1
    return sources >= 1


def interrupt_repeat_interval_valid(
    *,
    mode: InterruptMode,
    interval: float,
    worst_interrupt_propagation: float,
    max_ack_generation: float = 0.0,
    worst_ack_propagation: float = 0.0,
) -> bool:
    if mode is InterruptMode.INTERRUPT:
        return interval > worst_interrupt_propagation
    return interval > (
        worst_interrupt_propagation + max_ack_generation + worst_ack_propagation
    )


def ack_generation_delay_valid(
    *,
    delay: float,
    worst_interrupt_propagation: float,
    max_ack_generation: float,
) -> bool:
    return delay > worst_interrupt_propagation and delay < max_ack_generation


@dataclass(frozen=True)
class NetworkServiceEvent:
    primitive: str
    endpoint: str
    payload: object


def send_packet_request(endpoint: str, packet: Packet) -> NetworkServiceEvent:
    return NetworkServiceEvent("SEND_PACKET.request", endpoint, packet)


def receive_packet_indication(endpoint: str, packet: Packet) -> NetworkServiceEvent:
    return NetworkServiceEvent(
        "RECEIVE_PACKET.indication",
        endpoint,
        {"packet": packet, "terminator": packet.end},
    )


def timecode_request(endpoint: str, value: int) -> NetworkServiceEvent:
    return NetworkServiceEvent("TIME-CODE.request", endpoint, timecode_broadcast_code(value))


def timecode_indication(endpoint: str, register: TimeCodeRegister, value: int):
    result = register.receive(value)
    if not result["valid"]:
        return None
    return NetworkServiceEvent("TIME-CODE.indication", endpoint, value)


def interrupt_request(endpoint: str, iid: int) -> NetworkServiceEvent:
    return NetworkServiceEvent("DISTRIBUTED_INTERRUPT.request", endpoint, interrupt_code(iid))


def interrupt_indication(endpoint: str, iid: int) -> NetworkServiceEvent:
    return NetworkServiceEvent("DISTRIBUTED_INTERRUPT.indication", endpoint, iid)


def interrupt_ack_request(endpoint: str, iid: int) -> NetworkServiceEvent:
    return NetworkServiceEvent(
        "DISTRIBUTED_INTERRUPT_ACK.request", endpoint, interrupt_code(iid, ack=True)
    )


def interrupt_ack_indication(endpoint: str, iid: int) -> NetworkServiceEvent:
    return NetworkServiceEvent("DISTRIBUTED_INTERRUPT_ACK.indication", endpoint, iid)


def source_multicast(packet: Packet, endpoints: tuple[str, ...]) -> tuple[NetworkServiceEvent, ...]:
    return tuple(send_packet_request(ep, packet) for ep in endpoints)


@dataclass
class NetworkFeatureProfile:
    packet: bool = True
    time_code: bool = True
    distributed_interrupt: bool = True
    interrupt_modes: tuple[InterruptMode, ...] = (
        InterruptMode.INTERRUPT,
        InterruptMode.ACK,
    )
    endpoint_timecode_register: bool = True
    source_multicast: bool = True
    test_port_loopback: bool = True
