"""Go environment recipes for the main draw (see selection/env-notes-go.md).

env.py consults RECIPES (owner/repo -> function(meta, tree) -> recipe dict) before its defaults. Every recipe here
is built by `build()`, which differs from the default in three ways:
  * it finds the go.mod nearest to each changed test file. If any is not the root module (cosmos-sdk store/,
    google-cloud-go internal/librariangen, every azure-sdk-for-go module, which has no root go.mod), the image gets
    env_helpers/go_shim.sh as /go/bin/go, so that stage1's `go test ./path/to/pkg` from /work runs inside the
    module that owns the package (a go.work was tried first and failed: cosmos store hit an ambiguous-import
    error that module mode with -mod=mod does not have).
  * the warm-up compiles only the packages under test (`go test -run '^$' <pkgs>`), not `go build ./...`.
  * optional per-repo `pre` (bash, before the warm-up), `env`, `flags`.
"""
import re
from pathlib import Path


def _gover(modfile):
    m = re.search(r"^go (\d+)\.(\d+)(?:\.(\d+))?", Path(modfile).read_text(encoding="utf-8"), re.M)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)) if m else (1, 22, 0)


def modules(meta, tree):
    """Relative dirs ('.' for root) of the modules that contain the PR's runnable test files."""
    tree = Path(tree)
    mods = set()
    for t in meta["runnable_tests"]:
        p = (tree / t).parent
        while True:
            if (p / "go.mod").exists():
                mods.add(p.relative_to(tree).as_posix() if p != tree else ".")
                break
            if p == tree:
                break
            p = p.parent
    return sorted(mods)


def build(meta, tree, *, pre="", flags="-mod=mod -trimpath", env=None, warm_all=False, image=None, shim=False, warm_pre="", warm_post="", prepare=None):
    tree = Path(tree)
    mods = modules(meta, tree) or ["."]
    ver = max(_gover(tree / m / "go.mod") for m in mods)
    pkgs = " ".join(sorted({"./" + str(Path(f).parent).replace("\\", "/") for f in meta["runnable_tests"]}))
    ws = mods != ["."]
    e = {"GOTOOLCHAIN": "auto", "GOFLAGS": flags}
    e.update(env or {})
    setup = "set -e; cd /work; " + "".join(f"export {k}='{v}'; " for k, v in e.items())
    if ws or shim:
        # /go/bin/go becomes a shim: enters the module owning each ./pkg argument (nested modules) and drops
        # ./pkg arguments whose directory the PR deleted (see env_helpers/go_shim.sh)
        setup += "install -m755 /opt/go_shim.sh /go/bin/go; hash -r; "
    if ws:
        setup += "".join(f"(cd /work/{m} && go mod download); " for m in mods)
    else:
        setup += "go mod download || true; "
    setup += pre
    build_all = "go build ./... || true; " if (warm_all and not ws) else ""
    setup += ("rm -rf /tmp/w; cp -r /work /tmp/w; cd /tmp/w; " + warm_pre + build_all +
              f"go test -count=1 -run '^$' {pkgs} || true; " + warm_post + "cd /; rm -rf /tmp/w")
    r = {"image": image or f"golang:{ver[0]}.{ver[1]}-bookworm", "env": e, "setup": setup}
    if prepare:
        r["prepare"] = prepare
    return r


def default(meta, tree):
    return build(meta, tree, warm_all=True)


def with_shim(meta, tree):
    return build(meta, tree, shim=True)


def azure(meta, tree):
    # some modules carry their own go.work (sdk/azidentity); -mod=mod is illegal in workspace mode
    env = {"GOWORK": "off"}
    tree = Path(tree)
    if any((tree / m / "live_test.go").exists() for m in modules(meta, tree)):
        # TestMain of these modules starts the Azure test proxy and restores recordings from GitHub (no network
        # in test containers) unless the record mode is live: live mode runs the offline tests, and tests that
        # need real Azure fail at both commits and do not count
        env["AZURE_RECORD_MODE"] = "live"
    return build(meta, tree, env=env)


def only_pkgs(meta, tree):
    return build(meta, tree)


def mimir(meta, tree):
    # the repo vendors its dependencies: use them, no download needed
    return build(meta, tree, flags="-mod=vendor -trimpath")


def tidb(meta, tree):
    # tidb's testkit refuses to run without the `intest` build tag (the Makefile passes --tags=intest)
    return build(meta, tree, flags="-mod=mod -trimpath -tags=intest")


def gcloud(meta, tree):
    # the repo root has a go.work listing ~300 modules and -mod=mod is illegal in workspace mode: work per module
    return build(meta, tree, env={"GOWORK": "off"})


def zitadel(meta, tree):
    """Same as env.py's zitadel recipe for the new layout (apps/api/project.json lists the generator tools);
    older trees (no apps/api) take the tool list from the Makefile instead. Generation itself is
    env_helpers/zitadel_gen.sh in both cases."""
    gen = "bash /opt/zitadel_gen.sh /tmp/w; "
    prep = "bash /opt/zitadel_gen.sh /work > /tmp/gen.log 2>&1 || echo 'generation failed'"
    if (Path(tree) / "apps/api/project.json").exists():
        pre = ("mkdir -p /opt/zbin; grep -o 'go install [^\"]*' apps/api/project.json | sed 's/\\\\u0027//g' | "
               "sort -u | while read -r cmd; do (cd /work && GOBIN=/opt/zbin $cmd) || echo \"failed: $cmd\"; done; ")
    else:
        pre = ("mkdir -p /opt/zbin; grep -oE 'go install [^ 	#]+@v[0-9.]+' Makefile | sort -u | "
               "while read -r cmd; do (cd /tmp && GOFLAGS= GOBIN=/opt/zbin $cmd) || echo \"failed: $cmd\"; done; "
               "(cd /work && go build -o /opt/zbin/protoc-gen-authoption ./internal/protoc/protoc-gen-authoption && "
               "go build -o /opt/zbin/protoc-gen-zitadel ./internal/protoc/protoc-gen-zitadel) || echo 'failed: own plugins'; ")
    return build(meta, tree, pre=pre, warm_all=True, warm_pre=gen, prepare=prep)


RECIPES = {
    "zitadel/zitadel": zitadel,
    "Azure/azure-sdk-for-go": azure,
    "ava-labs/avalanchego": only_pkgs,
    "celestiaorg/celestia-app": default,
    "cloudposse/atmos": default,
    "cosmos/cosmos-sdk": only_pkgs,
    "googleapis/google-cloud-go": gcloud,
    "grafana/mimir": mimir,
    "pingcap/tidb": tidb,
    "volcano-sh/volcano": default,
    "zeta-chain/node": with_shim,
}
