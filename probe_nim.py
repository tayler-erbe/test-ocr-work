"""Learn what an OpenAI-compatible model server (NIM, vLLM) is running, from the API alone.

Reads the endpoint and key from environment variables so neither is ever written
into a file or the repository. Prints the served model, its context limit, the
NIM metadata (whose profile name often states GPU type, precision and GPU count),
and single-user versus 8-user generation speed.

PowerShell:
  $env:NIM_BASE_URL = "https://<server>/v1"
  $env:NIM_API_KEY  = "<your key>"
  python probe_nim.py
"""
import concurrent.futures
import json
import os
import time
import urllib.request

BASE = os.environ["NIM_BASE_URL"].rstrip("/")
KEY = os.environ.get("NIM_API_KEY", "")
HEADERS = {"Content-Type": "application/json", **({"Authorization": f"Bearer {KEY}"} if KEY else {})}
ROOT = BASE[:-3] if BASE.endswith("/v1") else BASE


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
            return json.load(response)
    except Exception as error:
        return {"unavailable": f"{type(error).__name__}: {error}"}


def speed(model):
    body = json.dumps({"model": model, "max_tokens": 400, "temperature": 0,
                       "messages": [{"role": "user", "content": "Write 300 words about contract law."}]}).encode()
    started = time.time()
    with urllib.request.urlopen(urllib.request.Request(BASE + "/chat/completions", body, HEADERS), timeout=300) as response:
        reply = json.load(response)
    return reply["usage"]["completion_tokens"] / (time.time() - started)


def main():
    models = get(BASE + "/models")
    print("== /v1/models (model name, max_model_len) ==")
    print(json.dumps(models, indent=1))
    for path in ("/v1/metadata", "/v1/version", "/v1/health/ready"):
        print(f"== {path} ==")
        print(json.dumps(get(ROOT + path), indent=1)[:4000])
    if "data" not in models:
        return
    model = models["data"][0]["id"]
    print("== speed ==")
    print("1 user, tokens/sec:", round(speed(model)))
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        print("8 users at once, tokens/sec each:", [round(x) for x in pool.map(speed, [model] * 8)])


if __name__ == "__main__":
    main()
