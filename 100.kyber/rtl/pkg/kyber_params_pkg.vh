// Kyber parameter package
// Defines configurable constants for the ML-KEM hardware accelerator.

`ifndef KYBER_PARAMS_PKG_VH
`define KYBER_PARAMS_PKG_VH

// Base modulus and polynomial degree
`define KYBER_Q                 3329
`define KYBER_N                 256

// Security levels
`define KYBER_K_512             2
`define KYBER_K_768             3
`define KYBER_K_1024            4

// Noise parameter eta per security level
`define KYBER_ETA_512           2
`define KYBER_ETA_768           2
`define KYBER_ETA_1024          2

// Compression parameters
`define KYBER_DU_512            10
`define KYBER_DU_768            10
`define KYBER_DU_1024           11

`define KYBER_DV_512            4
`define KYBER_DV_768            4
`define KYBER_DV_1024           5

// Lane configuration (compile-time)
`define KYBER_MAX_LANES         4

// SHAKE output width in bits per cycle
`define KYBER_SHAKE_WIDTH       128

`endif // KYBER_PARAMS_PKG_VH
