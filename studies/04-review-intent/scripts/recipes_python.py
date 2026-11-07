"""Per-repo environment recipes for the Python PRs of the main draw (see env.recipe)."""
import json
from pathlib import Path

PY_BASE = ("set -e; export DEBIAN_FRONTEND=noninteractive; apt-get update -qq; "
           "apt-get install -y -qq git build-essential pkg-config {apt} >/dev/null; "
           "python -m pip install -q --upgrade pip uv; ")
UV = "uv pip install --system -q --exclude-newer \"$MERGED_AT\" "


def azure_cli(meta, tree):
    # python 3.10: the pinned jmespath 0.9.5 calls random.sample on a set, which Python 3.11+ rejects
    srcs = "/work/src/azure-cli:/work/src/azure-cli-core:/work/src/azure-cli-telemetry:/work/src/azure-cli-testsdk"
    return {"image": "python:3.10-bookworm", "env": {"PYTHONPATH": srcs, "AZURE_CLI_TEST_DEV_SP_NAME": "x"},
            "setup": PY_BASE.format(apt="") +
            "cd /work; grep -v -E '^azure-cli(-core|-telemetry)?==' src/azure-cli/requirements.py3.Linux.txt > /tmp/req.txt; "
            + UV + "-r /tmp/req.txt pytest pytest-xdist; "
            # install the four local packages (non-editable copies, for their metadata); the code is
            # imported from /work through PYTHONPATH, which comes first on sys.path
            "for p in azure-cli-telemetry azure-cli-core azure-cli-testsdk azure-cli; do "
            "rm -rf /tmp/pk-$p; cp -r /work/src/$p /tmp/pk-$p; " + UV + "/tmp/pk-$p; done",
            # -n 8: azure-cli #32298's test file holds ~800 recorded scenario tests (~70 min serially, over the
            # 30-minute stage-1 limit); the same tests run in 8 worker processes
            "pytest": "python -m pytest -p no:randomly -o addopts='' -n 8"}


def azure_sdk(meta, tree):
    if meta["id"] in PLAYBACK_PRS:
        return azure_sdk_playback(meta, tree)
    parts = meta["runnable_tests"][0].split("/")
    pkg = "/".join(parts[:3] if parts[0] == "sdk" else parts[:2])  # sdk/<service>/<package>, tools/<package>
    return {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": f"/work/{pkg}"},
            "setup": PY_BASE.format(apt="") +
            f"cd /work/{pkg}; "
            # dev_requirements: local tools are installed from the tree (non-editable); the package under test is
            # installed from a copy (dependencies and metadata) and imported from /work through PYTHONPATH.
            # (An editable install breaks when a dev requirement pulls the released package from PyPI: its files
            # then shadow the editable finder.)
            "if [ -f dev_requirements.txt ]; then sed -e 's#^-e ##' dev_requirements.txt > /tmp/dev_req.txt; "
            + UV + "-r /tmp/dev_req.txt; fi; "
            f"rm -rf /tmp/pkgcopy; cp -r /work/{pkg} /tmp/pkgcopy; " + UV + "/tmp/pkgcopy pytest pytest-asyncio "
            "pytest-xdist 'setuptools<81'",
            # devtools_testutils starts a downloaded test-proxy for recorded tests (needs network and a .git dir);
            # "live, not recording" mode skips the proxy: tests that need recordings or a real service fail in
            # every run and so never count; tests that use mocks run normally
            "pytest": "export AZURE_TEST_RUN_LIVE=true AZURE_SKIP_LIVE_RECORDING=true; "
                      "python -m pytest -p no:randomly --continue-on-collection-errors"}


# PRs whose recorded tests run offline in playback (see azure_sdk_playback and env-notes-python.md, "40615 repair")
PLAYBACK_PRS = {"Azure__azure-sdk-for-python-40615"}
ASSETS_REPO = "https://github.com/Azure/azure-sdk-assets"


