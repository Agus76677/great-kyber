`timescale 1ns/1ps

module reject_sampler_tb;
    // ---------------- 参数配置 ----------------
    localparam integer LANES = 4;           // 并行通道数
    localparam integer CAND_BITS = 12;      // 每个候选/样本的位宽
    localparam integer NUM_VECTORS = 80;    // （未直接使用）向量数量上限/参考

    // ---------------- DUT 连接信号 ----------------
    reg clk;                                // 时钟
    reg rst_n;                              // 低有效复位
    reg random_valid;                       // 随机输入有效标志
    reg [127:0] random_in;                  // 随机比特输入总线
    reg [15:0] q;                           // 模数 q
    reg [LANES*CAND_BITS-1:0] cand_bus;     // 各通道的候选值打包输入
    reg [LANES*CAND_BITS-1:0] urnd_bus;     // 各通道的均匀随机数（用于拒绝采样门限对比）
    reg [LANES*CAND_BITS-1:0] threshold_bus;// 各通道的阈值（q*floor 等）
    reg [LANES-1:0] mode_select;            // 各通道模式选择

    wire [LANES-1:0] acc_bus;               // 各通道是否接受（accept）标志
    wire [LANES*CAND_BITS-1:0] sample_tdata;// 输出样本打包数据
    wire sample_tvalid;                     // 输出样本有效标志

    // ---------------- 文件与循环控制 ----------------
    integer vec_file;                       // 向量输入文件句柄
    integer out_file;                       // 硬件输出记录文件句柄
    integer scan_fields;                    // fscanf 读取字段数量
    integer vec_count;                      // 已处理向量计数

    // ---------------- DUT 实例化 ----------------
    reject_sampler_core #(
        .LANES(LANES),
        .CAND_BITS(CAND_BITS),
        .CONST_TIME(1)                      // 常数时间选项（1=开启）
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

    // ---------------- 时钟产生：100MHz（周期10ns） ----------------
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // ---------------- 复位与初值、文件打开、主流程 ----------------
    initial begin
        // 初始复位与输入清零
        rst_n = 0;
        random_valid = 0;
        random_in = 128'd0;
        q = 16'd0;
        cand_bus = {LANES*CAND_BITS{1'b0}};
        urnd_bus = {LANES*CAND_BITS{1'b0}};
        threshold_bus = {LANES*CAND_BITS{1'b0}};
        mode_select = {LANES{1'b0}};
        vec_count = 0;
        #(25);              // 维持一段时间的复位
        rst_n = 1;          // 释放复位

        // 打开输入/输出文件（绝对路径）
        vec_file = $fopen("D:/desktopnew/Vivado_Projects/0.Kyber/3.REJECT/test/reject_vectors.txt", "r");
        if (vec_file == 0) begin
            $display("ERROR: could not open vector file");
            $finish;
        end
        out_file = $fopen("D:/desktopnew/Vivado_Projects/0.Kyber/3.REJECT/test/hw_output.txt", "w");
        if (out_file == 0) begin
            $display("ERROR: could not open output file");
            $finish;
        end

        // 让复位和初始值在流水线中稳定传播两拍
        @(posedge clk);
        @(posedge clk);

        // -------- 主循环：逐行读取刺激，驱动 DUT，并记录输出 --------
        while (!$feof(vec_file)) begin
            @(posedge clk);
            // 读取一行向量：顺序需与生成文件保持一致
            scan_fields = $fscanf(
                vec_file,
                "%d %h %h %h %h %h %h\n",
                random_valid,   // 1) 随机有效
                q,              // 2) 模数 q
                cand_bus,       // 3) 候选值总线
                urnd_bus,       // 4) 均匀随机数总线
                threshold_bus,  // 5) 阈值总线
                mode_select,    // 6) 模式选择
                random_in       // 7) 随机比特块
            );
            if (scan_fields != 7) begin
                $display("ERROR: malformed line in vector file at %0d", vec_count);
                $finish;
            end
            vec_count = vec_count + 1;

            // 给组合/寄存路径留 1ns，随后记录一帧输出
            #(1);
            $fwrite(out_file,
                    "%0d %0d %h %0d\n",
                    vec_count,        // 计数器（行号）
                    acc_bus,          // 接受掩码
                    sample_tdata,     // 采样输出
                    sample_tvalid);   // 输出有效
        end

        // -------- 末尾冲刷水管：继续跑若干拍让流水线输出完毕 --------
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

        // 关闭文件并结束仿真
        $fclose(vec_file);
        $fclose(out_file);

        #(20);
        $finish;
    end

endmodule
