# AGENTS.md — SpaceWire Spec2RTL

## Project objective
Build a traceable SpaceWire Golden Model and FPGA RTL from ECSS-E-ST-50-12C Rev.1.

## Engineering rules
1. Preserve stable requirement IDs.
2. Distinguish SHALL from SHOULD/MAY/CAN/NOTE.
3. Every interpreted behavior must carry source evidence and assumption status.
4. Golden Model must remain implementation-independent.
5. Never silently resolve specification ambiguity.
6. Requirement/contract changes must identify affected model/tests/RTL.
7. Generated SQLite/HTML is not the source of truth.

## Preferred flow
Spec evidence -> semantic relation -> atomic requirement -> behavior contract -> Golden Model -> tests/invariants -> RTL contract -> RTL.

## Current priority
Pilot the Data Link layer (§5.5), then expand after traceability and validation rules are stable.