def azure_sdk_playback(meta, tree):
    """azure-sdk recipe with the test-proxy in playback mode, no network at test time.

    Build (network on): every package that holds a changed test file is installed (dev requirements, then the
    package from a copy; code imported from /work via PYTHONPATH, as in azure_sdk); the standalone test-proxy at
    the tree's pinned version goes to /opt/test-proxy; the azure-sdk-assets tags named by the packages' assets.json
    go into a local mirror /opt/assets-mirror.git, and git rewrites the assets-repo URL to that mirror, so the
    proxy's own restore (git clone + checkout of the tag) works offline.
    Recordings are those of the merge commit's assets.json: where the PR moved a tag, the base tag name in the
    mirror points at the merge tag's commit. The base tree and an agent's tree (base assets.json) then play back
    the same recordings as the merge tree; otherwise the PR's new recorded tests would fail at base with
    "recording not found" rather than on behaviour. (#40615: the merge blob tag only adds the 4 recordings of the
    new test_transports*.py tests; the other recordings are byte-identical.)
    Box start (prepare): the proxy starts on http://localhost:5000 with /work as storage root; devtools_testutils
    and the proxy both look for a `.git` entry to find the repo root, so an empty one is made if the tree has none
    (.assets, .certificate and .proxy are git-ignored in this repo).
    """
    merge = Path(tree).parent / "merge"
    pkgs = sorted({"/".join(f.split("/")[:3]) for f in meta["runnable_tests"]})  # sdk/<service>/<package>
    tags, alias = set(), {}
    for p in pkgs:
        b = json.loads((Path(tree) / p / "assets.json").read_text(encoding="utf-8"))["Tag"]
        m = json.loads((merge / p / "assets.json").read_text(encoding="utf-8"))["Tag"]
        tags.add(m)
        if b != m:
            alias[b] = m
    fetch = " ".join(f"refs/tags/{t}:refs/tags/{t}" for t in sorted(tags))
    aliases = "".join(f"git -C /opt/assets-mirror.git tag -f {b} {m}; " for b, m in sorted(alias.items()))
    deps = "".join(f"cd /work/{p}; sed -e 's#^-e ##' dev_requirements.txt > /tmp/dev_req.txt; "
                   + UV + "-r /tmp/dev_req.txt; " for p in pkgs)
    copies = " ".join(f"/tmp/pkgcopy/{p.split('/')[-1]}" for p in pkgs)
    return {"image": "python:3.12-bookworm",
            "env": {"PYTHONPATH": ":".join(f"/work/{p}" for p in pkgs), "AZURE_TEST_RUN_LIVE": "false",
                    "PROXY_URL": "http://localhost:5000", "PROXY_MANUAL_START": "true"},
            "setup": PY_BASE.format(apt="") + deps +
            "rm -rf /tmp/pkgcopy; mkdir -p /tmp/pkgcopy; "
            + "".join(f"cp -r /work/{p} /tmp/pkgcopy/; " for p in pkgs)
            + UV + copies + " pytest pytest-asyncio pytest-xdist 'setuptools<81'; "
            # test-proxy: the version devtools_testutils would download for this tree
            "cd /work; V=$( (cat eng/target_proxy_version.txt 2>/dev/null || cat eng/common/testproxy/target_version.txt) | tr -d '[:space:]'); "
            "mkdir -p /opt/test-proxy; curl -sSfL -o /tmp/tp.tgz https://github.com/Azure/azure-sdk-tools/releases/"
            "download/Azure.Sdk.Tools.TestProxy_$V/test-proxy-standalone-linux-x64.tar.gz; "
            "tar xzf /tmp/tp.tgz -C /opt/test-proxy; rm /tmp/tp.tgz; echo \"test-proxy $V\"; "
            # recordings: full history of the needed tags (a shallow mirror makes the proxy's filtered clone hang);
            # git also auto-follows the older tags in that history (a few MB in all)
            "rm -rf /opt/assets-mirror.git; git init -q --bare /opt/assets-mirror.git; "
            f"git -C /opt/assets-mirror.git fetch -q {ASSETS_REPO} {fetch}; " + aliases +
            "git -C /opt/assets-mirror.git tag -l; "
            f"git config --system url.file:///opt/assets-mirror.git.insteadOf {ASSETS_REPO}",
            "prepare": "[ -e /work/.git ] || mkdir /work/.git; cd /tmp; "
                       "setsid nohup /opt/test-proxy/Azure.Sdk.Tools.TestProxy start --storage-location=/work "
                       "-- --urls http://localhost:5000 > /tmp/proxy.log 2>&1 < /dev/null & "
                       "for i in $(seq 60); do curl -sf http://localhost:5000/Info/Available > /dev/null && break; "
                       "sleep 1; done; curl -sf http://localhost:5000/Info/Available > /dev/null || echo 'proxy down'",
            # one pytest session per package, junit reports merged: the packages' test folders share module
            # names (test_helpers_async, settings.testcase), which one session cannot import side by side
            "pytest": "python /opt/py_pytest_per_package.py -p no:randomly --continue-on-collection-errors"}


