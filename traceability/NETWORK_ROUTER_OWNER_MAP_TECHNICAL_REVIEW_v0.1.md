# Network / Router Owner Map Technical Review v0.1

Date: 2026-09-23  
Branch: `verify/network-router-closure-v0.1`  
Scope: all 224 rows in `traceability/network_router_owner_map_v0.1.json`

## Result

This review is complete as a **technical review candidate**, but it is not a gate approval.

- Total rows examined: **224**
- Approved dispositions already applied: **2**
- No additional owner gap detected: **203**
- Approval-required owner findings: **19**

The existing 224/224 structural allocation check remains PASS. The findings below concern **accountability completeness**, not missing rows.

## Previously approved dispositions

- `SPW-5.6.4.1-a`: Router remains primary; Endpoint added as collaborator.
- `SPW-5.6.7-a`: ConfigurationManagement remains primary; Encoding and Physical added as collaborators.

## Approval-required findings

### A. Shared time-code clauses missing Router collaboration

ECSS 5.6.4.1 explicitly applies time-code support to **nodes and routers**. ECSS 5.6.4.5 explicitly applies validation to an **end-point or routing switch**. The current owner map assigns the following rows to Endpoint/DataLink without Router collaboration:

- `SPW-5.6.4.1-b` — unsupported_timecodes_ignored
- `SPW-5.6.4.2-a` — time_code_value_is_6_bits_0_to_63
- `SPW-5.6.4.3-d` — port_reset_initializes_timecode_register_as_specified
- `SPW-5.6.4.5-a` — compare_received_timecode_to_register
- `SPW-5.6.4.5-b` — valid_if_received_equals_register_plus_one_mod64
- `SPW-5.6.4.5-c` — otherwise_invalid

Candidate disposition for each: retain Endpoint as primary owner and add Router as collaborator.

`SPW-5.6.4.1-b` is inactive in the selected profile because time-code support is enabled; adding Router would be traceability cleanup rather than a new active behavior.

### B. Shared distributed-interrupt clauses missing Router collaboration

ECSS 5.6.5.1 states that distributed interrupts are optionally implemented in **nodes and routers**, and that a **node or routing switch** supporting them operates in one of the defined modes. Clauses 5.6.5.2 and 5.6.5.3 define the interrupt/acknowledgement code semantics used by both node and routing-switch behavior.

Current rows without Router collaboration:

- `SPW-5.6.5.1-a` — distributed_interrupt_optional
- `SPW-5.6.5.1-b` — unsupported_distributed_interrupts_are_ignored
- `SPW-5.6.5.1-c` — interrupt_modes_interrupt_and_interrupt_with_ack
- `SPW-5.6.5.1-d` — supporting_entity_operates_in_one_or_configurable_modes
- `SPW-5.6.5.2-a` — interrupt_code_broadcasts_interrupt
- `SPW-5.6.5.2-b` — IID_bits_0_4_range_0_31
- `SPW-5.6.5.2-c` — interrupt_value_bit5_zero
- `SPW-5.6.5.2-d` — interrupt_code_associated_with_one_of_32_interrupts_by_IID
- `SPW-5.6.5.3-a` — ack_code_returns_interrupt_ack
- `SPW-5.6.5.3-b` — ack_IID_bits_0_4_range_0_31
- `SPW-5.6.5.3-c` — ack_value_bit5_one
- `SPW-5.6.5.3-d` — ack_IID_matches_interrupt_IID

Candidate disposition for each: retain Endpoint as primary owner and add Router as collaborator.

`SPW-5.6.5.1-b` is inactive in the selected full-feature profile; again this is traceability cleanup, not a new implementation behavior.

### C. Router management parameters missing Physical collaboration

- `SPW-RTR-5.6.9-b` — `router_provides_data_link_encoding_and_physical_management_parameters_per_port`

ECSS 5.6.9.b explicitly includes Data Link, Encoding and **Physical** layer management parameters. The current owner map includes Router/DataLink/Encoding but not Physical.

Candidate disposition: retain ConfigurationManagement as primary owner and add Physical collaborator.

## Groups with no additional owner gap detected

The following allocation patterns were reviewed and found internally coherent with the current project boundaries:

- packet + host/service primitives → Endpoint primary, DataLink collaboration, Router collaboration where packet semantics cross routers;
- node-specific time-code and interrupt behavior → Endpoint primary;
- routing, arbitration, timeout, router relay → Router primary;
- configuration/management → ConfigurationManagement primary;
- whole-network constraints and topology → SystemIntegration primary;
- DataLink/Encoding/Physical remain lower-layer source/transport owners rather than invented Network RTL blocks.

## Separate semantic-format debt discovered

The owner review also exposed a pre-existing artifact-format issue: requirement files use non-canonical modality labels even though the project rule is to preserve exact source modalities.

Current non-canonical rows: **53**

- `OPTIONAL_CARDINALITY`: 2
- `SHALL_CONDITIONAL`: 32
- `SHALL_IF_PRESENT`: 2
- `SHALL_IF_SUPPORTED`: 8
- `SHALL_OPTIONAL`: 5
- `SHOULD_CONDITIONAL`: 4

No requirement was changed in this review. See `traceability/NETWORK_ROUTER_MODALITY_AUDIT_v0.1.md`.

## Gate conclusion

The no-approval review work is complete. Before Network/Router can be marked `Reviewed`, approval is still required for:

1. the 19 owner-map candidate collaborator additions above,
2. disposition of the non-canonical modality representation debt,
3. the formal `Reviewed` status transition and merge.
