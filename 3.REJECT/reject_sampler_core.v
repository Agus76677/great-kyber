// SPDX-License-Identifier: MIT
// Module: reject_sampler_core
// Description: Parameterizable rejection sampling core with pipelined accept logic.

`timescale 1ns / 1ps

module reject_sampler_core #(
    parameter integer LANES = 4,
    parameter integer CAND_BITS = 12,
    parameter integer CONST_TIME = 0
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         random_valid,
    input  wire [127:0]                 random_in,
    input  wire [15:0]                  q,
    input  wire [LANES*CAND_BITS-1:0]   cand_bus,
    input  wire [LANES*CAND_BITS-1:0]   urnd_bus,
    input  wire [LANES*CAND_BITS-1:0]   threshold_bus,
    input  wire [LANES-1:0]             mode_select,
    output reg  [LANES-1:0]             acc_bus,
    output reg  [LANES*CAND_BITS-1:0]   sample_tdata,
    output reg                          sample_tvalid
);

    localparam integer LANE_MSB = CAND_BITS - 1;

    // Stage 0 registers hold incoming random data when valid is asserted.
    reg [LANES*CAND_BITS-1:0] cand_stage0;
    reg [LANES*CAND_BITS-1:0] urnd_stage0;
    reg [LANES*CAND_BITS-1:0] threshold_stage0;
    reg [LANES-1:0]           mode_stage0;
    reg [15:0]                q_stage0;
    reg [127:0]               rnd_stage0;

    reg                       random_valid_d0;

    // Stage 1 registers provide operands to the accept logic.
    reg [LANES*CAND_BITS-1:0] cand_stage1;
    reg [LANES*CAND_BITS-1:0] urnd_stage1;
    reg [LANES*CAND_BITS-1:0] threshold_stage1;
    reg [LANES-1:0]           mode_stage1;
    reg [15:0]                q_stage1;
    reg [127:0]               rnd_stage1;

    reg                       random_valid_d1;

    wire [LANES-1:0] uniform_accept;
    wire [LANES-1:0] bernoulli_accept;
    wire [LANES-1:0] combined_accept;

    integer lane_idx;

    // Stage 0 capture
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cand_stage0      <= {LANES*CAND_BITS{1'b0}};
            urnd_stage0      <= {LANES*CAND_BITS{1'b0}};
            threshold_stage0 <= {LANES*CAND_BITS{1'b0}};
            mode_stage0      <= {LANES{1'b0}};
            q_stage0         <= 16'd0;
            rnd_stage0       <= 128'd0;
            random_valid_d0  <= 1'b0;
        end else begin
            if (random_valid) begin
                cand_stage0      <= cand_bus;
                urnd_stage0      <= urnd_bus;
                threshold_stage0 <= threshold_bus;
                mode_stage0      <= mode_select;
                q_stage0         <= q;
                rnd_stage0       <= random_in;
            end
            random_valid_d0 <= random_valid;
        end
    end

    // Stage 1 capture (pipeline register)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cand_stage1      <= {LANES*CAND_BITS{1'b0}};
            urnd_stage1      <= {LANES*CAND_BITS{1'b0}};
            threshold_stage1 <= {LANES*CAND_BITS{1'b0}};
            mode_stage1      <= {LANES{1'b0}};
            q_stage1         <= 16'd0;
            rnd_stage1       <= 128'd0;
            random_valid_d1  <= 1'b0;
        end else begin
            cand_stage1      <= cand_stage0;
            urnd_stage1      <= urnd_stage0;
            threshold_stage1 <= threshold_stage0;
            mode_stage1      <= mode_stage0;
            q_stage1         <= q_stage0;
            rnd_stage1       <= rnd_stage0;
            random_valid_d1  <= random_valid_d0;
        end
    end

    // Uniform accept: candidate less than modulus q
    generate
        genvar gidx;
        for (gidx = 0; gidx < LANES; gidx = gidx + 1) begin : g_uniform
            wire [CAND_BITS-1:0] cand_lane;
            assign cand_lane = cand_stage1[gidx*CAND_BITS + LANE_MSB -: CAND_BITS];
            assign uniform_accept[gidx] = (cand_lane < q_stage1[CAND_BITS-1:0]);
        end
    endgenerate

    // Bernoulli accept: uniform random less than programmable threshold
    generate
        for (gidx = 0; gidx < LANES; gidx = gidx + 1) begin : g_bernoulli
            wire [CAND_BITS-1:0] urnd_lane;
            wire [CAND_BITS-1:0] threshold_lane;
            assign urnd_lane       = urnd_stage1[gidx*CAND_BITS + LANE_MSB -: CAND_BITS];
            assign threshold_lane  = threshold_stage1[gidx*CAND_BITS + LANE_MSB -: CAND_BITS];
            assign bernoulli_accept[gidx] = (urnd_lane < threshold_lane);
        end
    endgenerate

    // Combined accept: choose comparison based on mode select
    generate
        for (gidx = 0; gidx < LANES; gidx = gidx + 1) begin : g_select
            assign combined_accept[gidx] = (mode_stage1[gidx]) ?
                                            bernoulli_accept[gidx] :
                                            uniform_accept[gidx];
        end
    endgenerate

    // Output stage registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_bus       <= {LANES{1'b0}};
            sample_tdata  <= {LANES*CAND_BITS{1'b0}};
            sample_tvalid <= 1'b0;
        end else begin
            for (lane_idx = 0; lane_idx < LANES; lane_idx = lane_idx + 1) begin
                if (combined_accept[lane_idx] && random_valid_d1) begin
                    sample_tdata[lane_idx*CAND_BITS + LANE_MSB -: CAND_BITS]
                        <= cand_stage1[lane_idx*CAND_BITS + LANE_MSB -: CAND_BITS];
                end else begin
                    sample_tdata[lane_idx*CAND_BITS + LANE_MSB -: CAND_BITS]
                        <= {CAND_BITS{1'b0}};
                end
            end
            acc_bus <= combined_accept & {LANES{random_valid_d1}};

            if (CONST_TIME != 0) begin
                sample_tvalid <= random_valid_d1;
            end else begin
                sample_tvalid <= |(combined_accept & {LANES{random_valid_d1}});
            end
        end
    end

endmodule

