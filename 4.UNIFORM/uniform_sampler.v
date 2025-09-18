// uniform_sampler.v
// -----------------------------------------------------------------------------
// Uniform sampler with Barrett reduction, lane-level rejection filtering, and
// a three-stage pipeline. The design ingests a wide random word (128-bit by
// default) and produces LANES parallel samples that are uniformly distributed
// in the range [0, q). Barrett reduction avoids costly integer division during
// modular reduction while a per-lane rejection test guarantees uniformity.
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module uniform_sampler #(
    parameter integer LANES        = 8,
    parameter integer CAND_BITS    = 16,
    parameter integer Q_BITS       = 16,
    parameter integer RANDOM_WIDTH = 128,
    parameter integer FLOOR_WIDTH  = CAND_BITS + 1,
    parameter integer BARRETT_WIDTH = CAND_BITS + Q_BITS
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         random_valid,
    input  wire [RANDOM_WIDTH-1:0]      random_in,
    input  wire [Q_BITS-1:0]            q,
    output wire                         random_ready,
    output reg  [LANES*CAND_BITS-1:0]   sampled_vals,
    output reg  [LANES-1:0]             sampled_valid,
    output reg  [LANES-1:0]             retry_mask
);

    localparam integer TOTAL_CAND_BITS = LANES * CAND_BITS;
    localparam integer THRESH_WIDTH    = Q_BITS + FLOOR_WIDTH;
    localparam [CAND_BITS-1:0] CAND_MASK = {CAND_BITS{1'b1}};

    assign random_ready = 1'b1;

    initial begin
        if (TOTAL_CAND_BITS > RANDOM_WIDTH) begin
            $error("uniform_sampler: TOTAL_CAND_BITS must not exceed RANDOM_WIDTH");
        end
    end

    // Stage 0 registers incoming entropy and q
    reg [RANDOM_WIDTH-1:0] random_s0;
    reg [Q_BITS-1:0]       q_s0;
    reg                    valid_s0;

    // Stage 1 computes Barrett reciprocal and rejection helper values
    reg [TOTAL_CAND_BITS-1:0] candidates_s1;
    reg [Q_BITS-1:0]          q_s1;
    reg [BARRETT_WIDTH-1:0]   mu_s1;
    reg [FLOOR_WIDTH-1:0]     floor_s1;
    reg                       valid_s1;

    // Stage 2 holds registered helper values for the reduction stage
    reg [TOTAL_CAND_BITS-1:0] candidates_s2;
    reg [Q_BITS-1:0]          q_s2;
    reg [BARRETT_WIDTH-1:0]   mu_s2;
    reg [FLOOR_WIDTH-1:0]     floor_s2;
    reg                       valid_s2;

    integer lane;

    // ------------------------------------------------------------------
    // Helper functions
    // ------------------------------------------------------------------
    function automatic [BARRETT_WIDTH-1:0] compute_barrett_mu;
        input [Q_BITS-1:0] q_val;
        reg   [BARRETT_WIDTH:0] numerator;
    begin
        if (q_val == {Q_BITS{1'b0}}) begin
            compute_barrett_mu = {BARRETT_WIDTH{1'b0}};
        end else begin
            numerator = {1'b1, {BARRETT_WIDTH{1'b0}}};
            compute_barrett_mu = numerator / q_val;
        end
    end
    endfunction

    function automatic [FLOOR_WIDTH-1:0] compute_floor_factor;
        input [Q_BITS-1:0] q_val;
        reg   [FLOOR_WIDTH:0] numerator;
    begin
        if (q_val == {Q_BITS{1'b0}}) begin
            compute_floor_factor = {FLOOR_WIDTH{1'b0}};
        end else begin
            numerator = {1'b1, {CAND_BITS{1'b0}}};
            compute_floor_factor = numerator / q_val;
        end
    end
    endfunction

    function automatic [CAND_BITS-1:0] barrett_reduce_value;
        input [CAND_BITS-1:0]     value;
        input [BARRETT_WIDTH-1:0] mu_val;
        input [Q_BITS-1:0]        q_val;
        reg   [CAND_BITS+BARRETT_WIDTH-1:0] product;
        reg   [CAND_BITS-1:0]               approx;
        reg   [CAND_BITS+Q_BITS-1:0]        approx_mul;
        reg   [CAND_BITS+Q_BITS-1:0]        value_ext;
        reg   [CAND_BITS+Q_BITS-1:0]        q_ext;
        reg   [CAND_BITS+Q_BITS-1:0]        corrected;
    begin
        if (q_val == {Q_BITS{1'b0}}) begin
            barrett_reduce_value = {CAND_BITS{1'b0}};
        end else begin
            product    = value * mu_val;
            approx     = product >> BARRETT_WIDTH;
            approx_mul = approx * q_val;
            value_ext  = {{Q_BITS{1'b0}}, value};
            q_ext      = {{CAND_BITS{1'b0}}, q_val};
            if (value_ext < approx_mul) begin
                value_ext = value_ext + q_ext;
            end
            corrected = value_ext - approx_mul;
            if (corrected >= q_ext) begin
                corrected = corrected - q_ext;
            end
            barrett_reduce_value = corrected[CAND_BITS-1:0];
        end
    end
    endfunction

    // ------------------------------------------------------------------
    // Pipeline stages
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            random_s0 <= {RANDOM_WIDTH{1'b0}};
            q_s0      <= {Q_BITS{1'b0}};
            valid_s0  <= 1'b0;
        end else if (random_ready) begin
            random_s0 <= random_in;
            q_s0      <= q;
            valid_s0  <= random_valid;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            candidates_s1 <= {TOTAL_CAND_BITS{1'b0}};
            q_s1          <= {Q_BITS{1'b0}};
            mu_s1         <= {BARRETT_WIDTH{1'b0}};
            floor_s1      <= {FLOOR_WIDTH{1'b0}};
            valid_s1      <= 1'b0;
        end else begin
            candidates_s1 <= random_s0[TOTAL_CAND_BITS-1:0];
            q_s1          <= q_s0;
            mu_s1         <= compute_barrett_mu(q_s0);
            floor_s1      <= compute_floor_factor(q_s0);
            valid_s1      <= valid_s0;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            candidates_s2 <= {TOTAL_CAND_BITS{1'b0}};
            q_s2          <= {Q_BITS{1'b0}};
            mu_s2         <= {BARRETT_WIDTH{1'b0}};
            floor_s2      <= {FLOOR_WIDTH{1'b0}};
            valid_s2      <= 1'b0;
        end else begin
            candidates_s2 <= candidates_s1;
            q_s2          <= q_s1;
            mu_s2         <= mu_s1;
            floor_s2      <= floor_s1;
            valid_s2      <= valid_s1;
        end
    end

    reg [LANES*CAND_BITS-1:0] reduced_comb;
    reg [LANES-1:0]           accept_comb;
    reg [LANES-1:0]           retry_comb;
    reg [THRESH_WIDTH-1:0]    threshold_full;
    reg [CAND_BITS-1:0]       candidate_val;
    reg [THRESH_WIDTH-1:0]    candidate_ext;
    reg [CAND_BITS-1:0]       reduced_lane;
    reg [LANES*CAND_BITS-1:0] lane_value;
    reg                       accept_bit;
    reg                       retry_bit;

    always @* begin
        reduced_comb   = {LANES*CAND_BITS{1'b0}};
        accept_comb    = {LANES{1'b0}};
        retry_comb     = {LANES{1'b0}};
        threshold_full = q_s2 * floor_s2;

        for (lane = 0; lane < LANES; lane = lane + 1) begin
            candidate_val = (candidates_s2 >> (lane * CAND_BITS)) & CAND_MASK;
            candidate_ext = {{(THRESH_WIDTH-CAND_BITS){1'b0}}, candidate_val};
            reduced_lane  = barrett_reduce_value(candidate_val, mu_s2, q_s2);
            accept_bit    = 1'b0;
            retry_bit     = 1'b0;

            if (valid_s2 && (q_s2 != {Q_BITS{1'b0}})) begin
                if (floor_s2 != {FLOOR_WIDTH{1'b0}}) begin
                    if (candidate_ext < threshold_full) begin
                        accept_bit = 1'b1;
                    end else begin
                        retry_bit = 1'b1;
                    end
                end else begin
                    retry_bit = 1'b1;
                end
            end

            lane_value = {{(LANES*CAND_BITS-CAND_BITS){1'b0}}, reduced_lane};
            lane_value = lane_value << (lane * CAND_BITS);
            reduced_comb = reduced_comb | lane_value;

            accept_comb[lane] = accept_bit;
            retry_comb[lane]  = retry_bit;
        end

        if (!valid_s2) begin
            reduced_comb = {LANES*CAND_BITS{1'b0}};
            accept_comb = {LANES{1'b0}};
            retry_comb  = {LANES{1'b0}};
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sampled_vals  <= {LANES*CAND_BITS{1'b0}};
            sampled_valid <= {LANES{1'b0}};
            retry_mask    <= {LANES{1'b0}};
        end else begin
            sampled_vals  <= reduced_comb;
            sampled_valid <= accept_comb;
            retry_mask    <= retry_comb;
        end
    end

endmodule
