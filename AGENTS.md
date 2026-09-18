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
8. Figures/tables/state diagrams are specification evidence, not decoration.
9. Cross-clause dependencies must be explicit before Golden Model implementation.

## Preferred flow
Spec evidence -> ontology -> atomic requirement -> behavior contract -> Golden Model -> tests/invariants -> RTL contract -> RTL.

## Current priority
Build the full understanding baseline from Encoding layer (§5.4) first, then extend the same schema to Data Link (§5.5) and Network/Router (§5.6).
