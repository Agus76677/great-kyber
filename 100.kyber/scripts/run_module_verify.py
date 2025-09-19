#!/usr/bin/env python3
"""Automation helper to run module-level verification for Kyber accelerator."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "sim"
TEST_DIR = ROOT / "test"
GOLDEN_DIR = ROOT / "golden"


MODULE_TESTS = {
    "shake": "test/shake_tb.v",
    "cbd": "test/cbd_tb.v",
    "uniform": "test/uniform_tb.v",
    "reject": "test/reject_tb.v",
    "ntt": "test/ntt_tb.v",
    "intt": "test/intt_tb.v",
}


def run_sim(tb: Path, extra_args: List[str]) -> int:
    cmd = ["iverilog", "-g2012", "-I", str(ROOT / "rtl"), "-o", str(SIM_DIR / tb.stem), str(tb)]
    cmd.extend(extra_args)
    subprocess.check_call(cmd)
    subprocess.check_call(["vvp", str(SIM_DIR / tb.stem)])
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", nargs="*", help="Subset of modules to run")
    parser.add_argument("--iverilog-arg", action="append", default=[], help="Additional args")
    args = parser.parse_args()

    selected = args.modules or MODULE_TESTS.keys()
    for name in selected:
        tb_path = ROOT / MODULE_TESTS[name]
        print(f"[INFO] Running {name} using {tb_path}")
        run_sim(tb_path, args.iverilog_arg)


if __name__ == "__main__":
    main()
