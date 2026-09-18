# Encoding semantic baseline v0.1 — Freeze Gate

A freeze is allowed only when all **hard gates** below are PASS.

## A. Structural integrity — automated

- [ ] All requirement IDs are unique.
- [ ] Every requirement referenced by a contract exists.
- [ ] Every normative §5.2.4 / §5.4 / relevant §6.3 / §6.4 requirement is mapped to a contract or explicitly classified as non-behavioral.
- [ ] Every ontology entity referenced by requirements/contracts exists.
- [ ] Every contract has source requirements and every test vector/invariant has a contract/source path.
- [ ] YAML parses cleanly; no dangling references.

**Method:** repository lint script. Any failure blocks freeze.

## B. Spec fidelity — source-to-artifact review

For each clause and Figure 5-11..5-18, review side-by-side:

1. **Omission:** Did we miss any SHALL, condition, exception, NOTE that changes interpretation?
2. **Over-interpretation:** Did we add behavior the source does not require?
3. **Contradiction:** Does ontology/requirement/contract disagree with another clause, figure or service interface?

Record every finding in `traceability/spec_issues.yaml`. Open high-impact issues block freeze.

## C. Behavioral completeness — pre-Golden vectors

- [ ] Every contract has at least one positive vector.
- [ ] Every error rule has a negative/error-injection vector.
- [ ] Every timing/range rule has boundary vectors.
- [ ] Every persistent state has set/hold/clear vectors.
- [ ] Every interface indication/request has direction and parameter checks.
- [ ] Invariants are written independently of Golden Model code.

## D. Boundary ownership

Every behavior must be classified as exactly one of:

- **Protocol semantic** → Golden Model.
- **RTL contract** → cycle/clock/reset/handshake/counter/pipeline/FIFO realization.
- **Physical/system constraint** → signal integrity/device/mission constraint.
- **Interpretation decision** → explicit decision record.

No behavior may be left as “implementation detail” without an owner.

## E. Independent challenge review

A second review pass should see only:
- source clauses/figures,
- atomic requirements,
- behavior contracts,

and answer:
- What is missing?
- What is asserted without evidence?
- What alternative interpretation would change observable behavior?

The reviewer must not use Golden Model or RTL code as evidence.

## F. Freeze manifest

When A–E PASS:

1. Set reviewed artifacts to `status: frozen`.
2. Create `traceability/freeze_manifest_encoding_v0.1.yaml` with hashes and open non-blocking issues.
3. Git tag: `semantic-encoding-v0.1`.
4. Golden Model must reference this tag/baseline.
5. Later semantic change requires a new baseline version; never edit the meaning of the frozen tag.

## Hard rule after Golden Model

Golden Model validation does **not** authorize direct RTL coding.

Required gate:

`validated Golden Model -> RTL Contract -> RTL implementation -> differential verification`

The RTL Contract is mandatory and must be traceable to both the semantic baseline and Golden Model tests.
