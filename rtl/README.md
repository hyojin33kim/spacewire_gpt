# RTL

Implementation area for reviewed RTL contracts. RTL changes must preserve the semantic Golden Model as the implementation-independent oracle.

- `common/` — shared packages, FIFO/utilities and reusable primitives
- `encoding/` — character encoding/decoding, parity and Data/Strobe-facing logic
- `datalink/` — link FSM, credit, TX/RX FIFO and recovery
- `network/` — Network-layer endpoint/service adaptation
- `router/` — routing, allocation, Port 0, broadcast and multicast
- `top/` — multi-port integration, reset and system-facing composition

Implementation remains subject to the project RTL authorization gate.
