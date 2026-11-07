"""Per-PR Docker environments.

An image is built once per PR at the base commit: a container from the recipe's base image runs the
recipe's setup with network on and the base tree mounted at /work, then is committed. Every later
container (agent runs, test runs) starts from that image with a tree mounted at /work and, unless
stated, no network. Repository code never runs on the host.
"""
import json
import re
import subprocess
import uuid
from pathlib import Path

from prepare import PRS, SNAP

PY_BASE = ("set -e; export DEBIAN_FRONTEND=noninteractive; apt-get update -qq; "
           "apt-get install -y -qq git build-essential pkg-config {apt} >/dev/null; "
           "python -m pip install -q --upgrade pip uv; ")


def go_version(tree):
    gomod = (Path(tree) / "go.mod").read_text(encoding="utf-8")
    m = re.search(r"^go (\d+\.\d+)", gomod, re.M)
    return m.group(1) if m else "1.24"


def recipe(meta):
    """image, setup (bash, run in /work with network), env (baked into the image), optional pytest command."""
    repo, tree = meta["repo"], SNAP / meta["id"] / "base"
    if repo == "home-assistant/core":
        return {"image": "python:3.13-bookworm", "env": {"PYTHONPATH": "/work"},
                "setup": PY_BASE.format(apt="libturbojpeg0 libpcap-dev ffmpeg libavformat-dev libavcodec-dev "
                                            "libavdevice-dev libavutil-dev libswscale-dev libswresample-dev "
                                            "libavfilter-dev autoconf") +
                "cd /work; uv pip install --system -q -r requirements_test.txt -r requirements.txt; "
                "uv pip install --system -q --no-deps -e . ; "
                "for c in $(python /opt/ha_components.py); do "
                "python -m script.install_integration_requirements \"$c\" >/dev/null 2>&1 "
                "|| echo \"integration requirements failed: $c\"; done; "
                "pip uninstall -y -q homeassistant || true",
                "pytest": "python -m pytest -p no:randomly -o addopts='' -n 0"}
    if repo == "getsentry/sentry-python":
        return {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": "/work"},
                "setup": PY_BASE.format(apt="") +
                "cd /work; uv pip install --system -q -r requirements-testing.txt; "
                "uv pip install --system -q -e . ; "
                "for x in $(python /opt/sentry_extras.py); do uv pip install --system -q \"$x\" "
                "|| echo \"extra failed: $x\"; done; pip uninstall -y -q sentry-sdk || true",
                "pytest": "python -m pytest -o addopts=''"}
    if meta["language"] == "Go":
        v = go_version(tree)
        pkgs = " ".join(sorted({"./" + str(Path(f).parent).replace("\\", "/") for f in meta["runnable_tests"]}))
        return {"image": f"golang:{v}-bookworm", "env": {"GOFLAGS": "-mod=mod", "GOTOOLCHAIN": "auto"},
                "setup": "set -e; cd /work; export GOTOOLCHAIN=auto; go mod download; "
                         f"go build ./... || true; go test -count=1 -run '^$' {pkgs} || true"}
    raise KeyError(f"no recipe for {repo}")


def tag(pid):
    return "study04/" + re.sub(r"[^a-z0-9._-]", "-", pid.lower()) + ":base"


def docker(*args, timeout=None, check=False):
    p = subprocess.run(["docker", *args], capture_output=True, timeout=timeout)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"docker {args[:2]}: {out[-1500:]}")
    return p.returncode, out


def helpers():
    """Small scripts copied into every image under /opt (read the tree, never the network)."""
    return Path(__file__).parent / "env_helpers"


def build(pid, meta):
    t = tag(pid)
    if docker("image", "inspect", t)[0] == 0:
        return True
    r = recipe(meta)
    name = f"setup-{uuid.uuid4().hex[:8]}"
    log = PRS / pid / "env.log"
    docker("rm", "-f", name)
    code, out = docker("run", "--name", name, "-v", f"{SNAP / pid / 'base'}:/work",
                       "-v", f"{helpers()}:/opt/h:ro", "-e", f"PR_TESTS={' '.join(meta['runnable_tests'])}",
                       r["image"], "bash", "-lc", "cp /opt/h/* /opt/; " + r["setup"], timeout=7200)
    log.write_text(out[-100000:], encoding="utf-8")
    if code != 0:
        docker("rm", "-f", name)
        return False
    changes = [f"--change=ENV {k}={v}" for k, v in r["env"].items()] + ["--change=WORKDIR /work",
                                                                       "--change=CMD [\"sleep\", \"infinity\"]"]
    docker("commit", *changes, name, t, check=True)
    docker("rm", "-f", name)
    return True


def start_box(pid, work, name, network=False):
    cname = f"{name}-{uuid.uuid4().hex[:6]}"
    args = ["run", "-d", "--name", cname, "-v", f"{work}:/work", "-w", "/work"]
    if not network:
        args += ["--network", "none"]
    docker(*args, tag(pid), "sleep", "infinity", check=True)
    return cname


def exec_box(cname, command, timeout=1800):
    try:
        return docker("exec", "-w", "/work", cname, "bash", "-lc", command, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        return 124, "[timed out]"


def stop_box(cname):
    docker("rm", "-f", cname)
