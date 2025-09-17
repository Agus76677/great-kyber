`timescale 1ns/1ps

module tb_reject_sampler;
    localparam integer LANES      = 4;
    localparam integer CAND_BITS  = 12;
    localparam integer OUT_BITS   = LANES * CAND_BITS;
    localparam integer NUM_VECTORS = 64;

    reg clk;
    reg rst;
    reg random_valid;
    reg [127:0] random_in;
    reg [LANES*CAND_BITS-1:0] cand_bus;
    reg [LANES*CAND_BITS-1:0] urnd_bus;
    reg mode_select;
    wire [LANES-1:0] acc_bus;
    wire [OUT_BITS-1:0] sample_tdata;
    wire sample_tvalid;

    // Test vectors
    reg [LANES*CAND_BITS-1:0] cand_mem [0:NUM_VECTORS-1];
    reg [LANES*CAND_BITS-1:0] urnd_mem [0:NUM_VECTORS-1];
    reg [0:0] mode_mem [0:NUM_VECTORS-1];

    integer vec_idx;
    integer output_fd;

    reject_sampler #(
        .LANES(LANES),
        .CAND_BITS(CAND_BITS),
        .OUT_BITS(OUT_BITS),
        .CONST_TIME(0)
    ) dut (
        .clk(clk),
        .rst(rst),
        .random_valid(random_valid),
        .random_in(random_in),
        .q(16'd3329),
        .cand_bus(cand_bus),
        .urnd_bus(urnd_bus),
        .mode_select(mode_select),
        .acc_bus(acc_bus),
        .sample_tdata(sample_tdata),
        .sample_tvalid(sample_tvalid)
    );

    // Clock generation
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        $readmemh("3.REJECT/test/cand.mem", cand_mem);
        $readmemh("3.REJECT/test/urnd.mem", urnd_mem);
        $readmemh("3.REJECT/test/mode.mem", mode_mem);
    end

    initial begin
        output_fd = $fopen("3.REJECT/test/rtl_output.txt", "w");
        if (output_fd == 0) begin
            $display("Failed to open rtl_output.txt");
            $finish;
        end
    end

    integer cycle_count;

    initial begin
        rst = 1'b1;
        random_valid = 1'b0;
        random_in = 128'd0;
        cand_bus = {OUT_BITS{1'b0}};
        urnd_bus = {OUT_BITS{1'b0}};
        mode_select = 1'b0;
        cycle_count = 0;

        repeat (4) @(posedge clk);
        rst = 1'b0;

        for (vec_idx = 0; vec_idx < NUM_VECTORS; vec_idx = vec_idx + 1) begin
            random_valid <= 1'b1;
            cand_bus <= cand_mem[vec_idx];
            urnd_bus <= urnd_mem[vec_idx];
            mode_select <= mode_mem[vec_idx][0];
            random_in <= {cand_mem[vec_idx], urnd_mem[vec_idx]};
            @(posedge clk);
        end

        random_valid <= 1'b0;
        cand_bus <= {OUT_BITS{1'b0}};
        urnd_bus <= {OUT_BITS{1'b0}};
        mode_select <= 1'b0;
        random_in <= 128'd0;

        repeat (4) @(posedge clk);
        $fclose(output_fd);
        $finish;
    end

    always @(posedge clk) begin
        if (rst) begin
            cycle_count <= 0;
        end else begin
            cycle_count <= cycle_count + 1;
        end

        #1;
        $fwrite(output_fd, "%0d %0h %0h\n", sample_tvalid, acc_bus, sample_tdata);
    end

endmodule
