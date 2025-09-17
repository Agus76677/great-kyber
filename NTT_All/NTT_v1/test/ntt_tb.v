`timescale 1ns/1ps

module ntt_tb;
    reg clk;
    reg reset;
    reg start;
    reg valid_in;
    reg [127:0] data_in;
    wire ready_in;
    wire [127:0] data_out;
    wire valid_out;
    wire done;

    integer i;
    integer out_file;

    reg [127:0] input_buffer [0:31];
    reg [127:0] output_buffer [0:31];
    integer load_idx;
    integer store_idx;

    kyber_ntt dut (
        .clk(clk),
        .reset(reset),
        .start(start),
        .valid_in(valid_in),
        .data_in(data_in),
        .ready_in(ready_in),
        .data_out(data_out),
        .valid_out(valid_out),
        .done(done)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        $readmemh("ntt_input.hex", input_buffer);
        for (i = 0; i < 32; i = i + 1) begin
            output_buffer[i] = 128'd0;
        end
        reset     = 1'b1;
        start     = 1'b0;
        valid_in  = 1'b0;
        data_in   = 128'd0;
        load_idx  = 0;
        store_idx = 0;
        #40;
        reset = 1'b0;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
    end

    always @(posedge clk) begin
        if (reset) begin
            valid_in <= 1'b0;
            load_idx <= 0;
        end else begin
            if (ready_in && load_idx < 32) begin
                data_in  <= input_buffer[load_idx];
                valid_in <= 1'b1;
                load_idx <= load_idx + 1;
            end else begin
                valid_in <= 1'b0;
            end
        end
    end

    always @(posedge clk) begin
        if (valid_out) begin
            output_buffer[store_idx] <= data_out;
            store_idx <= store_idx + 1;
        end
        if (done) begin
            out_file = $fopen("ntt_output_hw.hex", "w");
            for (i = 0; i < 32; i = i + 1) begin
                $fdisplay(out_file, "%032x", output_buffer[i]);
            end
            $fclose(out_file);
            $finish;
        end
    end
endmodule
