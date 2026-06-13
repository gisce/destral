# AGENTS.md - Destral

Destral is the GISCE OpenERP v5 test runner and support library. Treat it as
test infrastructure for the ERP ecosystem, not as an isolated helper package:
small changes here can affect how ERP pull requests select modules, create
databases, install requirements, report coverage, and publish CI results.

## Before changing code

1. Read `README.rst` for the public workflow and supported commands.
2. Read the code path you are touching, especially:
   - `destral/cli.py` for the command-line runner and CI behaviour.
   - `destral/utils.py` for module detection, dependency sorting and addon
     requirements installation.
   - `destral/testing.py` for OpenERP test suites and test case helpers.
   - `destral/openerp.py` for database and OpenERP service lifecycle.
3. Check the current branch and working tree:
   ```bash
   git status --short --branch
   ```
4. Keep changes small and reviewable. This repo is shared infrastructure for
   many ERP modules, so broad refactors need a very clear payoff.

## Core behaviour to preserve

- `destral` supports Python 2.7 and Python 3.x. Avoid f-strings, unguarded type
  annotation syntax, pathlib-only rewrites, and dependencies that dropped
  Python 2 support.
- When `--modules/-m` is not provided, `destral/cli.py` detects modules from
  changed files:
  - In CI, it reads `CI_PULL_REQUEST`, `CI_REPO` and `GITHUB_TOKEN`, fetches the
    pull request diff from GitHub, and extracts paths from that diff.
  - Outside CI, it falls back to `git diff --name-only HEAD~1..HEAD`.
  - `detect_module()` walks each path upward until it finds a directory with a
    `__terp__.py` file.
  - Duplicates are removed. If no module is found, Destral tests `base`.
  - The resulting module list is sorted with `sort_modules_by_dependencies()`
    so dependencies that are also touched run before dependent modules.
- The runner executes server specs first, then for each selected module:
  - optionally installs addon `requirements.txt` and `requirements-dev.txt`
    from dependencies plus the module itself;
  - runs mamba specs if present;
  - sets `DESTRAL_MODULE`;
  - runs the OpenERP unittest suite.
- Database handling is part of the contract:
  - Test runs create temporary PostgreSQL databases unless `OPENERP_DB_NAME` or
    `--database` selects an existing one.
  - `--dropdb` is enabled by default.
  - `--no-dropdb` keeps the database and enables the `admin` user for local
    inspection.
  - Database names are validated and quoted in `destral/openerp.py`; keep that
    boundary tight.
- Coverage and JUnit XML output are CI-facing features. Preserve existing file
  formats and defaults unless the PR explicitly changes the contract.

## Testing expectations

Run the narrowest useful tests first, then broaden if the change touches shared
behaviour.

Pure helper or output changes:

```bash
python -m unittest discover tests
```

Spec and runner behaviour:

```bash
export PYTHONPATH="$(pwd):../erp/server/bin"
mamba spec
```

Lint-sensitive changes:

```bash
python -m pylint destral
```

For changes that affect OpenERP integration, database lifecycle, module
detection, dependency sorting, requirements installation, coverage or JUnit XML,
validate on both supported runtimes when possible:

- Python 2.7, matching the legacy ERP runtime.
- Python 3.11, matching the modern CI path.

If local ERP dependencies are unavailable, state that clearly in the PR and make
sure the code path is covered by unit tests or specs where possible.

## Test style

- Prefer focused regression tests in `tests/` for pure Python helpers.
- Use mamba specs in `spec/` when behaviour is already expressed there or when
  the change is easier to describe as a scenario.
- For OpenERP module tests, prefer `destral.testing.OOTestCaseWithCursor` when a
  cursor and user are needed. It manages the transaction setup and teardown.
- Do not leave transactions, cursors, temporary directories, databases or
  patched globals around after a test.
- Keep tests deterministic and fast. CI installs ERP and oorq, so expensive
  tests multiply quickly.

## Design guidance

- Preserve the CLI contract. Many repos call `destral` from GitHub Actions and
  local scripts with existing flags.
- Keep imports compatible with the ERP server path added through `PYTHONPATH`.
- Prefer explicit environment variables and options over hidden global state.
- Be careful with subprocess calls, network calls and `pip install` execution.
  They are intentional in some paths, but they should stay bounded and visible.
- Avoid swallowing failures from test discovery, module installation, database
  lifecycle and report generation. A false green test run is worse than a noisy
  failure.
- When touching PR-diff module detection, include cases for multi-module PRs,
  non-module paths and dependency ordering. This logic decides what ERP CI
  actually exercises.

## Pull request checklist

- Explain the affected Destral contract in the PR body.
- Mention whether module auto-detection, database lifecycle, coverage or JUnit
  output is affected.
- Include the test commands run, with Python version.
- Keep documentation examples in sync with `README.rst` and `docs/`.
- Do not include secrets, tokens, customer data, generated coverage databases or
  local `.coverage` files.
