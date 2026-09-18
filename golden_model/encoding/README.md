# Encoding Golden Model

Baseline: **semantic-encoding-v0.1**

This package implements observable Encoding-layer semantics from the frozen
baseline. It must remain independent of FPGA microarchitecture.

Included now:
- character/control semantic encoding helpers
- history-dependent parity
- Null / First-Null semantics
- Data-Strobe encode and valid-waveform decode
- gotNull / parity / ESC / disconnect receiver semantics
- signalling-rate constraint helpers

Explicitly excluded until the **RTL Contract**:
- cycle counts and pipelines
- CDC/synchronizers
- exact hardware handshake timing
- counter widths
- exact reset-delay cycle realization
- FPGA-specific mitigation

Validation is in `verification/golden/test_encoding_golden.py` and is derived
from the frozen pre-Golden vectors, not from the model implementation.
