# Changelog

## 1.0.1

Accuracy and scope-hardening release. No schema change; `schema_version`
stays `1.0`.

- Fixed three false CONTRADICTED sources: a capability name inside a
  single-line string literal, inside an inline comment, and inside a
  triple-quoted docstring. A per-line string mask now marks quoted spans,
  backtick runs and multi-line docstrings; rule matching only accepts hits
  that start on unmasked code.
- A masked first occurrence no longer hides a real call later on the same
  line. `Rule.find` now scans every occurrence and returns the leftmost
  acceptable one.
- `#[link(...)` in Rust is no longer mistaken for a comment, so native code
  loading is detected again.
- The claim budget now emits exactly one Note instead of one per remaining
  line.
- Added `--max-claims` and `--max-evidence` so coverage degradation can be
  reproduced from the CLI.
- Clarified the contract: `--exclude` is deliberate scope narrowing and is
  disclosed; automatic skips and exhausted budgets set `scan_complete: false`.
- 71 tests, up from 50. Review rounds 10-12 documented.

All 1.0.0 golden outputs are unchanged at the verdict level: `check .`
7/0/1, clean 4/0/1, dirty 0/4/1, diff 5 added capabilities. Two reason
strings now report one fewer contradicting capability because a dependency
name inside `pyproject.toml` is no longer counted as a telemetry call. The
README demo was re-copied from the new output.

## 1.0.0

First release.

- `scan`, `check`, `diff`, `selftest` and `ontology` commands.
- Nine claim kinds, three-state verdicts, capability receipts, version diffs.
- JSON, Markdown and SARIF output. Stable exit codes 0/1/2/3.
- Fifty regression and adversarial tests.
- Nine documented review rounds.
- Bundled skill catalogues and research reports under `third_party/`.

### Known limits

Static analysis only. `no_binary` is UNVERIFIABLE by design. Conditional
claims are UNVERIFIABLE. Excluded paths are disclosed but cannot be hidden
from a determined caller.
