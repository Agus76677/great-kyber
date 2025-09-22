# Vivado build script skeleton for Kyber accelerator
set project_name kyber_accel
set part_name xc7a200tfbg484-2
set top_module kyber_core

create_project $project_name ./vivado -part $part_name -force
set_property target_language Verilog [current_project]

# Add RTL sources
set rtl_dir [file normalize "../rtl"]
add_files -norecurse [glob -directory $rtl_dir -types f "**/*.v"]
add_files -norecurse [glob -directory $rtl_dir -types f "**/*.vh"]

# Add XDC constraints
read_xdc ../constr/a7_100mhz.xdc

# Run synthesis
launch_runs synth_1 -jobs 8
wait_on_run synth_1

# Run implementation
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

# Report timing and utilization
report_timing_summary -file timing_summary.rpt
report_utilization -file utilization.rpt
