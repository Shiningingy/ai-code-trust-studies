"""Host-side model service.

Speaks OpenAI chat completions to AssertFlip in its containers and answers each
request with one fresh `claude -p`. Handles text only: it never runs anything a
container sends, never reads the login token, and `claude` runs with no tools.

Validity: a call counts only if `judge` accepts it. On the first failed call the
service trips and answers every later call with a 429 carrying the quota text,
which AssertFlip re-raises, so the run exits with an error.
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUOTA = "You exceeded your current quota"
MODEL = "claude-sonnet-5-5"
LABEL = "gpt-4o"
EFFORT = "medium"
CLAUDE = "claude"  # path to the Claude Code executable
NEUTRAL = r"G:\devwork\app"
CALL_TIMEOUT = 900

CLOSING = "Reply as the assistant to the last message above."
TOOL_NOTE = """You can call the tools below.

{schemas}

To call one, reply with nothing except:
<tool_call>{{"name": "<tool name>", "arguments": {{...}}}}</tool_call>

The result comes back in the next message. There is no other way to call a tool."""
TOOL_TAG = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "ANTHROPIC"))}
    env["DISABLE_NON_ESSENTIAL_MODEL_CALLS"] = "1"
    return env


def claude_backend(system, prompt, schema):
    """The one place that knows how the model is reached. Returns (exit code, stdout)."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(system)
    try:
        cmd = [CLAUDE, "-p", "--safe-mode", "--tools", "", "--system-prompt-file", f.name,
               "--no-session-persistence", "--output-format", "json", "--model", MODEL, "--effort", EFFORT]
        if schema:
            cmd += ["--json-schema", json.dumps(schema)]
        p = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True, cwd=NEUTRAL,
                           env=clean_env(), timeout=CALL_TIMEOUT)
        return p.returncode, p.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, ""
    finally:
        os.unlink(f.name)


def flatten(messages, tools=None):
    """OpenAI messages to (system prompt, one transcript)."""
    system, turns = [], []
    for m in messages:
        role, content = m["role"], m.get("content") or ""
        if role == "system":
            system.append(content)
        elif role == "user":
            turns.append(f"[user]\n{content}")
        elif role == "assistant":
            if content:
                turns.append(f"[assistant]\n{content}")
            for c in m.get("tool_calls") or []:
                f = c["function"]
                turns.append(f"[assistant called {f['name']} with {f['arguments']}]")
        elif role == "tool":
            turns.append(f"[result of {m.get('name', 'tool')}]\n{content}")
    if tools:
        schemas = json.dumps([t["function"] for t in tools], indent=1)
        system.append(TOOL_NOTE.format(schemas=schemas))
    turns.append(CLOSING)
    return "\n\n".join(system), "\n\n".join(turns)


def judge(code, raw, schema):
    """None if the call succeeded, otherwise why it did not. Accepts only clean successes."""
    if code != 0:
        return f"exit {code}"
    try:
        data = json.loads(raw)
    except ValueError:
        return "stdout is not JSON"
    if not isinstance(data, dict):
        return "stdout is not an object"
    if data.get("is_error") is not False:
        return "is_error"
    if data.get("subtype") != "success":
        return f"subtype {data.get('subtype')}"
    if data.get("terminal_reason") != "completed":
        return f"terminal_reason {data.get('terminal_reason')}"
    if schema and "structured_output" not in data:
        return "no structured_output"
    if not schema and not (data.get("result") or "").strip():
        return "empty result"
    return None


def declined(raw):
    """True if the model itself refused the request, as opposed to the call failing."""
    try:
        return json.loads(raw).get("stop_reason") == "refusal"
    except (ValueError, AttributeError):
        return False


