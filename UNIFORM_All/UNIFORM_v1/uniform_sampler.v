// uniform_sampler.v
// -----------------------------------------------------------------------------
// Uniform sampler with Barrett reduction and lane-level pipelining.
// The module consumes a 128-bit random input bus and produces LANES parallel
// uniform samples in the range [0, q). The design employs a three-stage
// pipeline: input register, reciprocal/threshold preparation, and Barrett
// reduction with acceptance filtering. Barrett reduction avoids costly
// integer division while rejection sampling ensures uniformity.
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module uniform_sampler #(
    parameter integer LANES = 8,
    parameter integer CAND_BITS = 16,
    parameter integer Q_BITS = 16,
    parameter integer BARRETT_WIDTH = CAND_BITS + Q_BITS,
    parameter integer FLOOR_WIDTH = CAND_BITS + 1
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         random_valid,
    input  wire [127:0]                 random_in,
    input  wire [Q_BITS-1:0]            q,
    output wire                         random_ready,
    output reg  [LANES*CAND_BITS-1:0]   sampled_vals,
    output reg  [LANES-1:0]             sampled_valid,
    output reg  [LANES-1:0]             retry_mask
);

    localparam integer TOTAL_CAND_BITS = LANES * CAND_BITS;
    localparam integer EXT_WIDTH       = CAND_BITS + Q_BITS + 1;
    localparam [CAND_BITS-1:0] CAND_MASK = {CAND_BITS{1'b1}};

    assign random_ready = 1'b1;

    initial begin
        if (TOTAL_CAND_BITS > 128) begin
            $error("uniform_sampler: TOTAL_CAND_BITS must not exceed 128 bits");
        end
    end

    // Stage 0 registers input words
    reg [127:0]             random_s0;
    reg [Q_BITS-1:0]        q_s0;
    reg                     valid_s0;

    // Stage 1 prepares Barrett reciprocal and rejection threshold factor
    reg [TOTAL_CAND_BITS-1:0] candidates_s1;
    reg [Q_BITS-1:0]          q_s1;
    reg [BARRETT_WIDTH-1:0]   mu_s1;
    reg [FLOOR_WIDTH-1:0]     floor_s1;
    reg                       valid_s1;

    // Stage 2 registers intermediate values for reduction
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
        reg   [BARRETT_WIDTH:0] remainder;
        reg   [BARRETT_WIDTH-1:0] quotient;
        integer idx;
    begin
        remainder = { (BARRETT_WIDTH+1){1'b0} };
        quotient  = { BARRETT_WIDTH{1'b0} };
        if (q_val == {Q_BITS{1'b0}}) begin
            compute_barrett_mu = {BARRETT_WIDTH{1'b0}};
        end else begin
            for (idx = BARRETT_WIDTH; idx > 0; idx = idx - 1) begin
                remainder = {remainder[BARRETT_WIDTH-1:0], (idx == BARRETT_WIDTH) ? 1'b1 : 1'b0};
                if (remainder >= q_val) begin
                    remainder = remainder - q_val;
                    quotient[idx-1] = 1'b1;
                end else begin
                    quotient[idx-1] = 1'b0;
                end
            end
            compute_barrett_mu = quotient;
        end
    end
    endfunction

    function automatic [FLOOR_WIDTH-1:0] compute_candidate_floor;
        input [Q_BITS-1:0] q_val;
        reg   [FLOOR_WIDTH:0] remainder;
        reg   [FLOOR_WIDTH-1:0] quotient;
        integer idx;
    begin
        remainder = { (FLOOR_WIDTH+1){1'b0} };
        quotient  = { FLOOR_WIDTH{1'b0} };
        if (q_val == {Q_BITS{1'b0}}) begin
            compute_candidate_floor = {FLOOR_WIDTH{1'b0}};
        end else begin
            for (idx = FLOOR_WIDTH; idx > 0; idx = idx - 1) begin
                remainder = {remainder[FLOOR_WIDTH-1:0], (idx == FLOOR_WIDTH) ? 1'b1 : 1'b0};
                if (remainder >= q_val) begin
                    remainder = remainder - q_val;
                    quotient[idx-1] = 1'b1;
                end else begin
                    quotient[idx-1] = 1'b0;
                end
            end
            compute_candidate_floor = quotient;
        end
    end
    endfunction

    function automatic [CAND_BITS-1:0] barrett_reduce_value;
        input [CAND_BITS-1:0]   value;
        input [BARRETT_WIDTH-1:0] mu_val;
        input [Q_BITS-1:0]      q_val;
        reg   [CAND_BITS+BARRETT_WIDTH-1:0] product;
        reg   [CAND_BITS-1:0]               approx;
        reg   [CAND_BITS+Q_BITS-1:0]        approx_mul_narrow;
        reg   [EXT_WIDTH-1:0]               approx_mul_ext;
        reg   [EXT_WIDTH-1:0]               corrected;
        reg   [EXT_WIDTH-1:0]               value_ext;
        reg   [EXT_WIDTH-1:0]               q_ext;
    begin
        product = value * mu_val;
        approx = product >> BARRETT_WIDTH;
        approx_mul_narrow = approx * q_val;
        approx_mul_ext = {1'b0, approx_mul_narrow};
        value_ext = {{(Q_BITS+1){1'b0}}, value};
        q_ext = {{(CAND_BITS+1){1'b0}}, q_val};
        if (value_ext < approx_mul_ext) begin
            value_ext = value_ext + q_ext;
            if (value_ext < approx_mul_ext) begin
                value_ext = value_ext + q_ext;
            end
        end
        corrected = value_ext - approx_mul_ext;
        if (corrected >= q_ext) begin
            corrected = corrected - q_ext;
            if (corrected >= q_ext) begin
                corrected = corrected - q_ext;
            end
        end
        barrett_reduce_value = corrected[CAND_BITS-1:0];
    end
    endfunction

    // ------------------------------------------------------------------
    // Pipeline stages
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            random_s0 <= 128'd0;
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
            floor_s1      <= compute_candidate_floor(q_s0);
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
    reg [Q_BITS+FLOOR_WIDTH-1:0] threshold_full;
    reg [CAND_BITS-1:0]       candidate_val;
    reg [CAND_BITS-1:0]       reduced_lane;
    reg [EXT_WIDTH-1:0]       candidate_ext;
    reg [LANES*CAND_BITS-1:0] lane_value;
    reg                       accept_bit;

    always @* begin
        reduced_comb   = {LANES*CAND_BITS{1'b0}};
        accept_comb    = {LANES{1'b0}};
        retry_comb     = {LANES{1'b0}};
        threshold_full = q_s2 * floor_s2;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            candidate_val = (candidates_s2 >> (lane * CAND_BITS)) & CAND_MASK;
            candidate_ext = {{(Q_BITS+1){1'b0}}, candidate_val};
            reduced_lane  = {CAND_BITS{1'b0}};
            accept_bit    = 1'b0;

            if (valid_s2 && (q_s2 != {Q_BITS{1'b0}})) begin
                if (floor_s2 != {FLOOR_WIDTH{1'b0}}) begin
                    if (candidate_ext < threshold_full) begin
                        accept_bit = 1'b1;
                    end
                end
                reduced_lane = barrett_reduce_value(candidate_val, mu_s2, q_s2);
            end

            lane_value = {{(LANES*CAND_BITS-CAND_BITS){1'b0}}, reduced_lane};
            lane_value = lane_value << (lane * CAND_BITS);
            reduced_comb = reduced_comb | lane_value;
            accept_comb[lane] = valid_s2 ? accept_bit : 1'b0;
            retry_comb[lane]  = valid_s2 ? (~accept_bit) : 1'b0;
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
