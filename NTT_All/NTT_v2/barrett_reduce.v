// Barrett reduction module for Kyber modulus q=3329
// Performs a single-cycle combinational reduction of a 32-bit input
// into the range [0, q-1].
module barrett_reduce (
    input  wire [31:0] value_in,
    output wire [15:0] value_out
);
    localparam integer Q = 3329;
    localparam integer BARRETT_FACTOR = 20159; // floor((2^26 + q/2) / q)

    wire [47:0] product = value_in * BARRETT_FACTOR;
    wire [31:0] shifted = (product + 48'd33554432) >> 26; // add 2^25 for rounding
    wire [31:0] mul_q   = shifted * Q;
    wire [31:0] diff    = value_in - mul_q;

    wire [31:0] corrected_neg = diff[31] ? diff + Q : diff;
    wire [31:0] corrected     = (corrected_neg >= Q) ? corrected_neg - Q : corrected_neg;

    assign value_out = corrected[15:0];
endmodule
