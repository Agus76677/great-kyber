# Kyber Hardware Accelerator Project Skeleton

This repository tree defines the structure and initial planning artifacts for a
fully parameterizable ML-KEM (Kyber) accelerator targeting Xilinx Artix-7 devices.

## Highlights
- Comprehensive documentation of algorithm, microarchitecture, memory maps, and
  interface requirements under `docs/`.
- Golden reference models in Python for SHAKE-driven sampling, NTT/INTT, polynomial
  arithmetic, and full Kyber flows in `golden/`.
- Automation scripts for module-level and system-level verification under `scripts/`.
- Placeholder directories for Verilog RTL, testbenches, constraints, and simulation
  collateral, aligned with the long-term implementation plan.

## Next Steps
1. Flesh out SHAKE core datapath and verification collateral.
2. Implement sampler suite (CBD, uniform, rejection) with matching Python models.
3. Develop NTT/INTT engine using the microarchitecture guidance in `docs/`.
4. Integrate modules into `kyber_core` and execute NIST KAT compliance tests.
