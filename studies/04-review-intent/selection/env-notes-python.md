# Environment notes, Python draw (35 PRs)

Recipes: `scripts/recipes_python.py`; helper `scripts/env_helpers/py_sentry_extras.py`.
Status per PR: `runs/main_setup_python.json`. Nothing here looked at review text or outcomes.

## Per repo

- **home-assistant/core**: env.py's recipe, unchanged (not in recipes_python.py).
- **getsentry/sentry-python**: copy of env.py's recipe with `py_sentry_extras.py`. env.py's `sentry_extras.py` has two bugs for
  non-pilot PRs: (a) tox lines such as `DJANGO_SETTINGS_MODULE=...` / `TESTPATH=...` were written into the requirements file
  (uv parse error); (b) a test directory without a tox entry (stdlib, unraisablehook) was added as a package name.
  The copy sends env lines to `/opt/py_envs.sh` (sourced in the pytest prefix) and drops (b). Django test app needs
  PostgreSQL: installed via apt, trust auth, started in `prepare`. Pilot PRs keep the original recipe.
- **Azure/azure-cli**: Python 3.10 (pinned jmespath 0.9.5 breaks on 3.11+), pinned `requirements.py3.Linux.txt` minus the four
  local packages; the local packages are installed from copies (metadata), code imported via PYTHONPATH.
  Tests are recorded (vcr) scenario tests; live-only and service-principal tests skip.
- **Azure/azure-sdk-for-python**: package dir derived from the test path; `dev_requirements.txt` (without `-e`), package installed
  from a copy, code via PYTHONPATH (editable installs broke when a dev requirement pulled the released package from PyPI).
  `AZURE_TEST_RUN_LIVE=true AZURE_SKIP_LIVE_RECORDING=true` in the pytest prefix: the test-proxy (downloaded binary, needs git/network)
  is skipped, so recording-dependent tests fail in every run and never count; mock-based tests run.
- **WeblateOrg/weblate**: python 3.13-trixie, `uv sync --frozen` from the project's lock file (as its CI), apt packages from `ci/apt-install`,
  local PostgreSQL (trust auth) started in `prepare`.
- **apache/superset**: python 3.11, pinned `requirements/development.txt` without `-e` lines, `superset-core` from a copy, code via PYTHONPATH.
- **home-assistant/supervisor**: python 3.13, requirements + test requirements (no linters), libpulse0 etc.
  `PYTHONDONTWRITEBYTECODE=1` because blockbuster flags pytest's .pyc writes inside the event loop.
- **meltano/meltano**: `uv sync --frozen --group testing` (lock file), project metadata from a copy, code via PYTHONPATH.
- **microsoft/onnxscript**: deps from pyproject.toml plus noxfile test deps; torch left out (drawn tests do not need it).
  Snapshots of both PRs were created with `git archive` because `git checkout` of the tree failed on the Windows host
  ("unable to unlink testdata"); same commits, `.tree-ok` written, prepare.py unchanged.
- **streamlit/streamlit**: protobuf modules generated in `prepare` (grpc_tools.protoc); package installed from a copy for metadata.
  The pytest prefix drops `e2e_playwright/...` arguments (browser, built frontend and git checkout needed; and running them in the
  same session made the lib tests error). PRs whose only changed tests are e2e therefore have no F2P.

## Excluded

See `runs/main_setup_python.json`. Evidence:
- sentry-python-4873: check 4, review_B has 0 comments (count from checks.json).
- streamlit-11690: only e2e_playwright tests changed; none runnable here (check 3).
- streamlit-12074: lib test change (config_test) is a value change that passes at base too: 56 P2P, 0 F2P (check 3).
- azure-sdk-for-python-41742 (cosmos): `tests/conftest.py` connects to a live Cosmos DB endpoint at import
  (Connection refused); 0 tests collected in base and merge. Needs the Cosmos emulator or an account (check 2 in spirit).

## Shared-code observations (not edited)
- env.py's sentry recipe uses `sentry_extras.py` with the two bugs above.
- stage1 skips the whole run when `tests.json` exists; after changing a recipe delete tests.json and the image.
- prepare.export_tree fails on onnxscript on Windows (see above).

## Additional exclusions and open items (final)
- azure-sdk-for-python-40615 (storage-blob): recorded tests need the test-proxy plus recordings from the azure-sdk-assets repo (network at
  test time; the proxy also needs a `.git` entry in the tree). Without them 22 tests fail with AzureSigningError and 4 modules fail to collect in every run.
  Recorded as check 2. Fixing it would need the proxy binary and restored `.assets` baked into the image and a fake `.git` in each box.
- azure-sdk-for-python-41742 (cosmos): see above, recorded as check 2.
- azure-cli-32115: the new test (`test_aks_create_no_ssh_key`) replays from its recording and passes at base too (242 tests ran, 171 P2P): genuine check 3.
- **Not finished: azure-cli-32298** (vm `test_vm_commands.py`, ~800 recorded scenario tests). The image builds and tests run
  correctly, but a run needs more than stage1's 30-minute TEST_TIMEOUT (41% done at 28 min), so junit is never written.
  Left out of ok and excluded. Needs either a longer TEST_TIMEOUT in stage1.py or an exclusion by the lead ("tests do not finish in 30 min").
- Image notes: azure-sdk images keep `PYTHONPATH=/work/<pkg>`; streamlit/onnx/meltano etc. as described above.
