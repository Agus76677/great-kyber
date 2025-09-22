`timescale 1ns/1ps

// -----------------------------------------------------------------------------
// SHAKE core based on Keccak permutation with simple pipelined round network.
// Supports SHAKE-128 and SHAKE-256 through the mode_select port.
// The core operates on 128-bit input/output data paths and manages absorption
// and squeezing phases internally. A 24 stage round pipeline is used to
// accelerate the Keccak-f[1600] permutation.
// -----------------------------------------------------------------------------

module shake_core (
    input  wire         clk,
    input  wire         reset,
    input  wire         start,
    input  wire         valid_in,
    input  wire [127:0] data_in,
    input  wire [1:0]   mode_select,
    input  wire [7:0]   output_length,
    output reg  [127:0] data_out,
    output reg          valid_out,
    output reg          ready_out,
    output reg          done
);

    localparam STATE_IDLE        = 3'd0;
    localparam STATE_ABSORB      = 3'd1;
    localparam STATE_WAIT_PERM   = 3'd2;
    localparam STATE_SQUEEZE     = 3'd3;

    localparam CONTEXT_ABSORB    = 1'b0;
    localparam CONTEXT_SQUEEZE   = 1'b1;

    reg [2:0]    core_state;
    reg [1599:0] state_reg;
    reg [8:0]    rate_bytes_reg;
    reg [15:0]   absorb_bytes;
    reg [15:0]   message_bytes;
    reg [15:0]   output_length_reg;
    reg [15:0]   output_bytes_generated;
    reg [15:0]   squeeze_byte_index;
    reg          data_seen;
    reg          input_finalized;
    reg          prev_valid_in;
    reg [127:0]  absorb_data_reg;
    reg          absorb_data_valid;
    reg          input_complete_pending;

    reg          permute_pending;
    reg          permute_busy;
    reg          permute_context;
    reg          permute_start;

    wire [1599:0] permute_state_out;
    wire          permute_done;

    integer i;
    integer idx;
    integer remaining;
    integer available;
    integer chunk_bytes;

    // ------------------------------------------------------------------
    // Permutation pipeline
    // ------------------------------------------------------------------
    keccak_permutation u_perm (
        .clk       (clk),
        .rst       (reset),
        .state_in  (state_reg),
        .valid_in  (permute_start),
        .state_out (permute_state_out),
        .valid_out (permute_done)
    );

    // ------------------------------------------------------------------
    // Permutation control handshake
    // ------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            permute_start   <= 1'b0;
            permute_busy    <= 1'b0;
        end else begin
            permute_start <= 1'b0;
            if (permute_pending && !permute_busy) begin
                permute_start <= 1'b1;
                permute_busy  <= 1'b1;
            end
            if (permute_done) begin
                permute_busy <= 1'b0;
            end
        end
    end

    // Track previous valid_in level for end-of-input detection
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            prev_valid_in <= 1'b0;
        end else begin
            prev_valid_in <= valid_in;
        end
    end

    wire end_of_input_raw = (core_state == STATE_ABSORB) && data_seen && prev_valid_in && !valid_in && !input_finalized;
    wire absorb_handshake = ((core_state == STATE_ABSORB) || (core_state == STATE_IDLE && start)) && ready_out && valid_in;
    wire absorb_data_ready = absorb_data_valid;

    // ------------------------------------------------------------------
    // Core state machine
    // ------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            core_state             <= STATE_IDLE;
            state_reg              <= {1600{1'b0}};
            rate_bytes_reg         <= 9'd168;
            absorb_bytes           <= 16'd0;
            message_bytes          <= 16'd0;
            output_length_reg      <= 16'd0;
            output_bytes_generated <= 16'd0;
            squeeze_byte_index     <= 16'd0;
            data_seen              <= 1'b0;
            input_finalized        <= 1'b0;
            permute_pending        <= 1'b0;
            permute_context        <= CONTEXT_ABSORB;
            data_out               <= 128'd0;
            valid_out              <= 1'b0;
            ready_out              <= 1'b1;
            done                   <= 1'b0;
            absorb_data_reg        <= 128'd0;
            absorb_data_valid      <= 1'b0;
            input_complete_pending <= 1'b0;
        end else begin
            valid_out <= 1'b0;
            done      <= 1'b0;

            case (core_state)
                STATE_IDLE: begin
                    ready_out       <= 1'b1;
                    permute_pending <= 1'b0;
                    permute_context <= CONTEXT_ABSORB;
                    input_finalized <= 1'b0;
                    data_seen       <= 1'b0;
                    absorb_bytes    <= 16'd0;
                    message_bytes   <= 16'd0;
                    squeeze_byte_index     <= 16'd0;
                    output_bytes_generated <= 16'd0;
                    if (start) begin
                        core_state        <= STATE_ABSORB;
                        state_reg         <= {1600{1'b0}};
                        rate_bytes_reg    <= (mode_select == 2'b01) ? 9'd136 : 9'd168;
                    output_length_reg <= {8'd0, output_length};
                    absorb_data_valid  <= 1'b0;
                    input_complete_pending <= 1'b0;
                end
            end

            STATE_ABSORB: begin
                    ready_out <= (!permute_busy) && ((absorb_bytes + 16) <= rate_bytes_reg);

                    if (absorb_data_ready) begin
                        data_seen <= 1'b1;
                        for (i = 0; i < 16; i = i + 1) begin
                            idx = absorb_bytes + i;
                            if (idx < rate_bytes_reg) begin
                                state_reg[8*idx +: 8] <= state_reg[8*idx +: 8] ^ absorb_data_reg[8*i +: 8];
                            end
                        end
                        absorb_bytes  <= absorb_bytes + 16;
                        message_bytes <= message_bytes + 16;
                    end

                    if (end_of_input_raw) begin
                        input_complete_pending <= 1'b1;
                    end

                    if (input_complete_pending && !absorb_data_ready) begin
                        input_complete_pending <= 1'b0;
                        input_finalized        <= 1'b1;
                        if (absorb_bytes < rate_bytes_reg) begin
                            state_reg[8*absorb_bytes +: 8] <= state_reg[8*absorb_bytes +: 8] ^ 8'h1F;
                        end else begin
                            state_reg[7:0] <= state_reg[7:0] ^ 8'h1F;
                        end
                        state_reg[8*(rate_bytes_reg-1) +: 8] <= state_reg[8*(rate_bytes_reg-1) +: 8] ^ 8'h80;
                        permute_pending <= 1'b1;
                        permute_context <= CONTEXT_ABSORB;
                        core_state      <= STATE_WAIT_PERM;
                    end
                end

                STATE_WAIT_PERM: begin
                    ready_out <= 1'b0;
                    if (permute_done) begin
                        state_reg          <= permute_state_out;
                        permute_pending    <= 1'b0;
                        squeeze_byte_index <= 16'd0;
                        if (permute_context == CONTEXT_ABSORB) begin
                            output_bytes_generated <= 16'd0;
                            absorb_data_valid      <= 1'b0;
                            input_complete_pending <= 1'b0;
                        end
                        core_state <= STATE_SQUEEZE;
                    end
                end

                STATE_SQUEEZE: begin
                    ready_out <= 1'b0;
                    if (output_bytes_generated < output_length_reg) begin
                        remaining = output_length_reg - output_bytes_generated;
                        available = rate_bytes_reg - squeeze_byte_index;
                        if (available == 0) begin
                            permute_pending <= 1'b1;
                            permute_context <= CONTEXT_SQUEEZE;
                            core_state      <= STATE_WAIT_PERM;
                        end else begin
                            chunk_bytes = 16;
                            if (remaining < chunk_bytes) chunk_bytes = remaining;
                            if (available < chunk_bytes) chunk_bytes = available;

                            data_out = 128'd0;
                            for (i = 0; i < 16; i = i + 1) begin
                                idx = squeeze_byte_index + i;
                                if ((i < chunk_bytes) && (idx < rate_bytes_reg)) begin
                                    data_out[8*i +: 8] = state_reg[8*idx +: 8];
                                end else begin
                                    data_out[8*i +: 8] = 8'h00;
                                end
                            end

                            valid_out              <= 1'b1;
                            squeeze_byte_index     <= squeeze_byte_index + chunk_bytes;
                            output_bytes_generated <= output_bytes_generated + chunk_bytes;

                            if ((output_bytes_generated + chunk_bytes) >= output_length_reg) begin
                                done       <= 1'b1;
                                core_state <= STATE_IDLE;
                            end else if ((squeeze_byte_index + chunk_bytes) >= rate_bytes_reg) begin
                                permute_pending <= 1'b1;
                                permute_context <= CONTEXT_SQUEEZE;
                                core_state      <= STATE_WAIT_PERM;
                            end
                        end
                    end else begin
                        done       <= 1'b1;
                        core_state <= STATE_IDLE;
                    end
                end

                default: begin
                    core_state <= STATE_IDLE;
                end
            endcase
            if (absorb_handshake) begin
                absorb_data_reg <= data_in;
            end
            absorb_data_valid <= absorb_handshake;
        end
    end

endmodule

// -----------------------------------------------------------------------------
// Keccak permutation wrapper: cascades 24 round stages into a pipeline. Each
// stage registers its output enabling high-frequency operation.
// -----------------------------------------------------------------------------
module keccak_permutation (
    input  wire         clk,
    input  wire         rst,
    input  wire [1599:0] state_in,
    input  wire         valid_in,
    output wire [1599:0] state_out,
    output wire         valid_out
);
    wire [1599:0] stage_state [0:24];
    wire          stage_valid [0:24];

    assign stage_state[0] = state_in;
    assign stage_valid[0] = valid_in;

    genvar r;
    generate
        for (r = 0; r < 24; r = r + 1) begin : gen_rounds
            keccak_round #(.ROUND_INDEX(r)) u_round (
                .clk      (clk),
                .rst      (rst),
                .state_in (stage_state[r]),
                .valid_in (stage_valid[r]),
                .state_out(stage_state[r+1]),
                .valid_out(stage_valid[r+1])
            );
        end
    endgenerate

    assign state_out  = stage_state[24];
    assign valid_out  = stage_valid[24];

endmodule

// -----------------------------------------------------------------------------
// Single Keccak round stage.
// -----------------------------------------------------------------------------
module keccak_round #(
    parameter integer ROUND_INDEX = 0
) (
    input  wire         clk,
    input  wire         rst,
    input  wire [1599:0] state_in,
    input  wire         valid_in,
    output reg  [1599:0] state_out,
    output reg          valid_out
);
    wire [63:0] round_constant_value;
    wire [1599:0] round_result;

    assign round_constant_value = round_constant(ROUND_INDEX);
    assign round_result = keccak_round_function(state_in, round_constant_value);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state_out <= {1600{1'b0}};
            valid_out <= 1'b0;
        end else begin
            state_out <= round_result;
            valid_out <= valid_in;
        end
    end

    // ------------------------------------------------------------------
    // Round constant lookup
    // ------------------------------------------------------------------
    function [63:0] round_constant;
        input integer round_idx;
        begin
            case (round_idx)
                0:  round_constant = 64'h0000000000000001;
                1:  round_constant = 64'h0000000000008082;
                2:  round_constant = 64'h800000000000808a;
                3:  round_constant = 64'h8000000080008000;
                4:  round_constant = 64'h000000000000808b;
                5:  round_constant = 64'h0000000080000001;
                6:  round_constant = 64'h8000000080008081;
                7:  round_constant = 64'h8000000000008009;
                8:  round_constant = 64'h000000000000008a;
                9:  round_constant = 64'h0000000000000088;
                10: round_constant = 64'h0000000080008009;
                11: round_constant = 64'h000000008000000a;
                12: round_constant = 64'h000000008000808b;
                13: round_constant = 64'h800000000000008b;
                14: round_constant = 64'h8000000000008089;
                15: round_constant = 64'h8000000000008003;
                16: round_constant = 64'h8000000000008002;
                17: round_constant = 64'h8000000000000080;
                18: round_constant = 64'h000000000000800a;
                19: round_constant = 64'h800000008000000a;
                20: round_constant = 64'h8000000080008081;
                21: round_constant = 64'h8000000000008080;
                22: round_constant = 64'h0000000080000001;
                23: round_constant = 64'h8000000080008008;
                default: round_constant = 64'h0;
            endcase
        end
    endfunction

    // ------------------------------------------------------------------
    // Keccak round function (theta, rho, pi, chi, iota)
    // ------------------------------------------------------------------
    function [1599:0] keccak_round_function;
        input [1599:0] state_value;
        input [63:0]   rc_value;
        integer i;
        integer x_idx;
        integer y_idx;
        reg [63:0] a [0:24];
        reg [63:0] b [0:24];
        reg [63:0] c [0:4];
        reg [63:0] d [0:4];
        reg [63:0] temp [0:24];
        reg [1599:0] result;
        begin
            for (i = 0; i < 25; i = i + 1) begin
                a[i] = state_value[64*i +: 64];
            end

            for (i = 0; i < 5; i = i + 1) begin
                c[i] = a[i] ^ a[i+5] ^ a[i+10] ^ a[i+15] ^ a[i+20];
            end

            for (i = 0; i < 5; i = i + 1) begin
                d[i] = c[(i+4)%5] ^ rotate_left(c[(i+1)%5], 1);
            end

            for (i = 0; i < 25; i = i + 1) begin
                a[i] = a[i] ^ d[i % 5];
            end

            for (i = 0; i < 25; i = i + 1) begin
                b[pi_lane_index(i)] = rotate_left(a[i], rho_offset_index(i));
            end

            for (i = 0; i < 25; i = i + 1) begin
                x_idx = i % 5;
                y_idx = (i / 5);
                temp[i] = b[i] ^ ((~b[y_idx*5 + ((x_idx+1)%5)]) & b[y_idx*5 + ((x_idx+2)%5)]);
            end

            temp[0] = temp[0] ^ rc_value;

            for (i = 0; i < 25; i = i + 1) begin
                result[64*i +: 64] = temp[i];
            end

            keccak_round_function = result;
        end
    endfunction

    // Rotation helper
    function [63:0] rotate_left;
        input [63:0] value;
        input integer offset;
        begin
            if (offset == 0) begin
                rotate_left = value;
            end else begin
                rotate_left = (value << offset) | (value >> (64-offset));
            end
        end
    endfunction

    // Rho offsets for each lane
    function integer rho_offset_index;
        input integer lane_index;
        begin
            case (lane_index)
                0:  rho_offset_index = 0;
                1:  rho_offset_index = 1;
                2:  rho_offset_index = 62;
                3:  rho_offset_index = 28;
                4:  rho_offset_index = 27;
                5:  rho_offset_index = 36;
                6:  rho_offset_index = 44;
                7:  rho_offset_index = 6;
                8:  rho_offset_index = 55;
                9:  rho_offset_index = 20;
                10: rho_offset_index = 3;
                11: rho_offset_index = 10;
                12: rho_offset_index = 43;
                13: rho_offset_index = 25;
                14: rho_offset_index = 39;
                15: rho_offset_index = 41;
                16: rho_offset_index = 45;
                17: rho_offset_index = 15;
                18: rho_offset_index = 21;
                19: rho_offset_index = 8;
                20: rho_offset_index = 18;
                21: rho_offset_index = 2;
                22: rho_offset_index = 61;
                23: rho_offset_index = 56;
                24: rho_offset_index = 14;
                default: rho_offset_index = 0;
            endcase
        end
    endfunction

    function integer pi_lane_index;
        input integer lane_index;
        begin
            case (lane_index)
                0:  pi_lane_index = 0;
                1:  pi_lane_index = 10;
                2:  pi_lane_index = 20;
                3:  pi_lane_index = 5;
                4:  pi_lane_index = 15;
                5:  pi_lane_index = 16;
                6:  pi_lane_index = 1;
                7:  pi_lane_index = 11;
                8:  pi_lane_index = 21;
                9:  pi_lane_index = 6;
                10: pi_lane_index = 7;
                11: pi_lane_index = 17;
                12: pi_lane_index = 2;
                13: pi_lane_index = 12;
                14: pi_lane_index = 22;
                15: pi_lane_index = 23;
                16: pi_lane_index = 8;
                17: pi_lane_index = 18;
                18: pi_lane_index = 3;
                19: pi_lane_index = 13;
                20: pi_lane_index = 14;
                21: pi_lane_index = 24;
                22: pi_lane_index = 9;
                23: pi_lane_index = 19;
                24: pi_lane_index = 4;
                default: pi_lane_index = 0;
            endcase
        end
    endfunction

endmodule

