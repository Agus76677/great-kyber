`timescale 1ns/1ps

module reject_sampler_tb;
    localparam integer LANES = 4;
    localparam integer CAND_BITS = 12;
    localparam integer NUM_VECTORS = 80;

    reg clk;
    reg rst_n;
    reg random_valid;
    reg [127:0] random_in;
    reg [15:0] q;
    reg [LANES*CAND_BITS-1:0] cand_bus;
    reg [LANES*CAND_BITS-1:0] urnd_bus;
    reg [LANES*CAND_BITS-1:0] threshold_bus;
    reg [LANES-1:0] mode_select;

    wire [LANES-1:0] acc_bus;
    wire [LANES*CAND_BITS-1:0] sample_tdata;
    wire sample_tvalid;

    integer vec_file;
    integer out_file;
    integer scan_fields;
    integer vec_count;

    reject_sampler_core #(
        .LANES(LANES),
        .CAND_BITS(CAND_BITS),
        .CONST_TIME(1)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .random_valid(random_valid),
        .random_in(random_in),
        .q(q),
        .cand_bus(cand_bus),
        .urnd_bus(urnd_bus),
        .threshold_bus(threshold_bus),
        .mode_select(mode_select),
        .acc_bus(acc_bus),
        .sample_tdata(sample_tdata),
        .sample_tvalid(sample_tvalid)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        rst_n = 0;
        random_valid = 0;
        random_in = 128'd0;
        q = 16'd0;
        cand_bus = {LANES*CAND_BITS{1'b0}};
        urnd_bus = {LANES*CAND_BITS{1'b0}};
        threshold_bus = {LANES*CAND_BITS{1'b0}};
        mode_select = {LANES{1'b0}};
        vec_count = 0;
        #(25);
        rst_n = 1;

        vec_file = $fopen("3.REJECT/test/reject_vectors.txt", "r");
        if (vec_file == 0) begin
            $display("ERROR: could not open vector file");
            $finish;
        end
        out_file = $fopen("3.REJECT/test/hw_output.txt", "w");
        if (out_file == 0) begin
            $display("ERROR: could not open output file");
            $finish;
        end

        // Allow reset to propagate
        @(posedge clk);
        @(posedge clk);

        while (!$feof(vec_file)) begin
            @(posedge clk);
            scan_fields = $fscanf(
                vec_file,
                "%d %h %h %h %h %h %h\n",
                random_valid,
                q,
                cand_bus,
                urnd_bus,
                threshold_bus,
                mode_select,
                random_in
            );
            if (scan_fields != 7) begin
                $display("ERROR: malformed line in vector file at %0d", vec_count);
                $finish;
            end
            vec_count = vec_count + 1;
            #(1);
            $fwrite(out_file,
                    "%0d %0d %h %0d\n",
                    vec_count,
                    acc_bus,
                    sample_tdata,
                    sample_tvalid);
        end

        // allow pipeline to flush
        repeat (5) begin
            @(posedge clk);
            random_valid = 0;
            cand_bus = {LANES*CAND_BITS{1'b0}};
            urnd_bus = {LANES*CAND_BITS{1'b0}};
            threshold_bus = {LANES*CAND_BITS{1'b0}};
            mode_select = {LANES{1'b0}};
            random_in = 128'd0;
            q = 16'd0;
            #(1);
            $fwrite(out_file,
                    "%0d %0d %h %0d\n",
                    vec_count,
                    acc_bus,
                    sample_tdata,
                    sample_tvalid);
        end

        $fclose(vec_file);
        $fclose(out_file);

        #(20);
        $finish;
    end

endmodule
