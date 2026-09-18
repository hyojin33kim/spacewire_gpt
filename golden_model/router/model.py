from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class RouteEntry:
    ports: tuple[int,...]=()
    valid: bool=False
    delete: bool=False
    adaptive: bool=False
    multicast: bool=False

@dataclass
class RouteDecision:
    outputs: tuple[int,...]=()
    consume_header: bool=False
    discard: bool=False
    wait: bool=False
    invalid_address_error: bool=False

@dataclass
class RouterModel:
    external_ports: tuple[int,...]=(1,2,3,4)
    table: dict[int,RouteEntry]=field(default_factory=dict)
    adaptive_enabled: bool=False
    multicast_enabled: bool=False
    rr_cursor: dict[int,int]=field(default_factory=dict)
    interrupt_active: set[int]=field(default_factory=set)
    timecode_register: int=0

    def reset(self):
        for a in range(32,256): self.table[a]=RouteEntry()
        self.adaptive_enabled=False; self.multicast_enabled=False
        self.interrupt_active.clear()

    def route(self, header:int, *, enabled_ports=None, ready_ports=None, busy_ports=None):
        enabled=set(self.external_ports if enabled_ports is None else enabled_ports)
        ready=set(enabled if ready_ports is None else ready_ports)
        busy=set(() if busy_ports is None else busy_ports)
        existing={0,*self.external_ports}
        if not 0<=header<=255: raise ValueError
        if header<=31:
            if header not in existing:
                return RouteDecision(discard=True,invalid_address_error=True)
            return RouteDecision((header,),consume_header=True)
        if header==255:
            return RouteDecision(discard=True,invalid_address_error=True)
        e=self.table.get(header,RouteEntry())
        if not e.valid or not e.ports or any(p not in existing for p in e.ports):
            return RouteDecision(discard=True,invalid_address_error=True)
        candidates=tuple(p for p in e.ports if p in enabled)
        if e.multicast and self.multicast_enabled:
            if not candidates: return RouteDecision(discard=True)
            if not set(candidates).issubset(ready): return RouteDecision(wait=True)
            return RouteDecision(candidates,consume_header=e.delete)
        if e.adaptive and self.adaptive_enabled:
            free=[p for p in candidates if p not in busy and p in ready]
            if not free: return RouteDecision(wait=True)
            # deterministic trace choice only; compliance requires fairness, not exact winner
            idx=self.rr_cursor.get(header,0)%len(free); p=free[idx]; self.rr_cursor[header]=idx+1
            return RouteDecision((p,),consume_header=e.delete)
        p=e.ports[0]
        if p not in enabled: return RouteDecision(discard=True)
        if p in busy or p not in ready: return RouteDecision(wait=True)
        return RouteDecision((p,),consume_header=e.delete)

    def stuck_packet(self, *, started:bool, ended:bool, idle_time:float, timeout:float, enabled:bool=True):
        stuck=enabled and started and not ended and idle_time>timeout
        return {"stuck":stuck,"discard":stuck,"send_EEP":stuck,"error":stuck}

    def receive_timecode(self, value:int, ingress:int, output_ports=None):
        if not 0<=value<64: raise ValueError
        valid=value==((self.timecode_register+1)&0x3F)
        self.timecode_register=value
        ports=self.external_ports if output_ports is None else tuple(output_ports)
        relay=tuple(p for p in ports if p!=ingress) if valid else ()
        return {"valid":valid,"relay":relay,"new_register":value}

    def receive_interrupt(self, iid:int, ingress:int, output_ports=None):
        if not 0<=iid<=31: raise ValueError
        if iid in self.interrupt_active: return {"relay":(),"active_after":True}
        self.interrupt_active.add(iid)
        ports=self.external_ports if output_ports is None else tuple(output_ports)
        return {"relay":tuple(p for p in ports if p!=ingress),"active_after":True}

    def receive_interrupt_ack(self, iid:int, ingress:int, output_ports=None):
        if iid not in self.interrupt_active: return {"relay":(),"active_after":False}
        self.interrupt_active.remove(iid)
        ports=self.external_ports if output_ports is None else tuple(output_ports)
        return {"relay":tuple(p for p in ports if p!=ingress),"active_after":False}

    def interrupt_timeout(self,iid:int): self.interrupt_active.discard(iid)

class FairRoundRobin:
    def __init__(self): self.last={}
    def choose(self,output:int,contenders:list[int]):
        if not contenders: return None
        ordered=sorted(contenders); last=self.last.get(output,ordered[-1])
        later=[x for x in ordered if x>last]; winner=later[0] if later else ordered[0]
        self.last[output]=winner; return winner
