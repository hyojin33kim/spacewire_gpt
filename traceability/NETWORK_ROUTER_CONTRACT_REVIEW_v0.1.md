# Network / Router RTL Contract v0.1 — 초안 검토 및 승인 목록

기준: `eabd632b6e055758c371781fd10610e0c73e8d23` (main 확인).
상태: **Draft / X1~X3 + NR-TECH-01 + NR-DEC-02 설계 closure 반영. Reviewed 아님. RTL 구현 금지.**
순서: Network Contract → Router Contract → 계층 간 통합 리뷰 → 별도 RTL 착수 승인.
기존 Notion의 Data Link RTL 병렬 착수 제안은 사용자의 최신 지시에 따라 보류한다.

## 작성한 것
- Network owner와 Data Link 연결 계약: `rtl_contract/5.6_network_ownership_contract.yaml`
- Router RTL 경계 초안: `rtl_contract/5.6_router_rtl_contract.yaml`
- Network 123개 / Router 101개 요구별 owner 초안: `network_router_owner_map_v0.1.json`
- 아래 승인 묶음과 기술 검증 blocker. 원 Golden/semantic contract와 main은 변경하지 않는다.
- 요구 ID 전수 배분은 구조적 누락 확인이며 구현/검증 완료를 의미하지 않는다.

## 기존 결정 — 재승인하지 않음
FIFO TX/RX 128, credit max 56, Encoding Accept/Commit 분리, Data Link-owned Direct-Drain.
Semantic superset은 path/logical/deletion, logical adaptive, multicast, per-port timeout,
time-code, 32-IID interrupt/ack 및 relay를 포함한다.
이것은 모든 기능의 FPGA 비용이나 RTL 구조가 승인됐다는 뜻이 아니다.
현 초안은 subset을 임의로 선택하지 않고 기존 기능을 유지한다.

## 승인 / 결정 상태
| ID | 권고안 | 대안 / 주요 위험 |
|---|---|---|
| NR-DEC-01 | **CLOSED — 사용자 승인 방향.** 외부 4포트 기본 + 내부 Port 0, 기존 Data Link FIFO 재사용, 회전 순서 기반 packet 중재. 포트 parameter range와 FPGA resource feasibility는 검증 항목. | 2포트 축소는 자원 절약이나 경합 검증 제한. 추가 packet buffer는 면적·ownership 비용. |
| NR-DEC-02 | **DESIGN CLOSED / verification pending.** Per-output timeout은 Router→DataLink abort handshake 사용. DataLink는 link reset 없이 unsent output remainder를 discard하고 synthetic EEP를 정상 credit/Encoding path로 전송. Router는 input tail을 EOP/EEP까지 local drain. Multicast 중 한 output timeout 정책은 NR-TECH-04로 분리. | EEP 단순 append 또는 FIFO enqueue 시 lock release는 packet association/다음 packet 보호를 보장하지 못함. |
| NR-DEC-03 | Port-0 packet service + 문서화된 configuration application/CSR 경계; AXI-only 대체 금지. Broadcast는 승인된 burst/rate envelope에서 무손실 처리하도록 event capture와 per-egress queue 설계 | RMAP 채택은 추가 범위이므로 자동 선택 안 함. 유한 버퍼로 무제한 no-backpressure broadcast를 보장할 수 없음. Traffic envelope/queue 크기와 설정 protocol은 확정 전 승인 항목. |

승인은 위 방향을 고르는 것이며, 아직 정하지 않은 signal timing/용량/시간값을
포괄 승인한 것으로 취급하지 않는다. NR-DEC-03은 실제 broadcast traffic 조건과
configuration application 선택이 확보돼야 닫을 수 있다.

## 기술 검증 blocker — 사용자 승인으로 대체 불가

### NR-TECH-01: FIFO ownership / timeout / packet completion — **DESIGN CLOSED / verification pending**
ECSS §5.6.8.7은 output port가 현재 packet을 다 보내거나 error로 terminate하기 전에는 다른 packet을 전송하지 못하게 하고, 전송이 끝난 뒤 다른 input packet을 받을 수 있게 한다. 따라서 Router packet ownership을 Data Link FIFO capacity와 분리한다.

**결정**
- `net_tx_nchar_ready`: current packet의 N-Char 진행 허가.
- `net_tx_new_packet_ready`: 새 packet 시작 허가.
- Router는 `net_tx_new_packet_ready`일 때만 output을 allocate한다.
- EOP/EEP가 Data Link FIFO에 accept되어도 output lock을 풀지 않는다.
- EOP/EEP가 Encoding에서 commit되어도 output lock을 풀지 않는다.
- matching EOP/EEP가 local serial transmission을 완료했다는 `net_tx_packet_done_valid`에서 정상 output lock을 release한다.
- qualified link error는 current output packet을 terminate하지만, 다음 packet allocation은 `net_tx_new_packet_ready` 재assert까지 금지한다.

**왜 completion feedback을 추가했는가**
`commit`은 serializer가 다음 item으로 irrevocably consume한 boundary이고 wire/local serial completion이 아니다. 따라서 wormhole의 "finished transmission"과 commit을 같은 사건으로 두지 않는다. Encoding→DataLink에 `enc_tx_complete_valid/kind`를 추가해 local transmitter completion을 명시한다.

