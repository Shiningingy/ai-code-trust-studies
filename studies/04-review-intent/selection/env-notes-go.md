# Go environments for the main draw

Recipes: `scripts/recipes_go.py` (consulted by `env.recipe` before its defaults); helper `scripts/env_helpers/go_shim.sh`.
Status: `runs/main_setup_go.json`. All repos use `golang:<go.mod version>-bookworm`, `GOFLAGS=-mod=mod -trimpath`,
`GOTOOLCHAIN=auto`, `go mod download`, then a warm build cache made in a /tmp copy (never in /work).

Shared parts of `build()` in recipes_go.py
- Warm-up compiles only the packages under test (`go test -run '^$' <pkgs>`); `go build ./...` only for the small repos (celestia-app, atmos, volcano).
- go_shim.sh is installed as /go/bin/go (ahead of the real go) for (a) nested modules and (b) zeta-chain. It enters the module that owns each `./pkg` argument (stage1 runs `go test ./pkg` from /work, which Go refuses across a module boundary), and it drops `./pkg` arguments whose directory does not exist (a package the PR deleted; without this `go test` prints "directory not found" and runs nothing, so every test of the merge run is lost). Used by: Azure, cosmos-sdk (store/), google-cloud-go (internal/librariangen), zeta-chain. Other images were built without it (no nested module, no deleted test package in the PR).
- A go.work was tried first for nested modules and abandoned: cosmos store failed with an ambiguous-import error under workspace mode that module mode does not have, and `-mod=mod` is illegal in workspace mode.

Per repo
- Azure/azure-sdk-for-go: no root go.mod; each test file's module is its own (eng/tools/generator, sdk/messaging/azservicebus, sdk/azidentity ...). Shim + `GOWORK=off` (sdk/azidentity ships its own go.work). If the module has live_test.go (azidentity) `AZURE_RECORD_MODE=live`: its TestMain otherwise starts the test proxy, which downloads a binary and restores recordings from GitHub (no network at test time) and panics before any test runs.
- ava-labs/avalanchego, celestiaorg/celestia-app, cloudposse/atmos, volcano-sh/volcano, zeta-chain/node: default recipe (zeta also with the shim).
- cosmos/cosmos-sdk: the tests are in the nested module `store/`; shim.
- googleapis/google-cloud-go: tests in nested module internal/librariangen; the root go.work lists ~300 modules and forbids -mod=mod, so `GOWORK=off` plus the shim.
- grafana/mimir: dependencies are vendored: `GOFLAGS=-mod=vendor -trimpath`.
- pingcap/tidb: `-tags=intest` added to GOFLAGS; testkit.NewTestKit refuses to run without it (the Makefile passes it). Without it every integration test fails at both commits.
- gruntwork-io/terragrunt, zitadel/zitadel: see end of file.

Excluded (evidence)
- volcano-sh/volcano#4354, pingcap/tidb#63878, ava-labs/avalanchego#4259: check 3. The selected tests compile and pass at base + PR tests (base results 24, 13, 96, all pass, EXIT=0), so no test goes from fail to pass (refactors/tests that already held).
- zeta-chain/node#4153, #4192, #4203, #4330: check 1 (merge diff has files the PR file list lacks, e.g. x/authority/migrations/v3/migrate_test.go, generated proto/typescript files).
- pingcap/tidb#60776: check 4 (B comments 0, C comments 1).

Terragrunt (default recipe in env.py, tofu downloaded at setup) and zitadel
- gruntwork-io/terragrunt#5037, #4794: default recipe, built and ran normally.
- zitadel/zitadel#10384: older layout (no apps/api/project.json). `recipes_go.zitadel` reproduces env.py's recipe for the new layout (checked identical apart from `|| true` on go mod download) and for the old layout takes the generator tools from the Makefile (`go install ...@v` lines, plus the two own plugins protoc-gen-authoption/-zitadel built from internal/protoc), then env_helpers/zitadel_gen.sh as before. The integration_test package needs a database ("setup failed", build tag excludes it) and does not count; the unit tests in internal/api/grpc/session/v2 give 51 F2P.

Notes on stage1 behaviour (not edited)
- go test run in a package list fails entirely when one listed package directory no longer exists at the merge commit (PR deleted it): zeta-chain#3734 lost all results (merge counts 0). Worked around in the image with the shim above, not in stage1.
- Images built before the shim got its deleted-directory rule (everything except zeta#3734 and later builds) do not have it; none of their PRs deletes a test package.
- Not finished: nothing.
