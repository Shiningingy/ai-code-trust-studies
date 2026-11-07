"""MCP server (stdio) with one tool, `run`, that executes a shell command inside the
task's Docker container. The agent's file tools work on the host checkout, which is
bind-mounted into the container at /work, so edits show up on both sides. The container
has no network, and the host never runs repository code.

Hand-written JSON-RPC so the study has no MCP library dependency.
Usage (from an MCP config): python box_mcp.py <container name> <log file>
"""
import json
import subprocess
import sys
import time

CONTAINER, LOG = sys.argv[1], sys.argv[2]
LIMIT = 30000  # characters of output returned to the agent
DEFAULT_TIMEOUT, MAX_TIMEOUT = 300, 900

TOOL = {
    "name": "run",
    "description": ("Run a shell command (bash) in the project's Linux environment. The repository is the "
                    "working directory (/work). Returns exit code and combined stdout/stderr (long output is "
                    "truncated in the middle). There is no network access."),
    "inputSchema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "bash command line"},
            "timeout": {"type": "integer", "description": f"seconds, default {DEFAULT_TIMEOUT}, max {MAX_TIMEOUT}"},
        },
        "required": ["command"],
    },
}


def log(row):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def run(command, timeout):
    timeout = max(1, min(int(timeout or DEFAULT_TIMEOUT), MAX_TIMEOUT))
    started = time.time()
    cmd = ["docker", "exec", "-w", "/work", CONTAINER, "timeout", "-k", "5", str(timeout), "bash", "-lc", command]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout + 30)
        code, out = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        code, out = 124, ""
    if code == 124:
        out += f"\n[timed out after {timeout}s]"
    if len(out) > LIMIT:
        half = LIMIT // 2
        out = out[:half] + f"\n[... {len(out) - LIMIT} characters cut ...]\n" + out[-half:]
    log({"t": started, "seconds": round(time.time() - started, 1), "command": command, "exit": code, "chars": len(out)})
    return f"exit code {code}\n{out}"


def reply(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        method, id_ = req.get("method"), req.get("id")
        if id_ is None:  # notification
            continue
        if method == "initialize":
            reply(id_, {"protocolVersion": req["params"].get("protocolVersion", "2024-11-05"),
                        "capabilities": {"tools": {}}, "serverInfo": {"name": "box", "version": "1"}})
        elif method == "tools/list":
            reply(id_, {"tools": [TOOL]})
        elif method == "tools/call":
            args = req["params"].get("arguments") or {}
            text = run(args.get("command", ""), args.get("timeout"))
            reply(id_, {"content": [{"type": "text", "text": text}]})
        elif method == "ping":
            reply(id_, {})
        else:
            reply(id_, error={"code": -32601, "message": f"no method {method}"})


if __name__ == "__main__":
    main()