def streamlit(meta, tree):
    # The e2e_playwright tests need a browser, a built frontend and a git checkout (image snapshots); they are
    # left out of the pytest command. Their presence also breaks the lib tests run in the same session.
    return {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": "/work/lib"},
            "setup": PY_BASE.format(apt="") +
            "cd /work; " + UV + "-r lib/test-requirements.txt grpcio-tools mypy-protobuf 'setuptools<81' wheel; "
            # streamlit's own dependencies and metadata come from a copy; the code is imported from /work/lib
            + "cp -r /work/lib /tmp/lib; " + UV + "/tmp/lib",
            # generated, git-ignored protobuf modules (the Makefile's `protobuf` target, python half)
            "prepare": "cd /work && python -m grpc_tools.protoc --proto_path=proto --python_out=lib "
                       "proto/streamlit/proto/*.proto > /tmp/protoc.log 2>&1 || echo 'protoc failed'",
            "pytest": ("python -c 'import sys, pytest; a = [x for x in sys.argv[1:] if not x.startswith(\"e2e_playwright\")]; "
                       "sys.exit(pytest.main([\"-p\", \"no:randomly\", \"-o\", \"addopts=\", "
                       "\"--continue-on-collection-errors\"] + a) if any(x.endswith(\".py\") for x in a) else 5)'")}


def weblate(meta, tree):
    apt = ("gettext git-svn subversion postgresql libxml2-dev libacl1-dev liblz4-dev libzstd-dev libxxhash-dev "
           "libxmlsec1-dev libsasl2-dev libldap2-dev libssl-dev libffi-dev libgirepository-2.0-dev libcairo2-dev "
           "gir1.2-rsvg-2.0 gir1.2-pango-1.0 libleptonica-dev libtesseract-dev libpq-dev")
    return {"image": "python:3.13-trixie",
            "env": {"PATH": "/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "PYTHONPATH": "/work", "DJANGO_SETTINGS_MODULE": "weblate.settings_test",
                    "CI_DATABASE": "postgresql", "CI_DB_HOST": "127.0.0.1", "CI_DB_USER": "postgres",
                    "UV_PROJECT_ENVIRONMENT": "/opt/venv"},
            "setup": PY_BASE.format(apt=apt) +
            # the project's own lock file (what its CI installs); the project itself is imported from /work
            "cd /work; export UV_PROJECT_ENVIRONMENT=/opt/venv; "
            "uv sync --frozen --all-extras --dev --no-install-project --no-binary-package lxml "
            "--no-binary-package xmlsec -q; "
            "for f in /etc/postgresql/*/main/pg_hba.conf; do sed -i -E 's/(peer|scram-sha-256|md5)$/trust/' $f; done",
            "prepare": "service postgresql start > /tmp/pg.log 2>&1; for i in $(seq 30); do "
                       "pg_isready -q -h 127.0.0.1 && break; sleep 1; done; pg_isready -h 127.0.0.1 || echo 'pg down'",
            "pytest": "python -m pytest -p no:randomly -o addopts='--reuse-db' -p no:cacheprovider"}


def onnxscript(meta, tree):
    return {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": "/work"},
            "setup": PY_BASE.format(apt="") +
            # runtime deps from pyproject.toml plus the test dependencies of noxfile.py (torch is left out: the
            # drawn PRs' tests do not need it, see env-notes-python.md)
            "cd /work; " + UV + "-r pyproject.toml onnx onnxruntime numpy ml-dtypes beartype expecttest hypothesis "
            "parameterized psutil pytest pytest-subtests pytest-xdist pyyaml packaging 'typing_extensions>=4.10'",
            "pytest": "python -m pytest -p no:randomly -o addopts='' --continue-on-collection-errors"}


