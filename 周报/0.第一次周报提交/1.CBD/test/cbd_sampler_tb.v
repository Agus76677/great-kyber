`timescale 1ns / 1ps

module cbd_sampler_tb;
    // -------------------- 测试参数配置 --------------------
    localparam integer LANES      = 4;   // 并行通道数
    localparam integer RAND_WIDTH = 128; // 随机输入位宽
    localparam integer ETA        = 3;   // 分布参数
    localparam integer CAND_BITS  = 4;   // 输出采样位宽
    localparam integer BERN_WIDTH = 8;   // 伯努利采样阈值位宽
    localparam integer REJ_WIDTH  = 8;   // 拒绝采样位宽

    // -------------------- 信号定义 --------------------
    reg                        clk;
    reg                        reset;
    reg                        start;
    reg                        valid_in;
    reg  [RAND_WIDTH-1:0]      random_in;
    reg  [BERN_WIDTH-1:0]      threshold;
    wire [LANES*CAND_BITS-1:0] sampled_vals;
    wire [LANES-1:0]           accepted_flags;
    wire                       done;

    // -------------------- 文件操作相关变量 --------------------
    integer                    input_file;     // 输入数据文件句柄
    integer                    output_file;    // 输出结果文件句柄
    integer                    vector_count;   // 测试向量数量
    integer                    idx;            // 测试向量索引
    integer                    scan_status;    // 文件读取状态
    reg [BERN_WIDTH-1:0]       threshold_word; // 从文件读取的阈值数据
    reg [RAND_WIDTH-1:0]       random_word;    // 从文件读取的随机数据

    // -------------------- DUT 实例化 --------------------
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

    // -------------------- 时钟产生 --------------------
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns 时钟周期 -> 100MHz
    end

    // -------------------- 复位逻辑 --------------------
    initial begin
        reset      = 1'b1;
        start      = 1'b0;
        valid_in   = 1'b0;
        threshold  = {BERN_WIDTH{1'b0}};
        random_in  = {RAND_WIDTH{1'b0}};
        #40;                   // 保持 40ns 复位
        reset = 1'b0;          // 释放复位
    end

    // -------------------- 主测试过程 --------------------
    initial begin
        // 打开输入文件
        input_file  = $fopen("D:/desktopnew/Vivado_Projects/0.Kyber/1.CBD/test/cbd_input.txt", "r");
        if (input_file == 0) begin
            $fatal(1, "无法打开输入文件 cbd_input.txt");
        end
        // 打开输出文件
        output_file = $fopen("D:/desktopnew/Vivado_Projects/0.Kyber/1.CBD/test/hw_output.txt", "w");
        if (output_file == 0) begin
            $fatal(1, "无法打开输出文件 hw_output.txt");
        end

        // 从输入文件读取测试向量总数
        scan_status = $fscanf(input_file, "%d\n", vector_count);
        if (scan_status != 1) begin
            $fatal(1, "读取测试向量数量失败");
        end

        // 等待复位结束
        @(negedge reset);
        @(posedge clk);

        // 循环读取每组测试向量
        for (idx = 0; idx < vector_count; idx = idx + 1) begin
            // 读取阈值和随机数据
            scan_status = $fscanf(input_file, "%h %h\n", threshold_word, random_word);
            if (scan_status != 2) begin
                $fatal(1, "读取第 %0d 组测试数据失败", idx);
            end

            // 将输入数据送入 DUT
            threshold <= threshold_word;
            random_in <= random_word;
            start     <= 1'b1;
            valid_in  <= 1'b1;
            @(posedge clk);
            start     <= 1'b0;
            valid_in  <= 1'b0;

            // 等待采样模块完成计算
            wait_done();
            #1;

            // 将采样结果写入输出文件
            $fwrite(output_file, "%01h %04h\n", accepted_flags, sampled_vals);
            @(posedge clk);
        end

        // 关闭文件，结束仿真
        $fclose(input_file);
        $fclose(output_file);
        #20;
        $finish;
    end

    // -------------------- 等待 done 任务 --------------------
    task wait_done;
        begin
            while (done == 1'b0) begin
                @(posedge clk);
            end
        end
    endtask

endmodule
