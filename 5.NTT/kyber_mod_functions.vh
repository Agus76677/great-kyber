function automatic [15:0] barrett_reduce(input [31:0] value);
    reg [47:0] prod;
    reg [31:0] t;
    reg signed [33:0] reduced;
begin
    prod = value * BARRETT_V;
    t = (prod + BARRETT_ROUND) >> BARRETT_SHIFT;
    reduced = $signed({1'b0, value}) - $signed({1'b0, t * KYBER_Q});
    if (reduced < 0)
        reduced = reduced + KYBER_Q;
    if (reduced < 0)
        reduced = reduced + KYBER_Q;
    if (reduced >= KYBER_Q)
        reduced = reduced - KYBER_Q;
    if (reduced >= KYBER_Q)
        reduced = reduced - KYBER_Q;
    barrett_reduce = reduced[15:0];
end
endfunction

function automatic [15:0] mod_add(input [15:0] a, input [15:0] b);
    reg [16:0] tmp;
begin
    tmp = a + b;
    if (tmp >= KYBER_Q)
        tmp = tmp - KYBER_Q;
    mod_add = tmp[15:0];
end
endfunction

function automatic [15:0] mod_sub(input [15:0] a, input [15:0] b);
    reg signed [16:0] tmp;
begin
    tmp = $signed({1'b0, a}) - $signed({1'b0, b});
    if (tmp < 0)
        tmp = tmp + KYBER_Q;
    if (tmp < 0)
        tmp = tmp + KYBER_Q;
    mod_sub = tmp[15:0];
end
endfunction
