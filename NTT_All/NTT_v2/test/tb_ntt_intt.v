`timescale 1ns/1ps

module tb_ntt_intt;
    localparam integer WORDS = 32;
    localparam integer NUM_TESTS = 4;

    reg clk;
    reg rst;

    // NTT interface
    reg        ntt_start;
    reg [127:0] ntt_data_in;
    reg        ntt_valid_in;
    wire       ntt_ready_in;
    wire [127:0] ntt_data_out;
    wire       ntt_valid_out;
    wire       ntt_done;

    // INTT interface
    reg        intt_start;
    reg [127:0] intt_data_in;
    reg        intt_valid_in;
    wire       intt_ready_in;
    wire [127:0] intt_data_out;
    wire       intt_valid_out;
    wire       intt_done;

    // Memories for stimulus and expected results
    reg [127:0] input_vectors   [0:NUM_TESTS*WORDS-1];
    reg [127:0] ntt_expected    [0:NUM_TESTS*WORDS-1];
    reg [127:0] intt_expected   [0:NUM_TESTS*WORDS-1];

    integer i;

    // Instantiate DUTs
    ntt_core dut_ntt (
        .clk(clk),
        .rst(rst),
        .start(ntt_start),
        .data_in(ntt_data_in),
        .valid_in(ntt_valid_in),
        .ready_in(ntt_ready_in),
        .data_out(ntt_data_out),
        .valid_out(ntt_valid_out),
        .done(ntt_done)
    );

    intt_core dut_intt (
        .clk(clk),
        .rst(rst),
        .start(intt_start),
        .data_in(intt_data_in),
        .valid_in(intt_valid_in),
        .ready_in(intt_ready_in),
        .data_out(intt_data_out),
        .valid_out(intt_valid_out),
        .done(intt_done)
    );

    // clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // reset and load vectors
    initial begin
        rst = 1;
        ntt_start = 0;
        ntt_valid_in = 0;
        intt_start = 0;
        intt_valid_in = 0;
        #40;
        rst = 0;
    end

    initial begin
        $readmemh("5.NTT/test/input_poly.hex", input_vectors);
        $readmemh("5.NTT/test/ntt_expected.hex", ntt_expected);
        $readmemh("5.NTT/test/intt_expected.hex", intt_expected);
    end

    task automatic drive_ntt(input integer test_idx);
        integer word_idx;
        begin
            @(posedge clk);
            ntt_start <= 1'b1;
            @(posedge clk);
            ntt_start <= 1'b0;
            word_idx = 0;
            while (word_idx < WORDS) begin
                @(posedge clk);
                if (ntt_ready_in) begin
                    ntt_data_in <= input_vectors[test_idx*WORDS + word_idx];
                    ntt_valid_in <= 1'b1;
                    word_idx = word_idx + 1;
                end else begin
                    ntt_valid_in <= 1'b0;
                end
            end
            @(posedge clk);
            ntt_valid_in <= 1'b0;
        end
    endtask

    task automatic check_ntt(input integer test_idx);
        integer word_idx;
        begin
            word_idx = 0;
            while (word_idx < WORDS) begin
                @(posedge clk);
                if (ntt_valid_out) begin
                    if (ntt_data_out !== ntt_expected[test_idx*WORDS + word_idx]) begin
                        $display("[NTT] mismatch test %0d word %0d: expected %032x got %032x", test_idx, word_idx, ntt_expected[test_idx*WORDS + word_idx], ntt_data_out);
                        $fatal;
                    end
                    word_idx = word_idx + 1;
                end
            end
            wait (ntt_done);
            @(posedge clk);
        end
    endtask

    task automatic drive_intt(input integer test_idx);
        integer word_idx;
        begin
            @(posedge clk);
            intt_start <= 1'b1;
            @(posedge clk);
            intt_start <= 1'b0;
            word_idx = 0;
            while (word_idx < WORDS) begin
                @(posedge clk);
                if (intt_ready_in) begin
                    intt_data_in <= ntt_expected[test_idx*WORDS + word_idx];
                    intt_valid_in <= 1'b1;
                    word_idx = word_idx + 1;
                end else begin
                    intt_valid_in <= 1'b0;
                end
            end
            @(posedge clk);
            intt_valid_in <= 1'b0;
        end
    endtask

    task automatic check_intt(input integer test_idx);
        integer word_idx;
        begin
            word_idx = 0;
            while (word_idx < WORDS) begin
                @(posedge clk);
                if (intt_valid_out) begin
                    if (intt_data_out !== intt_expected[test_idx*WORDS + word_idx]) begin
                        $display("[INTT] mismatch test %0d word %0d: expected %032x got %032x", test_idx, word_idx, intt_expected[test_idx*WORDS + word_idx], intt_data_out);
                        $fatal;
                    end
                    word_idx = word_idx + 1;
                end
            end
            wait (intt_done);
            @(posedge clk);
        end
    endtask

    initial begin
        @(negedge rst);
        for (i = 0; i < NUM_TESTS; i = i + 1) begin
            drive_ntt(i);
            check_ntt(i);
        end

        for (i = 0; i < NUM_TESTS; i = i + 1) begin
            drive_intt(i);
            check_intt(i);
        end

        $display("NTT/INTT test completed successfully");
        $finish;
    end
endmodule
