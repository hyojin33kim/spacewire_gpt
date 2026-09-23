# RTL Contract Freeze Candidate v0.1

Date: 2026-09-21
Branch: `contracts/network-router-after-dl-closure-v0.1`
Status: **Reviewed / verification passed / RTL not authorized**

## Scope

This freeze candidate closes the currently identified cycle-level design decisions for:
- Encoding §5.4 cross-layer TX ownership/commit/completion
- Data Link §5.5 FIFO reservation, recovery and Router abort support
- Network §5.6 ownership
- Router packet allocation, timeout, Port 0, broadcast and multicast

It does not claim RTL implementation or RTL verification.

## Closed design items

| Item | Design disposition |
|---|---|
| RTL-IF-X1 | Canonical `enc_tx_item_data_7_0`; raw ESC Encoding-internal |
| RTL-IF-X2 | FIFO-backed N-Char accept=reserve; commit=pop/account |
| RTL-IF-X3 | Same-edge commit precedes error cancellation; pending terminal flush preserves next packet |
| NR-DEC-01 | 4 external ports + Port 0; existing Data Link FIFO reuse; rotating packet arbitration |
| NR-TECH-01 | Router output ownership releases on local terminal serial completion, not FIFO enqueue/Encoding commit |
| NR-DEC-02 | Router timeout uses explicit Data Link abort; current unsent remainder discarded; synthetic EEP uses normal credit path |
| NR-TECH-02 | Accepted-but-uncommitted terminal handled by reserved FIFO head and explicit flush resolution |
| NR-DEC-03 | SPCFG-v0.1 Port-0 protocol; explicit return path; atomic route-table commit |
| NR-TECH-03 | Per-port BC capture, deterministic semantic serialization, class queues and TC > ACK > INT acceptance priority |
| NR-TECH-04 | Atomic multicast handoff; frozen selected mask; fail-whole active multicast on member failure; C0/C1/C2/C3 pipeline |

## New supporting contracts

- `rtl_contract/5.6_port0_configuration_rtl_contract.yaml`
- `rtl_contract/5.6_broadcast_multicast_rtl_contract.yaml`

## Port-0 implementation choices

ECSS requires configuration-port access and management visibility/configurability but does not define the application packet format. SPCFG-v0.1 is therefore an implementation choice.

- Path address 0 routes to Port 0 and is deleted before the configuration parser.
- Logical addressing cannot select Port 0.
- Request contains version/opcode/transaction ID/return path/resource/index/register and optional data/mask.
- Routing-table writes use shadow plus COMMIT.
- Same-cycle route lookup sees the pre-edge table; COMMIT is visible to the following lookup.
- No partial packet has side effects.
- Reset dominates same-cycle management writes.

## Broadcast capacity closure

Selected profile:
- 100 MHz core
- maximum operational link rate 200 Mbit/s
- four external ports
- broadcast code = ESC + data character = 14 serial bits

Therefore the same input port cannot deliver two broadcast codes closer than 70 ns = seven core cycles. Four one-entry ingress capture slots plus a semantic engine draining one event per core cycle can drain a four-port simultaneous burst in four cycles before any one input can generate its next broadcast code.

Egress storage is finite and explicit:
- Time-code queue: 4
- Interrupt-ack queue: 32
- Interrupt queue: 32
- priority at Network→DataLink acceptance: Time-code > Ack > Interrupt
- overflow is latched/counted and is never silent
- qualification must demonstrate zero overflow for the approved mission traffic profile

## Multicast fault policy

The standard defines all-output readiness and all-output per-N-Char transfer but does not define the exact mid-packet member-failure policy.

Project choice:
- freeze selected output mask at allocation
- all-or-none N-Char handoff
- timeout/link-error/disable/reset on any selected output fails the whole active multicast packet
- healthy active outputs receive abort/EEP termination
- failed output follows its native error/reset termination
- Router drains original input tail through first EOP/EEP
- group releases only after every selected output ownership terminates
- following packet performs a new enabled-port snapshot

## Exact Router pipeline

- C0: capture/present ingress head
- C1: registered route lookup and route snapshot
- C2: registered allocator grant
- C3: first forwardable N-Char handshake when required outputs are ready
- no same-edge release/regrant
- route/grant snapshot remains stable under stall

## Verification gate result

1. Parse all RTL-contract YAML.
2. Fix known Semantic Lint decision-ID false positive, then obtain clean lint.
3. Run X1-X3 directed boundary tests.
4. Run output ownership / timeout-abort tests.
5. Run Port-0 malformed/atomic-update/collision tests.
6. Prove four-port broadcast capture bound and run priority/overflow tests.
7. Run multicast all-or-none and member-failure tests.
8. Manually disposition Network 123 + Router 101 owner-map rows.
9. Re-run Golden regression and confirm semantic baseline is unchanged.
10. Formal Gate Review accepted on 2026-09-24; Network/Router contracts may transition to Reviewed. RTL authorization remains separate.

## Gate

- Design blockers: **none currently identified**
- Verification blockers: **closed by recorded evidence**
- RTL implementation allowed: **false**

- Formal Gate Review: **ACCEPTED 2026-09-24**
- Main merge: **not yet authorized**
