`timescale 1ns/1ps

module shake_core_tb;
    reg clk;
    reg reset;
    reg start;
    reg valid_in;
    reg [127:0] data_in;
    reg [1:0] mode_select;
    reg [7:0] output_length;
    wire [127:0] data_out;
    wire valid_out;
    wire ready_out;
    wire done;

    shake_core uut (
        .clk(clk),
        .reset(reset),
        .start(start),
        .valid_in(valid_in),
        .data_in(data_in),
        .mode_select(mode_select),
        .output_length(output_length),
        .data_out(data_out),
        .valid_out(valid_out),
        .ready_out(ready_out),
        .done(done)
    );

    localparam integer MESSAGE_BYTES = 32;
    reg [7:0] message_mem [0:MESSAGE_BYTES-1];

    integer i;

    initial begin
        for (i = 0; i < MESSAGE_BYTES; i = i + 1) begin
            message_mem[i] = i[7:0];
        end
    end

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task automatic send_message(input integer words);
        integer w;
        integer b;
        begin
            w = 0;
            while (w < words) begin
                @(posedge clk);
                if (ready_out) begin
                    start <= (w == 0) ? 1'b1 : 1'b0;
                    valid_in <= 1'b1;
                    for (b = 0; b < 16; b = b + 1) begin
                        data_in[8*b +: 8] <= message_mem[w*16 + b];
                    end
                    w = w + 1;
                end else begin
                    start <= 1'b0;
                    valid_in <= 1'b0;
                end
            end
            @(posedge clk);
            start    <= 1'b0;
            valid_in <= 1'b0;
            data_in  <= 128'd0;
        end
    endtask

    task automatic collect_output(
        input integer target_length,
        input string filename
    );
        integer out_idx;
        integer f;
        integer b;
        reg [7:0] buffer [0:255];
        begin
            out_idx = 0;
            while (out_idx < target_length) begin
                @(posedge clk);
                if (valid_out) begin
                    for (b = 0; b < 16; b = b + 1) begin
                        if (out_idx < target_length) begin
                            buffer[out_idx] = data_out[8*b +: 8];
                            out_idx = out_idx + 1;
                        end
                    end
                end
            end
            wait (done == 1'b1);
            @(posedge clk);
            f = $fopen(filename, "w");
            for (b = 0; b < target_length; b = b + 1) begin
                $fdisplay(f, "%02x", buffer[b]);
            end
            $fclose(f);
        end
    endtask

    initial begin
        reset = 1'b1;
        start = 1'b0;
        valid_in = 1'b0;
        data_in = 128'd0;
        mode_select = 2'b00;
        output_length = 8'd32;
        @(posedge clk);
        @(posedge clk);
        reset = 1'b0;
        @(posedge clk);

        // SHAKE-128 test
        mode_select = 2'b00;
        output_length = 8'd32;
        fork
            send_message(2);
            collect_output(32, "0.SHAKE/test/shake128_output.hex");
        join
        repeat (10) @(posedge clk);

        // Reset for SHAKE-256 test
        reset = 1'b1;
        @(posedge clk);
        reset = 1'b0;
        @(posedge clk);

        // SHAKE-256 test
        mode_select = 2'b01;
        output_length = 8'd32;
        fork
            send_message(2);
            collect_output(32, "0.SHAKE/test/shake256_output.hex");
        join

        repeat (20) @(posedge clk);
        $finish;
    end

endmodule

