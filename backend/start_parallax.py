#!/usr/bin/env python3
"""
start_parallax.py
Single-node launcher for Parallax (no scheduler).

Model: Qwen/Qwen3-0.6B
Layers: 0–14
Port: 3000

Usage:
    python start_parallax.py
"""

import os
import subprocess
import sys

MODEL = "Qwen/Qwen3-0.6B"
START_LAYER = 0
END_LAYER = 14
PORT = 3000
MAX_BATCH = 8


def find_launch_command():
    """
    Try to launch Parallax using:
    1) `python -m parallax.launch`
    2) local repo fallback: ./parallax/src/parallax/launch.py
    """
    # 1. Try module form
    try:
        import importlib
        importlib.import_module("parallax")
        return [sys.executable, "-m", "parallax.launch"]
    except Exception:
        pass

    # 2. Try local repo
    local_path = os.path.join(os.getcwd(), "parallax", "src", "parallax", "launch.py")
    if os.path.exists(local_path):
        return [sys.executable, local_path]

    raise RuntimeError(
        "Could not find parallax.launch.\n"
        "Either:\n"
        "  pip install -e '.[mac]' inside Parallax repo, OR\n"
        "  run this script from a folder containing ./parallax/src/parallax/launch.py"
    )


def main():
    launch_cmd = find_launch_command()

    cmd = launch_cmd + [
        "--model-path", MODEL,
        "--port", str(PORT),
        "--max-batch-size", str(MAX_BATCH),
        "--start-layer", str(START_LAYER),
        "--end-layer", str(END_LAYER),
    ]

    print("🚀 Starting Parallax single-node server...")
    print("Model:", MODEL)
    print("Layers:", f"{START_LAYER}–{END_LAYER}")
    print("Port:", PORT)
    print("Command:")
    print(" ", " ".join(cmd), "\n")

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
