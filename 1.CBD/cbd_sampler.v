// -----------------------------------------------------------------------------
// Module: cbd_sampler
// Description: Top-level CBD sampler with configurable parallel lanes. The
//              module accepts a stream of random bits and produces coefficients
//              that follow the centred binomial distribution. Each lane operates
//              on an independent slice of the random input enabling both
//              parallelism and pipelining. The sampler exposes a simple start / 
//              done handshake to integrate with external control logic.
// -----------------------------------------------------------------------------
module cbd_sampler #(
    parameter integer LANES          = 4,
    parameter integer RAND_WIDTH     = 128,
    parameter integer ETA            = 3,
    parameter integer CAND_BITS      = 4,
    parameter integer BERN_WIDTH     = 8,
    parameter integer REJ_WIDTH      = 8
) (
    input  wire                         clk,
    input  wire                         reset,
    input  wire                         start,
    input  wire                         valid_in,
    input  wire [RAND_WIDTH-1:0]        random_in,
    input  wire [BERN_WIDTH-1:0]        threshold,
    output wire [LANES*CAND_BITS-1:0]   sampled_vals,
    output wire [LANES-1:0]             accepted_flags,
    output wire                         done
);

    localparam integer LANE_WIDTH = RAND_WIDTH / LANES;

    initial begin
        if ((LANE_WIDTH * LANES) != RAND_WIDTH) begin
            $error("RAND_WIDTH must be an integer multiple of LANES");
        end
    end

    reg [RAND_WIDTH-1:0] random_reg;
    reg                  stage0_valid;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            random_reg   <= {RAND_WIDTH{1'b0}};
            stage0_valid <= 1'b0;
        end else begin
            if (start && valid_in) begin
                random_reg   <= random_in;
                stage0_valid <= 1'b1;
            end else begin
                stage0_valid <= 1'b0;
            end
        end
    end

    wire [LANES-1:0] lane_valid;
    wire [LANES-1:0] lane_accept;
    wire [LANES*CAND_BITS-1:0] lane_samples;

    genvar lane_idx;
    generate
        for (lane_idx = 0; lane_idx < LANES; lane_idx = lane_idx + 1) begin : g_lanes
            localparam integer LO = lane_idx * LANE_WIDTH;
            localparam integer HI = LO + LANE_WIDTH - 1;

            cbd_lane #(
                .ETA        (ETA),
                .LANE_WIDTH (LANE_WIDTH),
                .CAND_BITS  (CAND_BITS),
                .BERN_WIDTH (BERN_WIDTH),
                .REJ_WIDTH  (REJ_WIDTH)
            ) u_lane (
                .clk         (clk),
                .reset       (reset),
                .valid_in    (stage0_valid),
                .lane_random (random_reg[HI:LO]),
                .threshold   (threshold),
                .sample_out  (lane_samples[lane_idx*CAND_BITS +: CAND_BITS]),
                .accept_out  (lane_accept[lane_idx]),
                .valid_out   (lane_valid[lane_idx])
            );
        end
    endgenerate

    assign sampled_vals   = lane_samples;
    assign accepted_flags = lane_accept;
    assign done           = &lane_valid;

endmodule
