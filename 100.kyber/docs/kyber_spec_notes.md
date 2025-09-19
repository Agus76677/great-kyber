# Kyber Algorithm Hardwareization Notes

## Scope
This document captures the key algorithmic aspects of the ML-KEM (Kyber) suite that
influence hardware implementation on Xilinx Artix-7 devices.  It serves as the primary
reference for translating the NIST specification to hardware modules inside
`kyber_core`.

## Parameter Sets
| Security Level | k | \u03b7 | du | dv |
| -------------- | - | --- | -- | -- |
| ML-KEM-512     | 2 | 2   | 10 | 4  |
| ML-KEM-768     | 3 | 2   | 10 | 4  |
| ML-KEM-1024    | 4 | 2   | 11 | 5  |

The design must allow run-time selection of the tuple `(k, \u03b7, du, dv)` while fixing the
architectural parallelism (`P`, number of lanes) at synthesis time.  Configuration
registers exposed on the AXI-Lite bus drive all dynamic parameters.

## High-Level Data Flow
1. **Key Generation**
   - Expand seed using SHAKE128 to derive matrix A on-the-fly.
   - Sample noise polynomials using the CBD sampler.
   - Perform NTT on sampled polynomials, multiply with streamed A columns, and compute
     public/private key material.
2. **Encapsulation**
   - Use SHAKE256 for deterministic randomness (coins).
   - Generate ephemeral secrets via CBD, transform to NTT domain, perform matrix
     multiplication and polynomial operations to produce ciphertext.
3. **Decapsulation**
   - Reconstruct shared secret via inverse transforms and re-encryption comparison.
   - Apply confirmation hash following the ML-KEM specification.

## Hardwareization Priorities
- **Throughput**: All streaming datapaths must sustain `II=1` when `ready_in` is
  asserted.  Latency is amortized by deep pipelining.
- **Side-Channel Resistance**: Every conditional subtraction/addition must be constant
  time; selection between branches is implemented via multiplexers controlled by
  masks.
- **Area Control**: Support `P \u2264 4` parallel butterflies for baseline deployment.
  Modules expose generics that allow folding resources for area-optimized builds.

## Compliance References
- [NIST FIPS 203 Draft](https://csrc.nist.gov/projects/pqc-dilithium-kyber).
- Kyber reference implementation (PQClean) for algorithmic validation.
