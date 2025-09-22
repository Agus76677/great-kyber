# Verification Test Plan

## Goals
- Achieve bit-accurate equivalence with golden software models for all parameter sets.
- Demonstrate protocol-level compliance using NIST Known Answer Tests (KATs).
- Collect functional coverage over all FSM transitions and handshake scenarios.

## Verification Levels
### 1. Module Level
| Module Category | Testbench | Golden Model | Coverage Goals |
| --------------- | --------- | ------------ | -------------- |
| SHAKE Core      | `test/shake_tb.v` | `golden/shake_golden.py` | All sponge rounds, back-pressure scenarios. |
| Samplers        | `test/cbd_tb.v`, `test/uniform_tb.v`, `test/reject_tb.v` | `golden/sample_golden.py` | Exhaustive coefficient histogram bins. |
| NTT/INTT        | `test/ntt_tb.v`, `test/intt_tb.v` | `golden/ntt_golden.py` | All stages, lane permutations, reset mid-stream. |
| Poly Operators  | `test/poly_tb.v` | `golden/poly_golden.py` | Add/sub overflow paths, compression/decompression extremes. |
| Matrix Engine   | `test/mat_tb.v` | `golden/mat_golden.py` | Streaming alignment, SHAKE stall recovery. |

### 2. Subsystem Level
- **IND-CPA**: Integrate SHAKE, samplers, NTT, and polynomial arithmetic.
  - Testbench `test/indcpa_tb.v` drives encapsulation/decapsulation sequences.
  - Compare against `golden/kem_golden.py` partial results.

### 3. System Level
- `test/kem_tb.v` executes full ML-KEM flows for k=2,3,4 using seeds from `test/data/`.
- Python harness `scripts/run_kat_verify.py` consumes NIST KAT vectors and checks
  ciphertext and shared-secret equality.

## Automation Flow
1. `scripts/run_module_verify.py`
   - Generates stimulus via golden models.
   - Invokes ModelSim (or Icarus Verilog) for each module testbench.
   - Parses VCD/LOG outputs to ensure pass/fail.
2. `scripts/run_kat_verify.py`
   - Builds behavioral co-simulation harness.
   - Reports throughput, latency, and pass/fail summary.

## Metrics
- **Latency**: Record cycles from `start` to `done` for each operation.
- **Throughput**: Measure sustained rate under continuous request stream.
- **Resource Estimates**: Capture LUT/FF/DSP/BRAM post-synthesis numbers.

## Sign-off Criteria
- All tests pass across three security levels.
- Coverage report indicates >95% toggle and >90% FSM coverage.
- No critical warnings in synthesis/place-and-route runs.
