// Number Theoretic Transform (NTT) core for Kyber polynomials
// Implements a streaming load-compute-output flow using a radix-2 butterfly
// with per-stage twiddle factor accumulation. Modular arithmetic is reduced
// via Barrett reduction to avoid costly division.
`timescale 1ns/1ps

module ntt_core (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire [127:0] data_in,
    input  wire        valid_in,
    output wire        ready_in,
    output reg  [127:0] data_out,
    output reg         valid_out,
    output reg         done
);
    localparam integer N             = 256;
    localparam integer LOGN          = 8;
    localparam integer WORDS         = N / 8;
    localparam integer Q             = 3329;
    localparam integer TOTAL_OPS     = 1024; // N/2 * log2(N)

    // FSM states
    localparam [1:0] ST_IDLE   = 2'd0;
    localparam [1:0] ST_LOAD   = 2'd1;
    localparam [1:0] ST_COMPUTE= 2'd2;
    localparam [1:0] ST_OUTPUT = 2'd3;

    reg [1:0] state, next_state;

    // storage for polynomial coefficients
    reg [15:0] coeff_mem [0:N-1];

    // load control
    reg [5:0] load_index;
    wire load_done = (load_index == WORDS);

    // compute control
    reg [10:0] op_count;
    reg [2:0]  stage_idx;
    reg [8:0]  stage_len;
    reg [8:0]  start_idx;
    reg [8:0]  j_idx;
    reg [15:0] twiddle_acc;
    reg [15:0] stage_root_val;

    // pipeline registers
    reg        pipe0_valid;
    reg [8:0]  pipe0_addr_a;
    reg [8:0]  pipe0_addr_b;
    reg [15:0] pipe0_a;
    reg [15:0] pipe0_b;
    reg [15:0] pipe0_twiddle;

    reg        pipe1_valid;
    reg [8:0]  pipe1_addr_a;
    reg [8:0]  pipe1_addr_b;
    reg [15:0] pipe1_sum;
    reg [15:0] pipe1_diff;

    // multiplier helpers
    wire [31:0] mul_operand = pipe0_b * pipe0_twiddle;
    wire [15:0] mul_result;
    barrett_reduce br_mul (
        .value_in(mul_operand),
        .value_out(mul_result)
    );

    // twiddle accumulation multiplication
    wire [31:0] twiddle_mul_operand = twiddle_acc * stage_root_val;
    wire [15:0] twiddle_mul_result;
    barrett_reduce br_twiddle (
        .value_in(twiddle_mul_operand),
        .value_out(twiddle_mul_result)
    );

    // helper functions for modular add/sub
    function [15:0] mod_add;
        input [15:0] a;
        input [15:0] b;
        reg [16:0] tmp;
        begin
            tmp = a + b;
            if (tmp >= Q)
                tmp = tmp - Q;
            mod_add = tmp[15:0];
        end
    endfunction

    function [15:0] mod_sub;
        input [15:0] a;
        input [15:0] b;
        reg [16:0] tmp;
        begin
            tmp = a + Q - b;
            if (tmp >= Q)
                tmp = tmp - Q;
            mod_sub = tmp[15:0];
        end
    endfunction

    function [15:0] stage_root_lookup;
        input [2:0] idx;
        begin
            case (idx)
                3'd0: stage_root_lookup = 16'd3061;
                3'd1: stage_root_lookup = 16'd1915;
                3'd2: stage_root_lookup = 16'd1996;
                3'd3: stage_root_lookup = 16'd2532;
                3'd4: stage_root_lookup = 16'd2699;
                3'd5: stage_root_lookup = 16'd749;
                3'd6: stage_root_lookup = 16'd1729;
                3'd7: stage_root_lookup = 16'd3328;
                default: stage_root_lookup = 16'd1;
            endcase
        end
    endfunction

    // FSM sequential
    always @(posedge clk or posedge rst) begin
        if (rst)
            state <= ST_IDLE;
        else
            state <= next_state;
    end

    // FSM combinational
    always @(*) begin
        next_state = state;
        case (state)
            ST_IDLE: begin
                if (start)
                    next_state = ST_LOAD;
            end
            ST_LOAD: begin
                if (load_done)
                    next_state = ST_COMPUTE;
            end
            ST_COMPUTE: begin
                if (op_count == TOTAL_OPS && !pipe0_valid && !pipe1_valid)
                    next_state = ST_OUTPUT;
            end
            ST_OUTPUT: begin
                if (done)
                    next_state = ST_IDLE;
            end
            default: next_state = ST_IDLE;
        endcase
    end

    assign ready_in = (state == ST_LOAD);

    // load logic
    integer lane;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            load_index <= 6'd0;
        end else if (state == ST_IDLE) begin
            load_index <= 6'd0;
        end else if (state == ST_LOAD && valid_in && ready_in) begin
            for (lane = 0; lane < 8; lane = lane + 1) begin
                coeff_mem[{load_index, 3'b000} + lane] <= data_in[16*lane +: 16];
            end
            load_index <= load_index + 1'b1;
        end
    end

    // compute control reset on state entry
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            op_count      <= 11'd0;
            stage_idx     <= 3'd0;
            stage_len     <= 9'd128;
            start_idx     <= 9'd0;
            j_idx         <= 9'd0;
            twiddle_acc   <= 16'd1;
            stage_root_val<= stage_root_lookup(3'd0);
        end else if (state == ST_LOAD && next_state == ST_COMPUTE) begin
            op_count      <= 11'd0;
            stage_idx     <= 3'd0;
            stage_len     <= 9'd128;
            start_idx     <= 9'd0;
            j_idx         <= 9'd0;
            twiddle_acc   <= 16'd1;
            stage_root_val<= stage_root_lookup(3'd0);
        end else if (state == ST_COMPUTE && op_count < TOTAL_OPS) begin
            // update indices after scheduling current operation
            if (j_idx + 1 == start_idx + stage_len) begin
                if (start_idx + (stage_len << 1) >= N) begin
                    stage_idx   <= stage_idx + 1'b1;
                    stage_len   <= stage_len >> 1;
                    start_idx   <= 9'd0;
                    j_idx       <= 9'd0;
                    twiddle_acc <= 16'd1;
                    stage_root_val <= stage_root_lookup(stage_idx + 1'b1);
                end else begin
                    start_idx   <= start_idx + (stage_len << 1);
                    j_idx       <= start_idx + (stage_len << 1);
                    twiddle_acc <= 16'd1;
                end
            end else begin
                j_idx       <= j_idx + 1'b1;
                twiddle_acc <= twiddle_mul_result;
            end
            op_count <= op_count + 1'b1;
        end else if (state != ST_COMPUTE) begin
            op_count <= op_count;
        end
    end

    // pipeline management
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            pipe0_valid <= 1'b0;
            pipe1_valid <= 1'b0;
        end else begin
            // stage 0 capture
            if (state == ST_COMPUTE && op_count < TOTAL_OPS) begin
                pipe0_valid   <= 1'b1;
                pipe0_addr_a  <= j_idx;
                pipe0_addr_b  <= j_idx + stage_len;
                pipe0_a       <= coeff_mem[j_idx];
                pipe0_b       <= coeff_mem[j_idx + stage_len];
                pipe0_twiddle <= twiddle_acc;
            end else begin
                pipe0_valid <= 1'b0;
            end

            // stage 1 results
            pipe1_valid <= pipe0_valid;
            if (pipe0_valid) begin
                pipe1_addr_a <= pipe0_addr_a;
                pipe1_addr_b <= pipe0_addr_b;
                pipe1_sum    <= mod_add(pipe0_a, mul_result);
                pipe1_diff   <= mod_sub(pipe0_a, mul_result);
            end

            // write back
            if (pipe1_valid) begin
                coeff_mem[pipe1_addr_a] <= pipe1_sum;
                coeff_mem[pipe1_addr_b] <= pipe1_diff;
            end
        end
    end

    // output handling
    reg [5:0] output_index;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            output_index <= 6'd0;
            valid_out    <= 1'b0;
            data_out     <= 128'd0;
            done         <= 1'b0;
        end else begin
            done <= 1'b0;
            if (state == ST_COMPUTE && next_state == ST_OUTPUT) begin
                output_index <= 6'd0;
                valid_out    <= 1'b0;
            end else if (state == ST_OUTPUT) begin
                if (output_index < WORDS) begin
                    for (lane = 0; lane < 8; lane = lane + 1) begin
                        data_out[16*lane +: 16] <= coeff_mem[{output_index, 3'b000} + lane];
                    end
                    valid_out <= 1'b1;
                    output_index <= output_index + 1'b1;
                    if (output_index == WORDS - 1) begin
                        done <= 1'b1;
                    end
                end else begin
                    valid_out <= 1'b0;
                end
            end else begin
                valid_out <= 1'b0;
            end
        end
    end
endmodule
