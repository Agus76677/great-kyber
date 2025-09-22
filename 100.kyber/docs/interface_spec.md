# Interface Specification

## AXI-Lite Control Port
- 32-bit data width, 4 KB address space.
- All registers are little-endian.
- `core_ctrl.start` is level-sensitive; firmware must deassert after a single cycle pulse.
- Status bits sampled synchronously; reading clears sticky error flags.

## AXI-Stream Data Ports
### Ciphertext/Plaintext Input (`s_axis_ct`) 
- `tdata[127:0]`, `tvalid`, `tready`, `tlast`.
- Pack two Kyber coefficients per beat in little-endian order.
- Back-pressure supported; upstream may pause at any cycle.

### Ciphertext/Shared Key Output (`m_axis_ct` / `m_axis_ss`)
- Same signaling as input.
- `m_axis_ss` optional; enabled via configuration register bit.

## Internal Stream Interfaces
- Modules adhere to the ready/valid contract: data transfer occurs on rising clock edge
  when both `valid` and `ready` are asserted.
- Control modules must ensure no combinational loops between `ready` and `valid` paths.

## Interrupts
- Single active-high interrupt line `irq` asserted when operation completes or error occurs.
- Masking controlled via `irq_enable` register; status is W1C in `irq_status`.

## Reset and Clocking
- Global synchronous active-high reset `rst`.
- Primary clock `clk` at 100 MHz (design closed at 200 MHz target).
- All submodules derive enables from clock; no gated clocks allowed.

## Configuration Sequencing
1. Firmware loads seeds and configuration registers via AXI-Lite while `core_status.busy = 0`.
2. Firmware writes `core_ctrl.start = 1` for one cycle.
3. Hardware asserts `core_status.busy = 1`, processes request, and eventually asserts
   `irq` if enabled.
4. Firmware reads result buffers and clears status.
