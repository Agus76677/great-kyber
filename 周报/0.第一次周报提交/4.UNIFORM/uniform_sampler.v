`timescale 1ns / 1ps

// -----------------------------------------------------------------------------
// Module: uniform_sampler
// Description: Pipelined uniform sampler using Barrett reduction. The module
//              receives a wide random input vector and produces multiple samples
//              in parallel lanes. Each sample is reduced modulo q with a
//              Barrett divider to avoid expensive divisions in the datapath.
//              The module exposes a per-lane acceptance mask so the caller can
//              retry rejected candidates when using rejection sampling.
// -----------------------------------------------------------------------------
module uniform_sampler #(
    parameter integer LANES = 8,
    parameter integer CAND_BITS = 16
) (
    input  wire                         clk,
    input  wire                         rst,
    input  wire                         valid_in,
    input  wire [LANES*CAND_BITS-1:0]   random_in,
    input  wire [15:0]                  q,
    output reg                          valid_out,
    output reg  [LANES*CAND_BITS-1:0]   sampled_vals,
    output reg  [LANES-1:0]             accept_mask
);

    localparam integer SHIFT = 2 * CAND_BITS;
    localparam integer PROD_WIDTH = CAND_BITS + SHIFT + 1;
    localparam [SHIFT:0] BARRETT_BASE = {1'b1, {SHIFT{1'b0}}};
    localparam [CAND_BITS:0] CAND_BASE = {1'b1, {CAND_BITS{1'b0}}};

    // ------------------------------------------------------------------
    // Helper functions for Barrett coefficient and acceptance limit.
    // ------------------------------------------------------------------
    function automatic [SHIFT:0] compute_barrett_coeff;
        input [15:0] q_value;
        begin
            if (q_value == 0) begin
                compute_barrett_coeff = 0;
            end else begin
                compute_barrett_coeff = (BARRETT_BASE + q_value - 1) / q_value;
            end
        end
    endfunction

    function automatic [CAND_BITS-1:0] compute_limit;
        input [15:0] q_value;
        reg [CAND_BITS:0] bucket;
        reg [CAND_BITS:0] bucket_minus_one;
        begin
            if (q_value == 0) begin
                compute_limit = {CAND_BITS{1'b0}};
            end else begin
                bucket = (CAND_BASE / q_value) * q_value;
                if (bucket == 0) begin
                    compute_limit = {CAND_BITS{1'b0}};
                end else begin
                    bucket_minus_one = bucket - 1'b1;
                    compute_limit = bucket_minus_one[CAND_BITS-1:0];
                end
            end
        end
    endfunction

    // ------------------------------------------------------------------
    // Stage 0: Input register stage.
    // ------------------------------------------------------------------
    reg                         valid_stage0;
    reg [LANES*CAND_BITS-1:0]   random_stage0;
    reg [15:0]                  q_stage0;
    reg [SHIFT:0]               q_inv_stage0;
    reg [CAND_BITS-1:0]         limit_stage0;

    wire [SHIFT:0] q_inv_comb = compute_barrett_coeff(q);
    wire [CAND_BITS-1:0] limit_comb = compute_limit(q);

    always @(posedge clk) begin
        if (rst) begin
            valid_stage0   <= 1'b0;
            random_stage0  <= {LANES*CAND_BITS{1'b0}};
            q_stage0       <= 16'd0;
            q_inv_stage0   <= {SHIFT+1{1'b0}};
            limit_stage0   <= {CAND_BITS{1'b0}};
        end else begin
            valid_stage0   <= valid_in;
            random_stage0  <= random_in;
            q_stage0       <= q;
            q_inv_stage0   <= q_inv_comb;
            limit_stage0   <= limit_comb;
        end
    end

    // ------------------------------------------------------------------
    // Stage 1: Register candidates and share parameters.
    // ------------------------------------------------------------------
    reg                         valid_stage1;
    reg [LANES*CAND_BITS-1:0]   candidate_stage1;
    reg [15:0]                  q_stage1;
    reg [SHIFT:0]               q_inv_stage1;
    reg [CAND_BITS-1:0]         limit_stage1;

    integer lane_idx1;
    always @(posedge clk) begin
        if (rst) begin
            valid_stage1      <= 1'b0;
            candidate_stage1  <= {LANES*CAND_BITS{1'b0}};
            q_stage1          <= 16'd0;
            q_inv_stage1      <= {SHIFT+1{1'b0}};
            limit_stage1      <= {CAND_BITS{1'b0}};
        end else begin
            valid_stage1      <= valid_stage0;
            q_stage1          <= q_stage0;
            q_inv_stage1      <= q_inv_stage0;
            limit_stage1      <= limit_stage0;
            for (lane_idx1 = 0; lane_idx1 < LANES; lane_idx1 = lane_idx1 + 1) begin
                candidate_stage1[(lane_idx1+1)*CAND_BITS-1 -: CAND_BITS] <=
                    random_stage0[(lane_idx1+1)*CAND_BITS-1 -: CAND_BITS];
            end
        end
    end

    // ------------------------------------------------------------------
    // Stage 2: Multiply candidate with Barrett coefficient.
    // ------------------------------------------------------------------
    reg                         valid_stage2;
    reg [LANES*CAND_BITS-1:0]   candidate_stage2;
    reg [LANES*PROD_WIDTH-1:0]  product_stage2;
    reg [15:0]                  q_stage2;
    reg [CAND_BITS-1:0]         limit_stage2;

    integer lane_idx2;
    always @(posedge clk) begin
        if (rst) begin
            valid_stage2     <= 1'b0;
            candidate_stage2 <= {LANES*CAND_BITS{1'b0}};
            product_stage2   <= {LANES*PROD_WIDTH{1'b0}};
            q_stage2         <= 16'd0;
            limit_stage2     <= {CAND_BITS{1'b0}};
        end else begin
            valid_stage2     <= valid_stage1;
            candidate_stage2 <= candidate_stage1;
            q_stage2         <= q_stage1;
            limit_stage2     <= limit_stage1;
            for (lane_idx2 = 0; lane_idx2 < LANES; lane_idx2 = lane_idx2 + 1) begin
                product_stage2[(lane_idx2+1)*PROD_WIDTH-1 -: PROD_WIDTH] <=
                    candidate_stage1[(lane_idx2+1)*CAND_BITS-1 -: CAND_BITS] * q_inv_stage1;
            end
        end
    end

    // ------------------------------------------------------------------
    // Stage 3: Barrett reduction and acceptance decision.
    // ------------------------------------------------------------------
    reg [LANES*CAND_BITS-1:0] sampled_calc;
    reg [LANES-1:0]           accept_calc;

    integer lane_idx3;
    reg [PROD_WIDTH-1:0] prod_value;
    reg [CAND_BITS:0] quotient_value;
    reg [CAND_BITS+15:0] qmul_value;
    reg [CAND_BITS+15:0] residue_value;
    reg [CAND_BITS+15:0] q_extended;

    always @* begin
        sampled_calc = {LANES*CAND_BITS{1'b0}};
        accept_calc  = {LANES{1'b0}};

        for (lane_idx3 = 0; lane_idx3 < LANES; lane_idx3 = lane_idx3 + 1) begin
            prod_value     = product_stage2[(lane_idx3+1)*PROD_WIDTH-1 -: PROD_WIDTH];
            quotient_value = prod_value >> SHIFT;
            qmul_value     = quotient_value * q_stage2;
            residue_value  = { {16{1'b0}}, candidate_stage2[(lane_idx3+1)*CAND_BITS-1 -: CAND_BITS] };
            q_extended     = { {CAND_BITS{1'b0}}, q_stage2 };

            if (residue_value >= qmul_value) begin
                residue_value = residue_value - qmul_value;
            end else begin
                residue_value = residue_value + q_extended - qmul_value;
            end

            if (residue_value >= q_extended) begin
                residue_value = residue_value - q_extended;
            end

            sampled_calc[(lane_idx3+1)*CAND_BITS-1 -: CAND_BITS] = residue_value[CAND_BITS-1:0];

            if (candidate_stage2[(lane_idx3+1)*CAND_BITS-1 -: CAND_BITS] <= limit_stage2) begin
                accept_calc[lane_idx3] = 1'b1;
            end
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            sampled_vals <= {LANES*CAND_BITS{1'b0}};
            accept_mask  <= {LANES{1'b0}};
            valid_out    <= 1'b0;
        end else begin
            sampled_vals <= sampled_calc;
            accept_mask  <= accept_calc;
            valid_out    <= valid_stage2;
        end
    end

endmodule
