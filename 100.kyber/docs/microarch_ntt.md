# NTT/INTT Microarchitecture Plan

## Objectives
- Provide a radix-2 decimation-in-time NTT with parameterizable lane count `P` (1, 2, or 4).
- Achieve initiation interval (II) of 1 at 100--200 MHz on Artix-7 by staging arithmetic and memory accesses.
- Support both forward (NTT) and inverse (INTT) transforms with shared datapath.

## Pipeline Overview
1. **Stage 0 -- Twiddle Fetch**
   - Twiddle factors stored in dual-port BRAM (zeta ROM) partitioned per lane.
   - Address generation based on stage index and butterfly offset.
2. **Stage 1 -- Butterfly Multiply**
   - Montgomery multiplication of operand `b` with twiddle `\u03c9`.
   - Pipeline register inserted after DSP output.
3. **Stage 2 -- Butterfly Add/Sub**
   - Compute `a' = a + t`, `b' = a - t` with conditional subtraction by `q`.
   - Barrett reduction applied immediately when results exceed `2q`.
4. **Stage 3 -- Writeback**
   - Results written back to ping-pong banks to avoid read-write hazards.

## Memory Banking Strategy
- Coefficients mapped to `2P` banks enabling simultaneous read of `(a, b)` and writeback of `(a', b')`.
- Address generator emits read addresses two cycles ahead to hide BRAM latency.

## Control FSM
- Stage counter iterates through `log2(N)` levels.
- Within each level, butterfly index increments by `P` per cycle.
- Ready/valid handshake drives acceptance of new start commands while pipeline drains.

## Timing Budget
- DSP multiply and modular reduction targeted within 5 ns at -2 speed grade.
- Register boundaries: after operand fetch, after Montgomery product, after add/sub pair.

## Configurability
- `parameter integer KYBER_N = 256;`
- `parameter integer KYBER_Q = 3329;`
- `parameter integer LANES = 4;`
- `parameter integer DATA_WIDTH = 16;`

## Verification Hooks
- Tap outputs after Stage 2 and Stage 3 for waveform inspection.
- Provide debug mux to stream coefficient pairs through AXI-Stream for offline capture.
