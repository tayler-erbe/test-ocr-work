"""GPU window for the Qwen3-32B evidence-by-ID arms: hand the card to Ollama, run the arms, then ALWAYS unload
Ollama and give the card back to the 8001 server (restore_vl8001.py). Runs as a vllm-lane queue job so no other
GPU job overlaps it.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = Path("C:/dev/skyrule-fresh/.opencode/ops")
PY = "C:/dev/test-ocr-work-legal/.venv/Scripts/python.exe"
ARMS = ("id_x", "trim_x", "two_x", "id_full", "trim_full")


def sh(args, **kw):
    print(">", " ".join(args), flush=True)
    return subprocess.run(args, **kw).returncode


def main():
    rc = 0
    try:
        if sh([sys.executable, str(OPS / "gpu.py"), "switch", "ollama"]) != 0:
            print("GPU switch to ollama refused or failed; nothing run", flush=True)
            return 3
        for arm in ARMS:
            rc = rc or sh([PY, "-X", "utf8", str(HERE / "run_evid.py"), "run", "--model", "qwen3:32b", "--arm", arm])
    finally:
        sh(["ollama", "stop", "qwen3:32b"])
        if sh([sys.executable, str(OPS / "restore_vl8001.py")], cwd=str(OPS.parents[1])) != 0:
            rc = rc or 4
    return rc


if __name__ == "__main__":
    sys.exit(main())
