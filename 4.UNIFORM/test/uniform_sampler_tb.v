`timescale 1ns/1ps

module uniform_sampler_tb;
    localparam integer LANES = 8;
    localparam integer CAND_BITS = 16;
    localparam integer Q_BITS = 16;
    localparam integer TOTAL_CYCLES = 70;
    localparam integer LATENCY = 4;
    localparam [CAND_BITS-1:0] CAND_MASK = {CAND_BITS{1'b1}};

    reg clk;
    reg rst_n;
    reg random_valid;
    reg [127:0] random_in;
    reg [Q_BITS-1:0] q;

    wire random_ready;
    wire [LANES*CAND_BITS-1:0] sampled_vals;
    wire [LANES-1:0] sampled_valid;
    wire [LANES-1:0] retry_mask;

    uniform_sampler #(
        .LANES(LANES),
        .CAND_BITS(CAND_BITS),
        .Q_BITS(Q_BITS)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .random_valid(random_valid),
        .random_in(random_in),
        .q(q),
        .random_ready(random_ready),
        .sampled_vals(sampled_vals),
        .sampled_valid(sampled_valid),
        .retry_mask(retry_mask)
    );

    reg [127:0] random_mem [0:TOTAL_CYCLES-1];
    reg [Q_BITS-1:0] q_mem [0:TOTAL_CYCLES-1];
    reg              valid_mem [0:TOTAL_CYCLES-1];
    reg [LANES*CAND_BITS-1:0] expected_vals_mem [0:TOTAL_CYCLES-1];
    reg [LANES-1:0] expected_valid_mem [0:TOTAL_CYCLES-1];
    reg [LANES-1:0] expected_retry_mem [0:TOTAL_CYCLES-1];

    integer check_cycle;
    integer stim_idx;
    integer lane_idx;
    reg [LANES*CAND_BITS-1:0] expected_val;
    reg [LANES-1:0] expected_valid;
    reg [LANES-1:0] expected_retry;
    reg [CAND_BITS-1:0] expected_lane;
    reg [CAND_BITS-1:0] actual_lane;

    initial begin
        $readmemh("4.UNIFORM/test/data/random_in.mem", random_mem);
        $readmemh("4.UNIFORM/test/data/q.mem", q_mem);
        $readmemb("4.UNIFORM/test/data/random_valid.mem", valid_mem);
        $readmemh("4.UNIFORM/test/data/expected_vals.mem", expected_vals_mem);
        $readmemh("4.UNIFORM/test/data/expected_valid.mem", expected_valid_mem);
        $readmemh("4.UNIFORM/test/data/expected_retry.mem", expected_retry_mem);
    end

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        rst_n = 1'b0;
        random_in = 128'd0;
        q = {Q_BITS{1'b0}};
        random_valid = 1'b0;
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
    end

    initial begin
        @(posedge rst_n);
        @(posedge clk);
        for (stim_idx = 0; stim_idx < TOTAL_CYCLES; stim_idx = stim_idx + 1) begin
            random_in = random_mem[stim_idx];
            q = q_mem[stim_idx];
            random_valid = valid_mem[stim_idx];
            @(posedge clk);
        end
        random_valid = 1'b0;
        random_in = 128'd0;
        q = {Q_BITS{1'b0}};
        repeat (LATENCY + 5) @(posedge clk);
        $display("Test completed successfully.");
        $finish;
    end

    always @(negedge clk) begin
        if (!rst_n) begin
            check_cycle <= 0;
        end else begin
            if (check_cycle < TOTAL_CYCLES) begin
                expected_val = expected_vals_mem[check_cycle];
                expected_valid = expected_valid_mem[check_cycle];
                expected_retry = expected_retry_mem[check_cycle];
                if (sampled_valid !== expected_valid) begin
                    $display("[ERROR] sampled_valid mismatch at cycle %0d: got %0h expected %0h", check_cycle, sampled_valid, expected_valid);
                    $finish;
                end
                if (retry_mask !== expected_retry) begin
                    $display("[ERROR] retry_mask mismatch at cycle %0d: got %0h expected %0h", check_cycle, retry_mask, expected_retry);
                    $finish;
                end

                for (lane_idx = 0; lane_idx < LANES; lane_idx = lane_idx + 1) begin
                    if (expected_valid[lane_idx]) begin
                        expected_lane = (expected_val >> (lane_idx * CAND_BITS)) & CAND_MASK;
                        actual_lane = (sampled_vals >> (lane_idx * CAND_BITS)) & CAND_MASK;
                        if (actual_lane !== expected_lane) begin
                            $display("[ERROR] sampled value mismatch at cycle %0d lane %0d: got %0h expected %0h", check_cycle, lane_idx, actual_lane, expected_lane);
                            $finish;
                        end
                    end
                end
            end
            check_cycle <= check_cycle + 1;
        end
    end

endmodule
