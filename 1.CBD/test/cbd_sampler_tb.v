`timescale 1ns / 1ps

module cbd_sampler_tb;
    localparam integer LANES      = 4;
    localparam integer RAND_WIDTH = 128;
    localparam integer ETA        = 3;
    localparam integer CAND_BITS  = 4;
    localparam integer BERN_WIDTH = 8;
    localparam integer REJ_WIDTH  = 8;

    reg                        clk;
    reg                        reset;
    reg                        start;
    reg                        valid_in;
    reg  [RAND_WIDTH-1:0]      random_in;
    reg  [BERN_WIDTH-1:0]      threshold;
    wire [LANES*CAND_BITS-1:0] sampled_vals;
    wire [LANES-1:0]           accepted_flags;
    wire                       done;

    integer                    input_file;
    integer                    output_file;
    integer                    vector_count;
    integer                    idx;
    integer                    scan_status;
    reg [BERN_WIDTH-1:0]       threshold_word;
    reg [RAND_WIDTH-1:0]       random_word;

    cbd_sampler #(
        .LANES      (LANES),
        .RAND_WIDTH (RAND_WIDTH),
        .ETA        (ETA),
        .CAND_BITS  (CAND_BITS),
        .BERN_WIDTH (BERN_WIDTH),
        .REJ_WIDTH  (REJ_WIDTH)
    ) dut (
        .clk           (clk),
        .reset         (reset),
        .start         (start),
        .valid_in      (valid_in),
        .random_in     (random_in),
        .threshold     (threshold),
        .sampled_vals  (sampled_vals),
        .accepted_flags(accepted_flags),
        .done          (done)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        reset      = 1'b1;
        start      = 1'b0;
        valid_in   = 1'b0;
        threshold  = {BERN_WIDTH{1'b0}};
        random_in  = {RAND_WIDTH{1'b0}};
        #40;
        reset = 1'b0;
    end

    initial begin
        input_file  = $fopen("cbd_input.txt", "r");
        if (input_file == 0) begin
            $fatal(1, "Failed to open cbd_input.txt");
        end
        output_file = $fopen("hw_output.txt", "w");
        if (output_file == 0) begin
            $fatal(1, "Failed to open hw_output.txt");
        end

        scan_status = $fscanf(input_file, "%d\n", vector_count);
        if (scan_status != 1) begin
            $fatal(1, "Failed to read vector count");
        end

        @(negedge reset);
        @(posedge clk);

        for (idx = 0; idx < vector_count; idx = idx + 1) begin
            scan_status = $fscanf(input_file, "%h %h\n", threshold_word, random_word);
            if (scan_status != 2) begin
                $fatal(1, "Failed to read stimulus line %0d", idx);
            end

            threshold <= threshold_word;
            random_in <= random_word;
            start     <= 1'b1;
            valid_in  <= 1'b1;
            @(posedge clk);
            start     <= 1'b0;
            valid_in  <= 1'b0;

            // wait for pipeline to produce an output
            wait_done();
            #1;

            $fwrite(output_file, "%01h %04h\n", accepted_flags, sampled_vals);
            @(posedge clk);
        end

        $fclose(input_file);
        $fclose(output_file);
        #20;
        $finish;
    end

    task wait_done;
        begin
            while (done == 1'b0) begin
                @(posedge clk);
            end
        end
    endtask

endmodule
