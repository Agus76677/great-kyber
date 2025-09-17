// -----------------------------------------------------------------------------
// Module: bernoulli_sampler
// Description: Implements Bernoulli sampling by comparing a uniformly distributed
//              random value with a configurable threshold. When the random value
//              is less than the threshold the sampler outputs a positive sign,
//              otherwise a negative sign. The implementation is purely
//              combinational and can be used inside a pipeline stage.
// -----------------------------------------------------------------------------
module bernoulli_sampler #(
    parameter integer COMP_WIDTH = 8
) (
    input  wire [COMP_WIDTH-1:0] random_value,
    input  wire [COMP_WIDTH-1:0] threshold,
    output wire                  sign_is_positive
);

    assign sign_is_positive = (random_value < threshold);

endmodule
