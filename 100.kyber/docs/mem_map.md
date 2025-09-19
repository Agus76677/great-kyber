# Memory Map and Buffering Strategy

## On-Chip Storage Budget
- Target BRAM usage: < 40 blocks (36 Kb) for P=4 configuration.
- Dual-port true BRAM preferred for coefficient storage; LUTRAM used for FIFOs and
  register files.

## Global Memory Allocation
| Block                | Size (bits) | Description |
| -------------------- | ----------- | ----------- |
| `ntt_bank[0..7]`     | 256 x 16    | Eight banks holding polynomial coefficients for NTT/INTT.
| `twiddle_rom`        | 256 x 16    | Precomputed twiddle factors (Montgomery form).
| `shake_state`        | 1600        | Keccak state registers per lane.
| `sampler_fifo`       | 256 x 32    | Cross-domain buffer between SHAKE output and sampler cores.
| `axi_cfg_regs`       | 32 x 32     | Memory-mapped control/status registers.

## Address Generation
- **NTT Banks**: Address computed as `bank_sel = (index / stride) mod 2P` and
  `addr = index % stride`.  Ping-pong between even and odd banks for each stage.
- **Twiddle ROM**: Address derived from stage and butterfly number using precomputed
  tables stored in `kyber_addr_pkg.vh`.

## AXI-Lite Map
| Offset | Register           | Width | Description |
| ------ | ------------------ | ----- | ----------- |
| 0x00   | `core_ctrl`        | 32    | Start, reset, enable interrupts. |
| 0x04   | `core_status`      | 32    | Busy flags, error indicators. |
| 0x08   | `cfg_security`     | 32    | Encodes `k`, `du`, `dv`, sampler selects. |
| 0x0C   | `cfg_parallelism`  | 32    | Lane enable mask, sampler throttling. |
| 0x10   | `entropy_seed_lo`  | 32    | Lower bits of SHAKE seed (write-only). |
| 0x14   | `entropy_seed_hi`  | 32    | Upper bits of SHAKE seed (write-only). |
| 0x18   | `irq_enable`       | 32    | Interrupt mask. |
| 0x1C   | `irq_status`       | 32    | Interrupt status (write-1-to-clear). |

## Stream Interfaces
- **Ingress**: AXI-Stream for plaintext/ciphertext data, 128-bit data width, ready/valid.
- **Egress**: AXI-Stream for ciphertext/shared key.  Optional second stream for debug traces.

## DMA Considerations
- Provide outstanding depth of 4 transfers to tolerate AXI back-pressure.
- Burst length limited to 256 beats to simplify address wrap-around logic.
