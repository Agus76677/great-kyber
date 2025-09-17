module kyber_intt (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,
    input  wire        valid_in,
    input  wire [127:0] data_in,
    output reg         ready_in,
    output reg [127:0] data_out,
    output reg         valid_out,
    output reg         done
);
    `include "kyber_params.vh"
    `include "kyber_mod_functions.vh"

    localparam S_IDLE    = 3'd0;
    localparam S_LOAD    = 3'd1;
    localparam S_COMPUTE = 3'd2;
    localparam S_SCALE   = 3'd3;
    localparam S_OUTPUT  = 3'd4;
    localparam S_DONE    = 3'd5;

    reg [2:0] state;
    reg [5:0] load_word_idx;
    reg [5:0] output_word_idx;
    reg [8:0] len_size;
    reg [8:0] block_base;
    reg [8:0] position;
    reg [8:0] twiddle_base;
    reg       compute_phase;
    reg [8:0] addr_a_reg;
    reg [8:0] addr_b_reg;
    reg [15:0] value_a;
    reg [15:0] value_b;
    reg [15:0] zeta_reg;
    reg [15:0] t_val;
    reg [8:0] scale_idx;

    reg [15:0] coeffs [0:KYBER_N-1];

    wire [8:0] zeta_addr = twiddle_base + position;
    wire [15:0] zeta_value;

    integer i;

    zetas_inv_rom zetas_inst (
        .addr(zeta_addr),
        .data(zeta_value)
    );

    always @(posedge clk) begin
        if (reset) begin
            state           <= S_IDLE;
            ready_in        <= 1'b0;
            valid_out       <= 1'b0;
            done            <= 1'b0;
            load_word_idx   <= 6'd0;
            output_word_idx <= 6'd0;
            len_size        <= KYBER_N >> 1;
            block_base      <= 9'd0;
            position        <= 9'd0;
            twiddle_base    <= 9'd0;
            compute_phase   <= 1'b0;
            scale_idx       <= 9'd0;
        end else begin
            done      <= 1'b0;
            valid_out <= 1'b0;

            case (state)
                S_IDLE: begin
                    ready_in <= 1'b0;
                    if (start) begin
                        state         <= S_LOAD;
                        load_word_idx <= 6'd0;
                        ready_in      <= 1'b1;
                    end
                end

                S_LOAD: begin
                    ready_in <= 1'b1;
                    if (valid_in) begin
                        for (i = 0; i < 8; i = i + 1) begin
                            coeffs[{load_word_idx, 3'b000} + i] <= data_in[16*i +: 16];
                        end
                        if (load_word_idx == 6'd31) begin
                            state         <= S_COMPUTE;
                            ready_in      <= 1'b0;
                            len_size      <= KYBER_N >> 1;
                            block_base    <= 9'd0;
                            position      <= 9'd0;
                            twiddle_base  <= 9'd0;
                            compute_phase <= 1'b0;
                        end else begin
                            load_word_idx <= load_word_idx + 6'd1;
                        end
                    end
                end

                S_COMPUTE: begin
                    if (!compute_phase) begin
                        addr_a_reg   <= block_base + position;
                        addr_b_reg   <= block_base + position + len_size;
                        value_a      <= coeffs[block_base + position];
                        value_b      <= coeffs[block_base + position + len_size];
                        zeta_reg     <= zeta_value;
                        compute_phase <= 1'b1;
                    end else begin
                        coeffs[addr_a_reg] <= mod_add(value_a, value_b);
                        t_val = mod_sub(value_a, value_b);
                        coeffs[addr_b_reg] <= barrett_reduce(t_val * zeta_reg);
                        compute_phase <= 1'b0;

                        if (position == len_size - 1) begin
                            position <= 9'd0;
                            if (block_base + (len_size << 1) >= KYBER_N) begin
                                block_base   <= 9'd0;
                                twiddle_base <= twiddle_base + len_size;
                                if (len_size == 9'd1) begin
                                    state     <= S_SCALE;
                                    scale_idx <= 9'd0;
                                end else begin
                                    len_size <= len_size >> 1;
                                end
                            end else begin
                                block_base <= block_base + (len_size << 1);
                            end
                        end else begin
                            position <= position + 9'd1;
                        end
                    end
                end

                S_SCALE: begin
                    coeffs[scale_idx] <= barrett_reduce(coeffs[scale_idx] * KYBER_N_INV);
                    if (scale_idx == KYBER_N - 1) begin
                        state           <= S_OUTPUT;
                        output_word_idx <= 6'd0;
                    end else begin
                        scale_idx <= scale_idx + 9'd1;
                    end
                end

                S_OUTPUT: begin
                    ready_in  <= 1'b0;
                    valid_out <= 1'b1;
                    for (i = 0; i < 8; i = i + 1) begin
                        data_out[16*i +: 16] <= coeffs[{output_word_idx, 3'b000} + i];
                    end
                    if (output_word_idx == 6'd31) begin
                        state <= S_DONE;
                    end else begin
                        output_word_idx <= output_word_idx + 6'd1;
                    end
                end

                S_DONE: begin
                    done      <= 1'b1;
                    ready_in  <= 1'b0;
                    state     <= S_IDLE;
                end
            endcase
        end
    end
endmodule
