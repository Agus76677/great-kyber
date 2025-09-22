`timescale 1ns / 1ps

module uniform_sampler_tb;
    localparam integer LANES = 8;
    localparam integer CAND_BITS = 16;
    localparam integer INPUT_WIDTH = LANES * CAND_BITS;
    localparam integer VECTORS = 64;

    reg clk;
    reg rst;
    reg valid_in;
    reg [INPUT_WIDTH-1:0] random_in;
    reg [15:0] q;

    wire valid_out;
    wire [INPUT_WIDTH-1:0] sampled_vals;
    wire [LANES-1:0] accept_mask;

    uniform_sampler #(
        .LANES(LANES),
        .CAND_BITS(CAND_BITS)
    ) dut (
        .clk(clk),
        .rst(rst),
        .valid_in(valid_in),
        .random_in(random_in),
        .q(q),
        .valid_out(valid_out),
        .sampled_vals(sampled_vals),
        .accept_mask(accept_mask)
    );

    reg [INPUT_WIDTH-1:0] rand_mem [0:VECTORS-1];
    reg [INPUT_WIDTH-1:0] exp_mem [0:VECTORS-1];
    reg [15:0]            q_mem   [0:VECTORS-1];
    reg [LANES-1:0]       accept_mem [0:VECTORS-1];

    integer vec_idx;
    integer out_idx;

    initial begin
        $readmemh("4.UNIFORM/test/random_vectors.hex", rand_mem);
        $readmemh("4.UNIFORM/test/expected_samples.hex", exp_mem);
        $readmemh("4.UNIFORM/test/q_values.hex", q_mem);
        $readmemh("4.UNIFORM/test/expected_accept.hex", accept_mem);
    end

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        rst = 1'b1;
        valid_in = 1'b0;
        random_in = {INPUT_WIDTH{1'b0}};
        q = 16'd0;
        vec_idx = 0;
        out_idx = 0;
        repeat (4) @(posedge clk);
        rst = 1'b0;

        @(posedge clk);
        for (vec_idx = 0; vec_idx < VECTORS; vec_idx = vec_idx + 1) begin
            @(negedge clk);
            valid_in <= 1'b1;
            random_in <= rand_mem[vec_idx];
            q <= q_mem[vec_idx];
        end

        @(negedge clk);
        valid_in <= 1'b0;
        random_in <= {INPUT_WIDTH{1'b0}};
        q <= 16'd0;

        repeat (10) @(posedge clk);
        $display("Test completed successfully");
        $finish;
    end

    always @(posedge clk) begin
        if (rst) begin
            out_idx <= 0;
        end else if (valid_out) begin
            if (out_idx >= VECTORS) begin
                $display("[ERROR] Output index exceeded vector count");
                $finish;
            end

            if (sampled_vals !== exp_mem[out_idx]) begin
                $display("[ERROR] Sample mismatch at index %0d", out_idx);
                $display("Expected: %h", exp_mem[out_idx]);
                $display("Got     : %h", sampled_vals);
                $finish;
            end

            if (accept_mask !== accept_mem[out_idx]) begin
                $display("[ERROR] Accept mask mismatch at index %0d", out_idx);
                $display("Expected: %h", accept_mem[out_idx]);
                $display("Got     : %h", accept_mask);
                $finish;
            end

            out_idx <= out_idx + 1;
        end
    end
endmodule
