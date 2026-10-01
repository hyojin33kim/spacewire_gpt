# AGENTS.md — SpaceWire Spec2RTL

## Project objective
Build a traceable SpaceWire Golden Model and FPGA RTL from ECSS-E-ST-50-12C Rev.1.

## Restart point
Before continuing project work, read `traceability/current/CURRENT_HANDOVER.md` and verify the current `main` HEAD.

## Engineering rules
1. Preserve stable requirement IDs.
2. Distinguish SHALL from SHOULD/MAY/CAN/NOTE.
3. Every interpreted behavior must carry source evidence and assumption status.
4. Golden Model must remain implementation-independent.
5. Never silently resolve specification ambiguity.
6. Requirement/contract changes must identify affected model/tests/RTL.
7. Generated artifacts are never the engineering source of truth.
8. RTL Contract is a mandatory gate between validated Golden Model and RTL implementation.
9. RTL must not be coded directly from semantic requirements without a reviewed RTL Contract.
10. Figures/tables/state diagrams are specification evidence, not decoration.
11. Cross-clause dependencies must be explicit before Golden Model implementation.
12. CI PASS is verification evidence, not user/design approval.

## Directory placement policy

Choose a directory by **artifact role and authority**, not merely by subject name.

| Directory | Allowed | Forbidden / move elsewhere |
|---|---|---|
| `spec/` | source manifest, source identity/hash, clause indexing metadata | interpreted requirement, design choice, test result |
| `ontology/` | canonical entity/relation/type vocabulary | behavior contract, RTL timing, evidence |
| `requirements/` | atomic normative requirements and source anchors | architecture choices, interface timing, RTL |
| `contracts/` | implementation-independent behavior, state, ordering, ownership, error semantics | cycle-specific signal protocol, synthesizable code |
| `profiles/` | explicit feature/configuration selections | hidden default assumptions or normative source |
| `golden_model/` | executable reference behavior independent of implementation structure | FPGA primitive/timing assumptions, RTL convenience behavior |
| `rtl_contract/` | clocked interfaces, valid/ready/accept/commit, resource ownership, FIFO/reset/timing boundaries | synthesizable RTL or unreviewed semantic reinterpretation |
| `rtl/` | synthesizable implementation only | tests, reports, design-review prose |
| `verification/` | test vectors, invariants, contract tests, differential tests, SVA, random/fuzz, coverage, FPGA verification | source requirements, implementation source of truth |
| `traceability/` | current handover, decisions/issues, mappings, validation/freeze/review evidence | executable protocol behavior or RTL |
| `tools/` | parsers, lints, generators, audit/coverage automation | protocol implementation |
| `generated/` | disposable/reproducible outputs created by tools | hand-authored decisions, requirements, contracts, golden logic, RTL |
| `.github/` | CI/workflow configuration | engineering artifact content |

## Placement decision procedure

When adding or moving a file, answer these in order:

1. **What is authoritative?** Source evidence, interpreted requirement, semantic behavior, cycle contract, implementation, test, governance record, or generated view?
2. **Can it be regenerated losslessly?** If yes, prefer `generated/`; if no, it belongs with its authoritative source role.
3. **Does it constrain implementation structure?** If no, keep it out of `rtl_contract/` and `rtl/`.
4. **Does it contain approval/rationale/history rather than behavior?** Put it in `traceability/`.
5. **Does one file mix two authorities?** Split it instead of choosing one directory arbitrarily.

## Boundary examples

- ECSS clause text/index → `spec/`
- `SPW-...` atomic SHALL → `requirements/`
- “on error, transition/discard/recover” semantics → `contracts/`
- executable protocol state transition → `golden_model/`
- “accept on valid&&ready; pop on commit” → `rtl_contract/`
- SystemVerilog FIFO/FSM → `rtl/`
- RTL-vs-Golden scenario → `verification/rtl/differential/`
- SVA forbidden-state property → `verification/rtl/assertions/`
- owner-map review/sign-off → `traceability/reviews/`
- requirement-to-test HTML/CSV generated report → `generated/requirement_matrix/`

## Preferred flow
Spec evidence -> ontology -> atomic requirement -> behavior contract -> Golden Model -> RTL contract -> RTL -> verification.

## RTL directory rule
Start coarse: `common/`, `encoding/`, `datalink/`, `network/`, `router/`, `top/`.
Do not add deeper subdirectories until file count or independent ownership makes the split useful.

## Verification directory rule
Use lifecycle/method boundaries: `pre_golden/`, `golden/`, `contracts/`, `rtl/{directed,differential,assertions,random,coverage}/`, `fpga/{timing,cdc,bringup}/`.

## Change discipline
Directory moves must update references, manifests, scripts and CI in the same change. Run Semantic Lint and RTL Contract Verification after structural changes. Do not treat directory cleanup as RTL implementation authorization.
