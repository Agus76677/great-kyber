`timescale 1ns / 1ps

module tb_gauss_sampler;
    localparam integer RANDOM_WIDTH = 128;
    localparam integer PARALLELISM = 4;
    localparam integer GAUSS_MAX_SYMBOLS = 16;
    localparam integer GAUSS_CDF_WIDTH = 16;
    localparam integer VALUE_WIDTH = 13;
    localparam integer NUM_VECTORS = 13;

    localparam integer LANE_WIDTH = RANDOM_WIDTH / PARALLELISM;

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

    reg clk;
    reg rst;
    reg random_valid;
    reg [RANDOM_WIDTH-1:0] random_in;
    reg [7:0] sigma_in;

    wire random_ready;
    wire sample_valid;
    wire [PARALLELISM*VALUE_WIDTH-1:0] coeffs;

    gauss_sampler #(
        .RANDOM_WIDTH(RANDOM_WIDTH),
        .PARALLELISM(PARALLELISM),
        .GAUSS_MAX_SYMBOLS(GAUSS_MAX_SYMBOLS),
        .GAUSS_CDF_WIDTH(GAUSS_CDF_WIDTH),
        .VALUE_WIDTH(VALUE_WIDTH)
    ) dut (
        .clk(clk),
        .rst(rst),
        .random_valid(random_valid),
        .random_ready(random_ready),
        .random_in(random_in),
        .sigma(sigma_in),
        .sample_valid(sample_valid),
        .coeffs(coeffs)
    );

    reg [RANDOM_WIDTH-1:0] random_words [0:NUM_VECTORS-1];
    reg [7:0] sigma_words [0:NUM_VECTORS-1];
    reg expected_valid [0:NUM_VECTORS-1];
    reg [PARALLELISM*VALUE_WIDTH-1:0] expected_coeffs [0:NUM_VECTORS-1];

    `include "../src/gauss_cdf_rom.vh"

    function automatic [PARALLELISM*VALUE_WIDTH:0] compute_expected;
        input [RANDOM_WIDTH-1:0] rand_word;
        input [7:0] sigma_value;
        reg [GAUSS_CDF_WIDTH*GAUSS_MAX_SYMBOLS-1:0] cdf_flat_local;
        reg [GAUSS_CDF_WIDTH-1:0] tail_extend;
        reg [GAUSS_CDF_WIDTH-1:0] threshold [0:GAUSS_MAX_SYMBOLS-1];
        reg [PARALLELISM*VALUE_WIDTH-1:0] samples;
        reg valid;
        integer lane;
        integer symbol;
        reg [7:0] sigma_clamped;
    begin
        sigma_clamped = (sigma_value < 8'd1) ? 8'd1 : (sigma_value > 8'd8 ? 8'd8 : sigma_value);
        cdf_flat_local = gauss_cdf_pack(sigma_clamped);
        tail_extend = gauss_tail_threshold(sigma_clamped);
        for (symbol = 0; symbol < GAUSS_MAX_SYMBOLS; symbol = symbol + 1) begin
            threshold[symbol] = cdf_flat_local[GAUSS_CDF_WIDTH*symbol +: GAUSS_CDF_WIDTH];
        end
        samples = {PARALLELISM*VALUE_WIDTH{1'b0}};
        valid = 1'b1;
        for (lane = 0; lane < PARALLELISM; lane = lane + 1) begin
            reg [LANE_WIDTH-1:0] lane_bits;
            reg [GAUSS_CDF_WIDTH-1:0] uniform_value;
            reg [CAND_WIDTH-1:0] candidate;
            reg lane_tail;
            integer idx;
            lane_bits = rand_word[LANE_WIDTH*lane +: LANE_WIDTH];
            uniform_value = lane_bits[GAUSS_CDF_WIDTH-1:0];
            candidate = {CAND_WIDTH{1'b0}};
            lane_tail = 1'b1;
            for (idx = 0; idx < GAUSS_MAX_SYMBOLS; idx = idx + 1) begin
                if (lane_tail && uniform_value < threshold[idx]) begin
                    candidate = idx;
                    lane_tail = 1'b0;
                end
            end
            if (lane_tail) begin
                if (tail_extend != {GAUSS_CDF_WIDTH{1'b0}} && uniform_value < threshold[GAUSS_MAX_SYMBOLS-1] + tail_extend) begin
                    candidate = GAUSS_MAX_SYMBOLS-1;
                    lane_tail = 1'b0;
                end
            end
            if (lane_tail) begin
                valid = 1'b0;
            end
            begin
                reg [VALUE_WIDTH-1:0] abs_value;
                reg [VALUE_WIDTH-1:0] signed_value;
                reg sign_bit;
                abs_value = {{(VALUE_WIDTH-CAND_WIDTH){1'b0}}, candidate};
                sign_bit = lane_bits[GAUSS_CDF_WIDTH] & (|candidate);
                if (lane_tail) begin
                    signed_value = {VALUE_WIDTH{1'b0}};
                end else if (sign_bit) begin
                    signed_value = (~abs_value) + {{(VALUE_WIDTH-1){1'b0}}, 1'b1};
                end else begin
                    signed_value = abs_value;
                end
                samples[VALUE_WIDTH*lane +: VALUE_WIDTH] = signed_value;
            end
        end
        compute_expected = {valid, samples};
    end
    endfunction

    integer i;
    integer total_expected;

    initial begin
        random_words[0]  = 128'hE3E70682C2094CAC629F6FBED82C07CD;
        random_words[1]  = 128'hF728B4FA42485E3A0A5D2F346BAA9455;
        random_words[2]  = 128'hEB1167B367A9C3787C65C1E582E2E662;
        random_words[3]  = 128'hF7C1BD874DA5E709D4713D60C8A70639;
        random_words[4]  = 128'hE443DF789558867F5BA91FAF7A024204;
        random_words[5]  = 128'h23A7711A8133287637EBDCD9E87A1613;
        random_words[6]  = 128'h1846D424C17C627923C6612F48268673;
        random_words[7]  = 128'hFCBD04C340212EF7CCA5A5A19E4D6E3C;
        random_words[8]  = 128'hB4862B21FB97D43588561712E8E5216A;
        random_words[9]  = 128'h259F4329E6F4590B9A164106CF6A659E;
        random_words[10] = 128'h12E0C8B2BAD640FB19488DEC4F65D4D9;
        random_words[11] = 128'h5487CE1EAF19922AD9B8A714E61A441C;
        random_words[12] = 128'h00018000000000FF0000FF000000FFFF;

        sigma_words[0]  = 8'd4;
        sigma_words[1]  = 8'd4;
        sigma_words[2]  = 8'd4;
        sigma_words[3]  = 8'd4;
        sigma_words[4]  = 8'd4;
        sigma_words[5]  = 8'd4;
        sigma_words[6]  = 8'd7;
        sigma_words[7]  = 8'd7;
        sigma_words[8]  = 8'd7;
        sigma_words[9]  = 8'd7;
        sigma_words[10] = 8'd1;
        sigma_words[11] = 8'd9;
        sigma_words[12] = 8'd4;

        total_expected = 0;
        for (i = 0; i < NUM_VECTORS; i = i + 1) begin
            reg [PARALLELISM*VALUE_WIDTH:0] result;
            result = compute_expected(random_words[i], sigma_words[i]);
            expected_valid[i] = result[PARALLELISM*VALUE_WIDTH];
            expected_coeffs[i] = result[PARALLELISM*VALUE_WIDTH-1:0];
            if (expected_valid[i]) begin
                total_expected = total_expected + 1;
            end
        end
    end

    initial begin
        clk = 1'b0;
        forever #3 clk = ~clk;
    end

    initial begin
        rst = 1'b1;
        random_valid = 1'b0;
        random_in = {RANDOM_WIDTH{1'b0}};
        sigma_in = 8'd4;
        #20;
        rst = 1'b0;
    end

    integer stim_idx;
    initial begin
        stim_idx = 0;
        @(negedge rst);
        @(posedge clk);
        while (stim_idx < NUM_VECTORS) begin
            random_in <= random_words[stim_idx];
            sigma_in <= sigma_words[stim_idx];
            random_valid <= 1'b1;
            @(posedge clk);
            random_valid <= 1'b0;
            stim_idx = stim_idx + 1;
            @(posedge clk);
        end
    end

    integer pointer;
    integer matched_count;
    integer error_flag;

    initial begin
        pointer = 0;
        matched_count = 0;
        error_flag = 0;
        @(negedge rst);
        forever begin
            @(posedge clk);
            if (sample_valid) begin
                integer next_ptr;
                next_ptr = pointer;
                while (next_ptr < NUM_VECTORS && !expected_valid[next_ptr]) begin
                    next_ptr = next_ptr + 1;
                end
                if (next_ptr >= NUM_VECTORS) begin
                    $display("ERROR: received unexpected sample %0h", coeffs);
                    error_flag = 1;
                end else begin
                    if (coeffs !== expected_coeffs[next_ptr]) begin
                        $display("ERROR: mismatch at vector %0d: got %0h expected %0h", next_ptr, coeffs, expected_coeffs[next_ptr]);
                        error_flag = 1;
                    end else begin
                        matched_count = matched_count + 1;
                    end
                    pointer = next_ptr + 1;
                end
            end
        end
    end

    initial begin
        @(negedge rst);
        repeat (200) @(posedge clk);
        if (error_flag) begin
            $display("TEST FAILED: mismatches detected");
            $fatal(1);
        end
        if (matched_count !== total_expected) begin
            $display("TEST FAILED: expected %0d samples, saw %0d", total_expected, matched_count);
            $fatal(1);
        end
        $display("All gauss_sampler tests passed");
        $finish;
    end

endmodule
