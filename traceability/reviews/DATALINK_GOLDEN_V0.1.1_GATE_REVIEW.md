# Data Link Golden v0.1.1 Corrective Gate Review

Spec baseline: **ECSS-E-ST-50-12C Rev.1 (15 May 2019)**  
Current Data Link semantic baseline: **semantic-datalink-v0.1.1**  
Validated commit: **ae0ae56f43fffd3fcf9744cb6d86ed91d3a11405**

## Why v0.1.1 exists

RTL Contract review found a semantic defect in the previous v0.1 interpretation of §5.5.4.p.
Outstanding receive credit already reserves RX FIFO capacity. Therefore a new FCT is legal only when
physical free entries can cover the outstanding `rx_credit` **plus eight additional N-Chars**, and
the receive-credit counter also has eight-count headroom.

Correct rule:

```text
rx_fifo_free_entries >= rx_credit + 8
AND
rx_credit <= max_credit - 8
```

## Corrective evidence

- Atomic requirements: **140**
- Data Link concrete vectors: **46/46 mapped**
- Data Link invariants: **8**
- Whole-repository Python tests: **34 PASS**
- Golden Model Validation run: **35420999942 — PASS**
- Semantic Lint run: **35420999944 — PASS**
- Semantic Lint: **0 errors / 0 warnings**
- Protocol invariant mapping: **24/24**

## RTL Contract review findings closed

1. FCT issue rule now reserves outstanding receive credit FIFO capacity.
2. Encoding `ready` now means a next-item selection opportunity, preserving BC > FCT > N-Char > Null priority with separate accept/commit.
3. TX FIFO may queue N-Chars before Run; actual Encoding transfer remains Run-gated.
4. Current error flags and latched recovery-cause flags are separate so simultaneous causes are not collapsed.
5. Data Link and Encoding RTL contracts now use one canonical `enc_*` interface naming scheme.
6. Recovery direct-drain liveness is explicitly carried forward to the Network Ownership & Interface Contract.

## Gate result

**PASS — Data Link RTL Contract v0.1 is reviewed.**

The Data Link RTL implementation gate is open. The remaining direct-drain source liveness obligation is an integration-contract item, not a Data Link architecture blocker.
