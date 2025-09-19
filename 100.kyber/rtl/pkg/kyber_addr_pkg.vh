// Kyber address package
// Provides lookup tables for NTT twiddle indices and AXI register offsets.

`ifndef KYBER_ADDR_PKG_VH
`define KYBER_ADDR_PKG_VH

// AXI-Lite register offsets
`define KYBER_REG_CTRL          12'h000
`define KYBER_REG_STATUS        12'h004
`define KYBER_REG_CFG_SECURITY  12'h008
`define KYBER_REG_CFG_PARALLEL  12'h00C
`define KYBER_REG_SEED_LO       12'h010
`define KYBER_REG_SEED_HI       12'h014
`define KYBER_REG_IRQ_EN        12'h018
`define KYBER_REG_IRQ_STATUS    12'h01C

// Twiddle addressing parameters
`define KYBER_TWIDDLE_DEPTH     256
`define KYBER_TWIDDLE_ADDR_W    8

// Helper macro: compute stage offset base address
`define KYBER_STAGE_OFFSET(stage) ((stage) << 5)

`endif // KYBER_ADDR_PKG_VH