def meltano(meta, tree):
    return {"image": "python:3.12-bookworm",
            "env": {"PATH": "/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "PYTHONPATH": "/work/src", "UV_PROJECT_ENVIRONMENT": "/opt/venv"},
            "setup": PY_BASE.format(apt="libpq-dev") +
            # the project's lock file; the project itself is installed from a copy (for its metadata) and
            # imported from /work/src through PYTHONPATH
            "cd /work; export UV_PROJECT_ENVIRONMENT=/opt/venv; uv sync --frozen --group testing --no-install-project -q; "
            "rm -rf /tmp/mt; cp -r /work /tmp/mt; uv pip install -q --python /opt/venv/bin/python --no-deps /tmp/mt; "
            "rm -rf /tmp/mt",
            "pytest": "python -m pytest -p no:randomly --continue-on-collection-errors"}


def supervisor(meta, tree):
    return {"image": "python:3.13-bookworm", "env": {"PYTHONPATH": "/work"},
            "setup": PY_BASE.format(apt="libudev-dev libffi-dev libssl-dev libyaml-dev libpulse0 libglib2.0-0") +
            # linters/type checkers/pre-commit are not needed to run the tests (and mypy pins can vanish)
            "cd /work; grep -v -E '^(astroid|mypy|pre-commit|pylint|ruff|types-)' requirements_tests.txt > /tmp/req_test.txt; "
            + UV + "-r requirements.txt -r /tmp/req_test.txt",
            # no .pyc writing: blockbuster flags pytest's assertion-rewrite cache writes inside the event loop
            "pytest": "PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:randomly -o addopts='' --continue-on-collection-errors"}


def superset(meta, tree):
    return {"image": "python:3.11-bookworm", "env": {"PYTHONPATH": "/work:/work/superset-core/src",
                                                     "SUPERSET_TESTENV": "true"},
            "setup": PY_BASE.format(apt="libsasl2-dev libldap2-dev libpq-dev default-libmysqlclient-dev libffi-dev "
                                        "libssl-dev libecpg-dev") +
            # the project's pinned development requirements; the local (-e) packages are installed from copies
            # for their metadata and imported from /work through PYTHONPATH
            "cd /work; grep -v -E '^-e ' requirements/development.txt > /tmp/req_dev.txt; "
            + UV + "-r /tmp/req_dev.txt; "
            "for p in superset-core; do rm -rf /tmp/pk; cp -r /work/$p /tmp/pk; " + UV + "--no-deps /tmp/pk; done",
            "pytest": "python -m pytest -p no:randomly --continue-on-collection-errors"}


def sentry(meta, tree):
    # copy of the recipe in env.py, with py_sentry_extras.py (environment-setting lines go to /opt/py_envs.sh);
    # the pilot PRs keep env.py's original recipe untouched
    if meta["id"] in ("getsentry__sentry-python-5046", "getsentry__sentry-python-4869"):
        return {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": "/work"},
                "setup": PY_BASE.format(apt="") +
                "cd /work; python /opt/sentry_extras.py > /tmp/extras.txt; cat /tmp/extras.txt; "
                + UV + "-r requirements-testing.txt -r /tmp/extras.txt . ; pip uninstall -y -q sentry-sdk || true",
                "pytest": "python -m pytest -o addopts=''"}
    pg = any("integrations/django" in f for f in meta["runnable_tests"])  # the Django test app also uses PostgreSQL
    r = {"image": "python:3.12-bookworm", "env": {"PYTHONPATH": "/work"},
         "setup": PY_BASE.format(apt="postgresql libpq-dev" if pg else "") +
         "cd /work; python /opt/py_sentry_extras.py > /tmp/extras.txt; cat /tmp/extras.txt; "
         + UV + "-r requirements-testing.txt -r /tmp/extras.txt . ; pip uninstall -y -q sentry-sdk || true",
         "pytest": "[ -f /opt/py_envs.sh ] && . /opt/py_envs.sh; python -m pytest -o addopts=''"}
    if pg:
        r["setup"] += ("; for f in /etc/postgresql/*/main/pg_hba.conf; do "
                       "sed -i -E 's/(peer|scram-sha-256|md5)$/trust/' $f; done")
        r["prepare"] = ("service postgresql start > /tmp/pg.log 2>&1; for i in $(seq 30); do "
                        "pg_isready -q -h 127.0.0.1 && break; sleep 1; done; pg_isready -h 127.0.0.1 || echo 'pg down'")
    return r


RECIPES = {
    "getsentry/sentry-python": sentry,
    "apache/superset": superset,
    "home-assistant/supervisor": supervisor,
    "meltano/meltano": meltano,
    "microsoft/onnxscript": onnxscript,
    "WeblateOrg/weblate": weblate,
    "streamlit/streamlit": streamlit,
    "Azure/azure-cli": azure_cli,
    "Azure/azure-sdk-for-python": azure_sdk,
}
