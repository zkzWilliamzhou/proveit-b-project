# Security policy

Report a vulnerability through a private GitHub security advisory. Include a
reproduction, the affected version and the impact. Hold exploit details out of
public issues until a fix ships.

Supported versions: `1.0.x`.

## Trust boundary

`proveit` treats every scanned repository as hostile input. It reads file
bytes as data, applies fixed size, depth, line, entry and total-byte budgets
before decoding, and rejects symbolic links and non-regular files. It does
not build, install, import, evaluate or run target content, and it does not
resolve packages or fetch remote metadata. Rule matching uses fixed lowercase
literals on lines bounded by `--max-line-chars`.

The declared scan scope excludes binary assets, vendored dependency
directories, hidden directories other than `.github`, and any path named with
`--exclude`. Each skipped path is recorded as a Note and named in verdict
limitations. A warning Note sets `scan_complete` to false, which moves
negative claims to UNVERIFIABLE.

## What the tool itself contains

`proveit/` imports only the Python standard library. `pyproject.toml`
declares an empty runtime dependency set. `proveit selftest` audits the tool
with its own pipeline and prints every path it excluded from that audit.

## Verification

```console
$ python3 -m unittest discover -s tests -v
$ python3 -m proveit selftest
$ python3 -m proveit check . --format json
```

`tests/test_proveit.py` covers path escapes, symlinks, FIFOs, invalid UTF-8,
oversize files, long lines, terminal escapes, Markdown injection, string and
docstring precision, budget exhaustion, manifest parsing, verdict semantics,
determinism and exit codes. The full threat model is in
`third_party/research/THREAT_MODEL.md`.

## Scope limits

Static analysis misses obfuscated code, dynamically assembled identifiers,
generated sources and behaviour inside dependencies outside the scan scope.
A caller can exclude a path; that exclusion is disclosed but the tool cannot
prevent it. `VERIFIED` describes the declared scan, not all possible inputs.
