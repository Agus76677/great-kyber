create_clock -name sys_clk -period 10.000 [get_ports clk]
set_input_delay -clock sys_clk 2.5 [all_inputs]
set_output_delay -clock sys_clk 2.5 [all_outputs]
set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets clk]
