from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class PacketEnd(str,Enum): EOP="EOP"; EEP="EEP"

@dataclass(frozen=True)
class Packet:
    data: tuple[int,...]
    end: PacketEnd
    def __post_init__(self):
        if any(not 0<=x<=255 for x in self.data): raise ValueError("data character out of range")

def packets_interleaved(stream_packet_ids:list[int]) -> bool:
    closed=set(); current=None
    for pid in stream_packet_ids:
        if pid!=current:
            if pid in closed: return True
            if current is not None: closed.add(current)
            current=pid
    return False

@dataclass
class TimeCodeRegister:
    value:int=0
    def receive(self,received:int):
        if not 0<=received<64: raise ValueError("time-code must be 6-bit")
        valid=received==((self.value+1)&0x3F)
        self.value=received
        return {"valid":valid,"notify_host":valid,"new_register":self.value}

def timecode_broadcast_code(value:int):
    if not 0<=value<64: raise ValueError
    return {"type":0b00,"value":value}

class InterruptMode(str,Enum):
    INTERRUPT="interrupt"; ACK="interrupt_with_acknowledgement"

def interrupt_code(iid:int,ack:bool=False):
    if not 0<=iid<=31: raise ValueError("IID")
    return {"type":0b10,"value":((1 if ack else 0)<<5)|iid,"IID":iid,"ack":ack}

def ack_configuration_valid(*,sources:int,acknowledgers:int,mode:InterruptMode):
    if mode is InterruptMode.ACK: return sources==1 and acknowledgers==1
    return sources>=1

@dataclass
class NetworkFeatureProfile:
    packet:bool=True
    time_code:bool=True
    distributed_interrupt:bool=True
    interrupt_modes:tuple[InterruptMode,...]=(InterruptMode.INTERRUPT,InterruptMode.ACK)
    endpoint_timecode_register:bool=True
    source_multicast:bool=True
