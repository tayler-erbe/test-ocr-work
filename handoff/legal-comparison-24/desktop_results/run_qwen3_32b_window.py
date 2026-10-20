"""GPU window for the Qwen3-32B arms: hand the card to Ollama, run baseline, reasoning and fulldoc,
then ALWAYS unload Ollama and give the card back to the 8001 server (restore_vl8001.py).

Runs as a vllm-lane job on the Skyrule job queue so no other GPU job overlaps it.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = Path("C:/dev/skyrule-fresh/.opencode/ops")
PY = str(HERE.parents[2] / ".venv" / "Scripts" / "python.exe")


def sh(args, **kw):
    print(">", " ".join(args), flush=True)
    return subprocess.run(args, **kw).returncode


def main():
    rc = 0
    try:
        if sh([sys.executable, str(OPS / "gpu.py"), "switch", "ollama"]) != 0:
            print("GPU switch to ollama refused or failed; nothing run", flush=True)
            return 3
        for arm in ("baseline", "reasoning", "fulldoc"):
            r = sh([PY, "-X", "utf8", str(HERE / "run_desktop.py"), "run", "--model", "qwen3:32b", "--arm", arm])
            rc = rc or r
    finally:
        sh(["ollama", "stop", "qwen3:32b"])
        r = sh([sys.executable, str(OPS / "restore_vl8001.py")], cwd=str(OPS.parents[1]))
        if r != 0:
            rc = rc or 4
    return rc


if __name__ == "__main__":
    sys.exit(main())
