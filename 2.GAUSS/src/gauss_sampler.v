`timescale 1ns / 1ps

module gauss_sampler #(
    parameter integer RANDOM_WIDTH = 128,
    parameter integer PARALLELISM = 4,
    parameter integer GAUSS_MAX_SYMBOLS = 16,
    parameter integer GAUSS_CDF_WIDTH = 16,
    parameter integer VALUE_WIDTH = 13
)(
    input  wire                          clk,
    input  wire                          rst,
    input  wire                          random_valid,
    output wire                          random_ready,
    input  wire [RANDOM_WIDTH-1:0]       random_in,
    input  wire [7:0]                    sigma,
    output reg                           sample_valid,
    output reg  [PARALLELISM*VALUE_WIDTH-1:0] coeffs
);

    localparam integer LANE_WIDTH = RANDOM_WIDTH / PARALLELISM;

    initial begin
        if (RANDOM_WIDTH % PARALLELISM != 0) begin
            $error("RANDOM_WIDTH must be divisible by PARALLELISM");
        end
        if (LANE_WIDTH < (GAUSS_CDF_WIDTH + 2)) begin
            $error("LANE_WIDTH must provide enough entropy for sampling");
        end
    end

    function integer clog2;
        input integer value;
        integer i;
        begin
            clog2 = 0;
            for (i = value - 1; i > 0; i = i >> 1) begin
                clog2 = clog2 + 1;
            end
        end
    endfunction

    localparam integer CAND_WIDTH = clog2(GAUSS_MAX_SYMBOLS);

    wire [7:0] sigma_sanitized;
    assign sigma_sanitized = (sigma < 8'd1) ? 8'd1 : (sigma > 8'd8 ? 8'd8 : sigma);

    `include "gauss_cdf_rom.vh"

    wire [GAUSS_CDF_WIDTH*GAUSS_MAX_SYMBOLS-1:0] cdf_flat;
    assign cdf_flat = gauss_cdf_pack(sigma_sanitized);

    wire [GAUSS_CDF_WIDTH-1:0] tail_threshold;
    assign tail_threshold = gauss_tail_threshold(sigma_sanitized);

    reg [RANDOM_WIDTH-1:0] random_reg0;
    reg                    stage0_valid;
    reg                    stage1_valid;

    always @(posedge clk) begin
        if (rst) begin
            random_reg0 <= {RANDOM_WIDTH{1'b0}};
            stage0_valid <= 1'b0;
        end else begin
            if (random_valid) begin
                random_reg0 <= random_in;
            end
            stage0_valid <= random_valid;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            stage1_valid <= 1'b0;
        end else begin
            stage1_valid <= stage0_valid;
        end
    end

    assign random_ready = 1'b1;

    reg [PARALLELISM-1:0]                    lane_tail_s1;
    reg [PARALLELISM*CAND_WIDTH-1:0]         lane_value_s1;
    reg [PARALLELISM-1:0]                    lane_sign_s1;

    integer lane_idx;
    integer symbol_idx;

    reg [GAUSS_CDF_WIDTH-1:0] thresholds [0:GAUSS_MAX_SYMBOLS-1];

    always @(*) begin
        for (symbol_idx = 0; symbol_idx < GAUSS_MAX_SYMBOLS; symbol_idx = symbol_idx + 1) begin
            thresholds[symbol_idx] = cdf_flat[GAUSS_CDF_WIDTH*symbol_idx +: GAUSS_CDF_WIDTH];
        end
    end

    reg [PARALLELISM*CAND_WIDTH-1:0] lane_value_s1_next;
    reg [PARALLELISM-1:0] lane_tail_s1_next;
    reg [PARALLELISM-1:0] lane_sign_s1_next;

    always @(*) begin
        lane_value_s1_next = {PARALLELISM*CAND_WIDTH{1'b0}};
        lane_tail_s1_next  = {PARALLELISM{1'b0}};
        lane_sign_s1_next  = {PARALLELISM{1'b0}};
        for (lane_idx = 0; lane_idx < PARALLELISM; lane_idx = lane_idx + 1) begin
            reg [LANE_WIDTH-1:0] lane_bits;
            reg [GAUSS_CDF_WIDTH-1:0] uniform_value;
            reg [CAND_WIDTH-1:0] candidate;
            reg lane_tail;
            integer k;
            lane_bits = random_reg0[LANE_WIDTH*lane_idx +: LANE_WIDTH];
            uniform_value = lane_bits[GAUSS_CDF_WIDTH-1:0];
            lane_sign_s1_next[lane_idx] = lane_bits[GAUSS_CDF_WIDTH];
            candidate = {CAND_WIDTH{1'b0}};
            lane_tail = 1'b1;
            for (k = 0; k < GAUSS_MAX_SYMBOLS; k = k + 1) begin
                if (lane_tail && uniform_value < thresholds[k]) begin
                    candidate = k;
                    lane_tail = 1'b0;
                end
            end
            if (lane_tail) begin
                if (tail_threshold == {GAUSS_CDF_WIDTH{1'b0}}) begin
                    lane_tail = 1'b1;
                end else if (uniform_value < thresholds[GAUSS_MAX_SYMBOLS-1] + tail_threshold) begin
                    candidate = GAUSS_MAX_SYMBOLS-1;
                    lane_tail = 1'b0;
                end
            end
            lane_value_s1_next[ CAND_WIDTH*lane_idx +: CAND_WIDTH ] = candidate;
            lane_tail_s1_next[lane_idx] = lane_tail;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            lane_tail_s1  <= {PARALLELISM{1'b0}};
            lane_value_s1 <= {PARALLELISM*CAND_WIDTH{1'b0}};
            lane_sign_s1  <= {PARALLELISM{1'b0}};
        end else begin
            lane_tail_s1  <= lane_tail_s1_next;
            lane_value_s1 <= lane_value_s1_next;
            lane_sign_s1  <= lane_sign_s1_next;
        end
    end

    reg [PARALLELISM-1:0] lane_valid_s2;
    reg [PARALLELISM*VALUE_WIDTH-1:0] lane_value_s2;
    reg stage2_valid;

    always @(posedge clk) begin
        if (rst) begin
            lane_valid_s2 <= {PARALLELISM{1'b0}};
            lane_value_s2 <= {PARALLELISM*VALUE_WIDTH{1'b0}};
            stage2_valid  <= 1'b0;
        end else begin
            stage2_valid <= stage1_valid;
            for (lane_idx = 0; lane_idx < PARALLELISM; lane_idx = lane_idx + 1) begin
                reg [VALUE_WIDTH-1:0] signed_value;
                reg [VALUE_WIDTH-1:0] abs_value;
                reg sign_bit;
                abs_value = {{(VALUE_WIDTH-CAND_WIDTH){1'b0}}, lane_value_s1[CAND_WIDTH*lane_idx +: CAND_WIDTH]};
                sign_bit  = lane_sign_s1[lane_idx] & (|lane_value_s1[CAND_WIDTH*lane_idx +: CAND_WIDTH]);
                if (lane_tail_s1[lane_idx] || !stage1_valid) begin
                    lane_valid_s2[lane_idx] <= 1'b0;
                    signed_value = {VALUE_WIDTH{1'b0}};
                end else begin
                    lane_valid_s2[lane_idx] <= 1'b1;
                    if (sign_bit) begin
                        signed_value = (~abs_value) + {{(VALUE_WIDTH-1){1'b0}}, 1'b1};
                    end else begin
                        signed_value = abs_value;
                    end
                end
                lane_value_s2[VALUE_WIDTH*lane_idx +: VALUE_WIDTH] <= signed_value;
            end
        end
    end

    reg [PARALLELISM-1:0] lane_valid_s3;
    reg [PARALLELISM*VALUE_WIDTH-1:0] lane_value_s3;

    always @(posedge clk) begin
        if (rst) begin
            lane_valid_s3 <= {PARALLELISM{1'b0}};
            lane_value_s3 <= {PARALLELISM*VALUE_WIDTH{1'b0}};
        end else begin
            lane_valid_s3 <= lane_valid_s2 & {PARALLELISM{stage2_valid}};
            lane_value_s3 <= lane_value_s2;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            coeffs       <= {PARALLELISM*VALUE_WIDTH{1'b0}};
            sample_valid <= 1'b0;
        end else begin
            coeffs       <= lane_value_s3;
            sample_valid <= &lane_valid_s3;
        end
    end

endmodule
