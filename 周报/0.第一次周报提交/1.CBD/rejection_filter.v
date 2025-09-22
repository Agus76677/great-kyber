// -----------------------------------------------------------------------------
// Module: rejection_filter
// Description: Implements a configurable rejection sampling stage. The module
//              calculates a dynamic acceptance limit based on the magnitude of
//              the candidate value. Larger magnitudes have a smaller acceptance
//              window which mimics the typical behaviour of rejection sampling
//              when targeting a centred distribution. The limit computation is
//              parameterised so that the aggressiveness of the filter can be
//              tuned for different operating points.
// -----------------------------------------------------------------------------
module rejection_filter #(
    parameter integer VALUE_WIDTH   = 4,
    parameter integer RAND_WIDTH    = 8,
    parameter integer BASE_LIMIT    = 8'd200,
    parameter integer SHIFT_FACTOR  = 4
) (
    input  wire [VALUE_WIDTH-1:0] magnitude,
    input  wire [RAND_WIDTH-1:0]  random_value,
    output wire                   accept
);

    localparam integer EXT_WIDTH = RAND_WIDTH + SHIFT_FACTOR;

    wire [EXT_WIDTH-1:0] scaled_magnitude;
    wire [EXT_WIDTH-1:0] base_limit_ext;
    wire [EXT_WIDTH-1:0] dynamic_limit_ext;

    assign scaled_magnitude  = {magnitude, {SHIFT_FACTOR{1'b0}}};
    assign base_limit_ext    = {{(EXT_WIDTH-RAND_WIDTH){1'b0}}, BASE_LIMIT[RAND_WIDTH-1:0]};
    assign dynamic_limit_ext = (base_limit_ext > scaled_magnitude) ?
                               (base_limit_ext - scaled_magnitude) :
                               {EXT_WIDTH{1'b0}};

    assign accept = (random_value < dynamic_limit_ext[RAND_WIDTH-1:0]);

endmodule
