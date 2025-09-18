// -----------------------------------------------------------------------------
// Module: reject_sampler
// Description: Parameterizable rejection sampling engine with multi-lane
//              parallelism and two-stage pipeline. The module accepts candidate
//              values together with auxiliary uniform random numbers and applies
//              rejection tests based on the selected comparison mode.
//
//              Mode 0 (uniform): candidates are compared against the modulus q
//              (`cand < q`). Accepted candidates are returned on the sample bus.
//              Mode 1 (Bernoulli/LUT): uniform random numbers are compared
//              against the lane-specific threshold embedded in cand_bus
//              (`urnd < cand`). When the test is satisfied the output sample is
//              asserted to one (LSB of each chunk) to represent a Bernoulli
//              success.
//
//              The design uses a two-stage pipeline where stage 0 latches
//              incoming data and stage 1 performs the comparisons. All lanes are
//              processed in parallel to maximise throughput. Optional constant
//              time behaviour can be enabled with CONST_TIME so that the module
//              produces valid strobes at a fixed rate independent of acceptance.
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module reject_sampler #(
    parameter integer LANES = 4,
    parameter integer CAND_BITS = 12,
    parameter integer OUT_BITS = LANES * CAND_BITS,
    parameter integer CONST_TIME = 0
)(
    input  wire                     clk,
    input  wire                     rst,
    input  wire                     random_valid,
    input  wire [127:0]             random_in,
    input  wire [15:0]              q,
    input  wire [LANES*CAND_BITS-1:0] cand_bus,
    input  wire [LANES*CAND_BITS-1:0] urnd_bus,
    input  wire                     mode_select,
    output reg  [LANES-1:0]         acc_bus,
    output reg  [OUT_BITS-1:0]      sample_tdata,
    output reg                      sample_tvalid
);

    // Latch incoming words (stage 0)
    reg [LANES*CAND_BITS-1:0] cand_stage0;
    reg [LANES*CAND_BITS-1:0] urnd_stage0;
    reg                       mode_stage0;
    reg                       stage0_valid;

    // Pipeline stage 1 registers
    reg [LANES*CAND_BITS-1:0] cand_stage1;
    reg [LANES*CAND_BITS-1:0] urnd_stage1;
    reg                       mode_stage1;
    reg                       stage1_valid;

    reg [LANES-1:0]           acc_next;
    reg [OUT_BITS-1:0]        sample_next;

    localparam integer Q_WIDTH  = 16;
    localparam integer PAD_WIDTH = (Q_WIDTH > CAND_BITS) ? (Q_WIDTH - CAND_BITS) : 0;

    integer lane_idx;
    reg [CAND_BITS-1:0] lane_cand;
    reg [CAND_BITS-1:0] lane_urnd;
    reg [15:0]          lane_cand_ext;

    // Prevent synthesis warnings for the entropy input when the module is used
    // with pre-extracted candidates. The bitwise reduction does not affect
    // functionality but ties the signal into the design.
    wire random_in_used = ^random_in;

    // ------------------------------------------------------------------
    // Stage 0 and Stage 1 pipeline registers
    // ------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            cand_stage0   <= {LANES*CAND_BITS{1'b0}};
            urnd_stage0   <= {LANES*CAND_BITS{1'b0}};
            mode_stage0   <= 1'b0;
            stage0_valid  <= 1'b0;
            cand_stage1   <= {LANES*CAND_BITS{1'b0}};
            urnd_stage1   <= {LANES*CAND_BITS{1'b0}};
            mode_stage1   <= 1'b0;
            stage1_valid  <= 1'b0;
        end else begin
            cand_stage0   <= cand_bus;
            urnd_stage0   <= urnd_bus;
            mode_stage0   <= mode_select;
            stage0_valid  <= random_valid;

            cand_stage1   <= cand_stage0;
            urnd_stage1   <= urnd_stage0;
            mode_stage1   <= mode_stage0;
            stage1_valid  <= stage0_valid;
        end
    end

    // ------------------------------------------------------------------
    // Combinational rejection evaluation for stage 1 data
    // ------------------------------------------------------------------
    always @(*) begin
        acc_next    = {LANES{1'b0}};
        sample_next = {OUT_BITS{1'b0}};

        for (lane_idx = 0; lane_idx < LANES; lane_idx = lane_idx + 1) begin
            lane_cand = cand_stage1[lane_idx*CAND_BITS +: CAND_BITS];
            lane_urnd = urnd_stage1[lane_idx*CAND_BITS +: CAND_BITS];

            if (PAD_WIDTH == 0) begin
                lane_cand_ext = lane_cand;
            end else begin
                lane_cand_ext = { {PAD_WIDTH{1'b0}}, lane_cand };
            end

            if (mode_stage1 == 1'b0) begin
                // Uniform sampling mode: accept if candidate < q
                if (lane_cand_ext < q) begin
                    acc_next[lane_idx] = 1'b1;
                    sample_next[lane_idx*CAND_BITS +: CAND_BITS] = lane_cand;
                end
            end else begin
                // Bernoulli/LUT mode: accept if uniform random < threshold
                if (lane_urnd < lane_cand) begin
                    acc_next[lane_idx] = 1'b1;
                    if (CAND_BITS == 1) begin
                        sample_next[lane_idx*CAND_BITS +: CAND_BITS] = {acc_next[lane_idx]};
                    end else begin
                        sample_next[lane_idx*CAND_BITS +: CAND_BITS] =
                            {{(CAND_BITS-1){1'b0}}, acc_next[lane_idx]};
                    end
                end
            end
        end
    end

    // ------------------------------------------------------------------
    // Output registers
    // ------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            acc_bus       <= {LANES{1'b0}};
            sample_tdata  <= {OUT_BITS{1'b0}};
            sample_tvalid <= 1'b0;
        end else begin
            if (stage1_valid) begin
                acc_bus      <= acc_next;
                sample_tdata <= sample_next;
            end else begin
                acc_bus      <= {LANES{1'b0}};
                sample_tdata <= {OUT_BITS{1'b0}};
            end

            if (CONST_TIME != 0) begin
                sample_tvalid <= stage1_valid;
            end else begin
                sample_tvalid <= stage1_valid && (|acc_next);
            end
        end
    end

endmodule
