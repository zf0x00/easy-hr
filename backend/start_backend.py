# backend/start_backend.py
import os
import platform
import subprocess
import sys

backend_dir = os.path.dirname(__file__)
venv_bin = "Scripts" if platform.system() == "Windows" else "bin"
python_exec = os.path.join(backend_dir, "venv", venv_bin, "python")

if not os.path.exists(python_exec):
    print("python executable not found at", python_exec)
    sys.exit(1)

cmd = [
    python_exec,
    "-m",
    "uvicorn",
    "server:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
]
subprocess.run(cmd, cwd=backend_dir)
