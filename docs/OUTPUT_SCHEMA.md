# Output schema and stability contract

`schema_version` is `1.0`. A field addition bumps the minor version. A field
removal or a meaning change bumps the major version. `proveit diff` refuses to
trust two receipts with different major versions and records a Note.

## Streams

- stdout carries exactly one report document.
- stderr carries errors only. Progress messages never appear on stdout.
- With `-o FILE`, stdout stays empty and the report goes to the file.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success. No contradicted claim, no added risk capability. |
| 1 | At least one CONTRADICTED claim, or a new risk capability in `diff`, or a failed `selftest` check. |
| 2 | Operational error: bad root, invalid limit, unwritable output, internal error. |
| 3 | No contradictions, but UNVERIFIABLE claims exist and `--fail-unverifiable` was set. |

`diff --allow-risk` returns 0 even when capabilities were added.

## Resource budgets and scan scope

`--max-file-bytes`, `--max-total-bytes`, `--max-files`, `--max-line-chars`,
`--max-claims` and `--max-evidence` override the default hard ceilings.
Hitting a budget produces a warning Note, sets `scan_complete: false`, and
moves every negative claim to UNVERIFIABLE. A claim budget emits exactly one
`claim_budget` Note.

`--exclude RELATIVE_PATH` is different. It is a deliberate narrowing of the
declared scope: the excluded path appears as a `note`-level `excluded_path`
entry and in every verdict's limitations, while `scan_complete` stays true.
VERIFIED then means "no contradicting capability within the scope the caller
chose". `docs/CLAIM_ONTOLOGY.md` states the same distinction.

## `scan` / `check` receipt object

```json
{
  "schema_version": "1.0",
  "tool": "proveit",
  "root": ".",
  "scan_complete": true,
  "scanned_files": 19,
  "scanned_bytes": 84123,
  "capabilities": ["manifest.license"],
  "evidence": [
    {
      "path": "app.py",
      "line": 7,
      "column": 5,
      "capability": "network.http",
      "rule_id": "R_NET_HTTP_PY",
      "snippet": "    return requests.get(url)"
    }
  ],
  "notes": [
    {
      "severity": "warning",
      "code": "oversize",
      "path": "assets/big.bin",
      "message": "file exceeds per-file size budget"
    }
  ],
  "manifests": [
    {
      "path": "pyproject.toml",
      "kind": "python",
      "license": "MIT",
      "dependencies": [],
      "incomplete": false
    }
  ]
}
```

`line: 0` and `column: 0` mark a file-level fact. Root manifests and LICENSE
matches use this convention because their fields can span several lines.

`snippet` is sanitised: control characters, ANSI escapes, bidi overrides and
zero-width characters are removed, and the value is truncated to 160
characters.

## `check` report

```json
{
  "schema_version": "1.0",
  "tool": "proveit",
  "root": ".",
  "counts": {"VERIFIED": 4, "CONTRADICTED": 0, "UNVERIFIABLE": 1},
  "claims": [
    {
      "claim_id": "C0001",
      "kind": "no_telemetry",
      "argument": "",
      "text": "No telemetry.",
      "path": "README.md",
      "line": 5,
      "polarity": "absence",
      "scope": "analytics SDKs and event calls within scan scope",
      "qualified": false
    }
  ],
  "verdicts": [
    {
      "claim": { "...": "same object as above" },
      "state": "VERIFIED",
      "reason": "No contradicting capability was found in any in-scope source file, and the scan covered every eligible file.",
      "evidence": [],
      "limitations": ["Static evidence only; proveit never runs the target program."]
    }
  ],
  "receipt": { "...": "receipt object" }
}
```

`counts` always contains all three states, including zeros. `evidence` inside
a CONTRADICTED verdict is non-empty. `limitations` is a sorted, deduplicated
list of strings.

## `diff` report

```json
{
  "schema_version": "1.0",
  "tool": "proveit",
  "left_root": "left",
  "right_root": "right",
  "left_complete": true,
  "right_complete": true,
  "added_capabilities": ["network.http"],
  "removed_capabilities": [],
  "changes": [
    {
      "change": "added",
      "capability": "network.http",
      "path": "app.py",
      "line": 7,
      "rule_id": "R_NET_HTTP_PY",
      "snippet": "    return requests.get(url)"
    }
  ],
  "notes": []
}
```

A change is keyed by capability, path, line, column and rule id. The snippet
is deliberately excluded from the key, so reformatting a line does not create
a new capability. Re-indenting a line does change the column and appears as
one removal plus one addition; that is intentional and documented.

## `selftest` report

`ok` is a boolean. `checks` is a list of `{name, passed, detail}`.
`excluded_paths` names every path removed from the self-scan. `counts`,
`capabilities`, `scan_complete`, `verified_claims`, `contradicted_claims` and
`unverifiable_claims` summarise the underlying audit.

## SARIF 2.1.0

`check` and `diff` support `--format sarif`. Each claim becomes a SARIF
result with a `ruleId` equal to the claim kind, a `level` derived from the
state, and a `partialFingerprints` entry holding the claim id. Limitations are
appended to the SARIF message so a code-scanning consumer sees the scope.

## Determinism

Two runs on the same tree with the same limits, exclusions and tool version
produce byte-identical JSON. No timestamps, absolute paths, random values,
hash-order-dependent iteration or environment-derived fields appear in the
output. Evidence, notes, manifests, changes and limitations are sorted before
serialisation. `ensure_ascii=False` keeps non-ASCII text readable while the
JSON encoder still escapes control characters.

## Markdown rendering

Repository-derived strings pass through `proveit/sanitize.py` before they
reach a Markdown table. `&`, `<`, `>`, `|`, backticks, `*`, `_`, `[` and `]`
are escaped. Long note and change lists are truncated with an explicit
pointer to `--format json` for the complete data.
