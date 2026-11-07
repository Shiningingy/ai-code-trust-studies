"""Per-PR Docker environments.

An image is built once per PR at the base commit: a container from the recipe's base image runs the
recipe's setup with network on and the base tree mounted at /work, then is committed. Every later
container (agent runs, test runs) starts from that image with a tree mounted at /work and, unless
stated, no network. Repository code never runs on the host.
"""
import importlib
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
    # per-repo recipes for the main draw live in one file per language (recipes_python.py, recipes_go.py):
    # RECIPES = {"owner/repo": function(meta, tree) -> recipe dict}; they take precedence over the defaults below
    for modname in ("recipes_python", "recipes_go"):
        try:
            mod = importlib.import_module(modname)
        except ImportError:
            continue
        if repo in getattr(mod, "RECIPES", {}):
            return mod.RECIPES[repo](meta, tree)
    if repo == "home-assistant/core":
        return {"image": "python:3.13-bookworm", "env": {"PYTHONPATH": "/work"},
                "setup": PY_BASE.format(apt="libturbojpeg0 libpcap-dev ffmpeg libavformat-dev libavcodec-dev "
                                            "libavdevice-dev libavutil-dev libswscale-dev libswresample-dev "
                                            "libavfilter-dev autoconf") +
                "cd /work; python /opt/ha_components.py > /tmp/int.txt; cat /tmp/int.txt; "
                # mypy-dev pre-releases are deleted from PyPI; the type checker is not needed to run tests
                "sed -e '/^mypy-dev/d' -e 's#^\\(-[rc] *\\)\\([^/]\\)#\\1/work/\\2#' requirements_test.txt "
                "> /tmp/req_test.txt; "
                "uv pip install --system -q --exclude-newer \"$MERGED_AT\" -c homeassistant/package_constraints.txt "
                "-r /tmp/req_test.txt -r requirements.txt -r /tmp/int.txt",
                # generated, git-ignored translation files (HA's script/setup makes them); every new box
                "prepare": "python -m script.translations develop --all > /tmp/translations.log 2>&1 "
                           "|| echo 'translations failed'",
                "pytest": "python -m pytest -p no:randomly -o addopts='' -n 0"}
    if repo == "getsentry/sentry-python":
        return {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": "/work"},
                "setup": PY_BASE.format(apt="") +
                "cd /work; python /opt/sentry_extras.py > /tmp/extras.txt; cat /tmp/extras.txt; "
                "uv pip install --system -q --exclude-newer \"$MERGED_AT\" -r requirements-testing.txt "
                "-r /tmp/extras.txt . ; pip uninstall -y -q sentry-sdk || true",
                "pytest": "python -m pytest -o addopts=''"}
    if meta["language"] == "Go":
        v = go_version(tree)
        pkgs = " ".join(sorted({"./" + str(Path(f).parent).replace("\\", "/") for f in meta["runnable_tests"]}))
        # -trimpath keeps build-cache keys independent of the tree's path, so the warm cache from setup
        # (built in a copy at /tmp/w, leaving the snapshot untouched) serves every later container
        r = {"image": f"golang:{v}-bookworm", "env": {"GOFLAGS": "-mod=mod -trimpath", "GOTOOLCHAIN": "auto"}}
        pre, gen = "", ""
        if repo == "gruntwork-io/terragrunt":
            pre = ("TOFU=$(grep -oP 'opentofu = \"\\K[^\"]+' /work/mise.toml || echo 1.10.5); "
                   "curl -fsSL -o /tmp/tofu.tgz https://github.com/opentofu/opentofu/releases/download/v$TOFU/"
                   "tofu_${TOFU}_linux_amd64.tar.gz; tar -xzf /tmp/tofu.tgz -C /usr/local/bin tofu; "
                   "ln -sf /usr/local/bin/tofu /usr/local/bin/terraform; tofu version; ")
        if repo == "zitadel/zitadel":
            pre = ("mkdir -p /opt/zbin; grep -o 'go install [^\"]*' apps/api/project.json | sed 's/\\\\u0027//g' | "
                   "sort -u | while read -r cmd; do (cd /work && GOBIN=/opt/zbin $cmd) || echo \"failed: $cmd\"; done; ")
            gen = "bash /opt/zitadel_gen.sh /tmp/w; "
            r["prepare"] = "bash /opt/zitadel_gen.sh /work > /tmp/gen.log 2>&1 || echo 'generation failed'"
        r["setup"] = ("set -e; cd /work; export GOTOOLCHAIN=auto GOFLAGS='-mod=mod -trimpath'; go mod download; " + pre +
                      "rm -rf /tmp/w; cp -r /work /tmp/w; cd /tmp/w; " + gen +
                      f"go build ./... || true; go test -count=1 -run '^$' {pkgs} || true; cd /; rm -rf /tmp/w")
        return r
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
                       "-e", f"MERGED_AT={meta['merged_at']}",
                       r["image"], "bash", "-c", "cp /opt/h/* /opt/; " + r["setup"], timeout=7200)
    log.write_text(out[-100000:], encoding="utf-8")
    if code != 0:
        docker("rm", "-f", name)
        return False
    changes = [f'--change=ENV {k}="{v}"' for k, v in r["env"].items()] + ["--change=WORKDIR /work",
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
    meta = json.loads((PRS / pid / "meta.json").read_text(encoding="utf-8"))
    prep = recipe(meta).get("prepare")
    if prep:
        exec_box(cname, prep, timeout=900)
    return cname


def exec_box(cname, command, timeout=1800):
    try:
        return docker("exec", "-w", "/work", cname, "bash", "-c", command, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        return 124, "[timed out]"


def stop_box(cname):
    docker("rm", "-f", cname)