**효과**
- Data Link FIFO에 다음 Router packet을 미리 쌓지 않는다.
- timeout/abort의 packet association이 "현재 output packet 1개"로 단순해진다.
- v0.1에서는 packet tag가 필요 없다.
- FIFO depth 128은 current packet buffering과 flow-control decoupling에 그대로 사용한다.
### NR-TECH-02: accepted-but-uncommitted terminal의 flush — **CLOSED BY CONTRACT DRAFT**
하위 cross-layer branch `contracts/dl-encoding-cross-layer-v0.1`에서 다음을 고정했다.
- FIFO-backed N-Char는 accept 시 head reserve, commit 시 pop.
- accepted-uncommitted EOP/EEP가 packet-open 상태에서 flush되면 reserved terminator를 정확히 1회 discard하고 spill 종료.
- packet-closed 상태의 accepted-uncommitted N-Char는 reservation 취소 후 FIFO에 보존하여 retry.
- same-edge commit+error는 commit을 먼저 irrevocable accounting하고 post-commit packet state로 Recovery 판단.
- `pending_is_terminator`는 pending kind에서 derive.

이로써 **계약상 hazard는 닫혔으나**, directed boundary test PASS 전에는 전체 Network/Router Reviewed 상태로 올리지 않는다.
Evidence: `traceability/DATALINK_ENCODING_CROSSLAYER_REVIEW_v0.1.md`, branch HEAD `83c424fe7eab6dd1293591930fbb7a9d1f1af923`.

### NR-DEC-02 detail: Port timeout / abort — **DESIGN CLOSED / verification pending**
**Timeout measurement**
- start: first DATA `net_tx_nchar_valid && net_tx_nchar_ready`
- progress: each DATA handshake resets idle counter
- end: EOP/EEP handshake into output port
- expiry: elapsed time is **strictly greater than** configured timeout period
- same-edge DATA or terminal handshake suppresses timeout on that edge
- implementation choice: per-output 32-bit saturating counter at 100 MHz, reset default timeout disabled

**Abort sequence**
1. Latch stuck-packet status.
2. Stop forwarding the affected input packet to the output.
3. Request `net_tx_abort_valid(reason=ROUTER_TIMEOUT)`.
4. Router drains original input tail locally through first EOP/EEP.
5. DataLink resolves/cancels accepted-uncommitted current-packet N-Char, discards unsent buffered remainder, and raises one synthetic EEP.
6. Synthetic EEP consumes normal N-Char credit; credit bypass is forbidden.
7. `net_tx_abort_done` occurs only after the synthetic EEP completes local serial transmission.
8. Router releases output ownership; reuse waits for `net_tx_new_packet_ready`.
9. If a qualified link error occurs before abort completion, link-error recovery supersedes timeout abort and duplicate timeout EEP is forbidden.

**Scope boundary**
This closes unicast/per-output timeout semantics. Multicast member failure interaction remains in NR-TECH-04.
### NR-TECH-03: broadcast simultaneous events / priority / finite capacity
근거: §5.6.3.d, §5.6.4.6–7, §5.6.5.5/.7.
Data Link RX BC는 no-backpressure event이고 TX BC는 한 entry pending register이다.
여러 입력 event는 모두 capture해야 한다. 같은 IID의 interrupt/ack/timer 및 여러 time-code가
같은 cycle에 오면 shared-state 적용 순서가 필요하다.
또한 Data Link에 먼저 accept된 낮은 priority BC는 새 time-code에 선점되지 않는다.
Network priority를 어느 acceptance boundary에서 보장할지 명시 없이 wire priority를 주장하면 안 된다.
- Pass: 선택한 시간순서에 따른 Golden event comparison, duplicate 억제, capture 누락 0,
  승인 load 하 queue overflow 0, priority boundary counterexample 없음.
- 수정은 Golden의 protocol 의미가 아니라 adapter/event ordering에서 시작하되
  의미론 오류가 확인되면 semantic correction 절차로 돌아간다.

### NR-TECH-04: multicast / fair allocation / configuration / cycle schema
- multicast 출력 중 ready 일부만 1일 때 subset handshake가 생기면 안 됨.
  단순한 valid fan-out은 불충분. all-ready 원자 handoff와 stall 안정성을 함께 증명할 것.
- 반복적으로 eligible한 multicast가 unicast에 영구 배제되지 않는지 확인.
  환경이 필요한 출력 집합을 영원히 동시에 비워주지 않으면 bounded progress는 보장 불가.
- route lookup/write collision, snapshot 시점, reset과 table invalidation,
  Port-0 protocol, timeout counter 폭/단위/default, pending EEP/abort 우선순위를 확정.
- 논리주소로 Port 0 접근 금지(§5.6.8.3.f) directed test 필요.
- Encoding/DL payload 이름이 각각 enc_tx_item_data_7_0 / enc_tx_data_7_0이므로
  canonical spelling 또는 explicit adapter mapping을 확정. 단순 이름 수정만으로
  cycle 의미론이 닫혔다고 처리하지 않음.
- Pass: cycle table 및 signal schema 완성, 위 directed boundary 사례 통과.

## 완료 Gate
1. NR-DEC-01 CLOSED. NR-DEC-02 design CLOSED/verification pending. NR-DEC-03의 선택/값/범위가 명시 승인되고 trade-off 기록됨.
2. NR-TECH-01 design CLOSED/verification pending, NR-TECH-02 CLOSED. NR-TECH-03/04의 counterexample과 검증 결과가 첨부됨.
3. 224개 requirement owner row 수작업 검토, N/A/시스템 의무 포함 disposition 완료.
4. 기존 Golden regression 재실행 및 contract 구조 검사 통과.
5. 영향받은 Data Link/Encoding 계약의 cross-reference와 timing 일치 확인.
6. Network/Router review 기록 생성 후 Reviewed 전환. RTL 코딩은 별도 승인.

## 검증 상태
- 이번 작업은 문서/계약 초안 작성이다. RTL·Golden 코드를 수정하거나 실행하지 않았다.
- 저장 전 구조 검증 결과는 이 branch의 delivery 설명에 기록한다.
- 기존 Golden PASS/벡터 mapping과 새 계약 boundary 검증은 별개이다.