def tool_calls(text, tools):
    names = {t["function"]["name"] for t in tools or []}
    calls = []
    for m in TOOL_TAG.finditer(text):
        try:
            c = json.loads(m.group(1))
        except ValueError:
            continue
        if c.get("name") in names and isinstance(c.get("arguments"), dict):
            calls.append({"id": f"call_{uuid.uuid4().hex[:12]}", "type": "function",
                          "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}})
    return calls


def openai_reply(data, tools, schema):
    usage = data.get("usage") or {}
    prompt = sum(usage.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    completion = usage.get("output_tokens") or 0
    if schema:
        message = {"role": "assistant", "content": json.dumps(data["structured_output"])}
        finish = "stop"
    else:
        calls = tool_calls(data["result"], tools)
        message = {"role": "assistant", "content": "" if calls else data["result"]}
        finish = "tool_calls" if calls else "stop"
        if calls:
            message["tool_calls"] = calls
    return {"id": f"chatcmpl-{uuid.uuid4().hex}", "object": "chat.completion", "created": int(time.time()),
            "model": LABEL, "choices": [{"index": 0, "finish_reason": finish, "message": message}],
            "usage": {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}}


class Service:
    def __init__(self, ledger, backend=claude_backend, fail_call=None):
        self.ledger = Path(ledger)
        self.backend = backend
        self.fail_call = fail_call
        self.calls = 0
        self.failed = 0
        self.tripped = None
        self.declined_runs = set()
        self.lock = threading.Lock()

    def status(self):
        return {"tripped": self.tripped, "calls": self.calls, "failed": self.failed}

    def reset(self):
        with self.lock:
            self.tripped = None

    def _log(self, row):
        with self.lock:
            with open(self.ledger, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")

    def _refuse(self):
        return 429, {"error": {"message": QUOTA, "type": "insufficient_quota", "code": "insufficient_quota"}}

    def complete(self, token, body):
        """Returns (HTTP status, JSON body)."""
        if not token.startswith("run-"):
            return 401, {"error": {"message": "unknown run token", "type": "invalid_request_error"}}
        if self.tripped:
            self._log({"t": time.time(), "token": token, "outcome": "refused"})
            return self._refuse()
        if token in self.declined_runs:
            self._log({"t": time.time(), "token": token, "outcome": "after_decline"})
            return self._refuse()

        fmt = body.get("response_format") or {}
        schema = (fmt.get("json_schema") or {}).get("schema")
        tools = None if schema else body.get("tools")
        system, prompt = flatten(body["messages"], tools)

        with self.lock:
            self.calls += 1
            n = self.calls
        started = time.time()
        forced = self.fail_call is not None and n == self.fail_call
        code, raw = (1, "") if forced else self.backend(system, prompt, schema)
        why = "forced by test switch" if forced else judge(code, raw, schema)
        row = {"t": started, "seconds": round(time.time() - started, 1), "token": token, "n": n,
               "outcome": "failed" if why else "ok", "why": why, "exit": code, "schema": bool(schema),
               "system_chars": len(system), "prompt_chars": len(prompt)}
        if not forced and declined(raw):
            # The model's decision on this request stands: this run ends and nothing is retried or reworded.
            with self.lock:
                self.declined_runs.add(token)
            self._log({**row, "outcome": "model_declined", "raw": raw})
            return self._refuse()
        if why:
            with self.lock:
                self.failed += 1
                self.tripped = self.tripped or f"call {n}: {why}"
            row["raw"] = raw
            self._log(row)
            return self._refuse()

        data = json.loads(raw)
        row.update({k: data.get(k) for k in ("usage", "modelUsage", "total_cost_usd", "duration_api_ms", "num_turns", "session_id")})
        reply = openai_reply(data, tools, schema)
        row["tool_calls"] = len(reply["choices"][0]["message"].get("tool_calls") or [])
        self._log(row)
        return 200, reply


def handler_for(service):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            out = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def do_GET(self):
            self._send(200, service.status()) if self.path == "/status" else self._send(404, {})

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if self.path == "/reset":
                service.reset()
                return self._send(200, service.status())
            if not self.path.endswith("/chat/completions"):
                return self._send(404, {})
            token = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            self._send(*service.complete(token, json.loads(body)))

        def log_message(self, *args):
            pass

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--ledger", default=str(Path(__file__).parent.parent / "runs" / "ledger.jsonl"))
    ap.add_argument("--fail-call", type=int, help="test switch: treat call N as failed")
    a = ap.parse_args()
    Path(a.ledger).parent.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), handler_for(Service(a.ledger, fail_call=a.fail_call))).serve_forever()


if __name__ == "__main__":
    main()
