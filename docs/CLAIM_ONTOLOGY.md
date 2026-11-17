# Claim ontology

`proveit` does not understand English. It recognises a fixed set of sentences
and maps each one to a fixed set of static capabilities. Anything outside the
list is left alone. Run `proveit ontology --format json` to print the live
table from the code, so this document cannot drift from the implementation.

## Claim sources

By default only root-level `README*`, `SECURITY*`, `PRIVACY*` and
`CONTRIBUTING*` documents count. Fenced code blocks, block quotes and table
rows inside those documents are skipped. `--claim-docs` adds Markdown under
`docs/`. Vendored material in `third_party/` is outside the scan scope.

A sentence carrying a qualifier (`by default`, `unless`, `optional`,
`experimental`, `planned`, `?`, and others listed in `proveit/claims.py`)
becomes UNVERIFIABLE. Conditional promises depend on configuration, not on
source text.

## The nine claim kinds

| Kind | Polarity | Contradicting capabilities | Scope |
|---|---|---|---|
| `no_network` | absence | `network.http`, `network.socket`, `network.download` | runtime source files in scan scope |
| `offline` | absence | the three above plus `telemetry.sdk`, `telemetry.event` | runtime source files and telemetry SDKs |
| `no_telemetry` | absence | `telemetry.sdk`, `telemetry.event` | analytics SDKs and event calls |
| `no_data_egress` | absence | network capabilities plus telemetry capabilities | runtime source files |
| `zero_dependencies` | absence | declared runtime dependencies in root manifests | supported manifests |
| `no_dynamic_exec` | absence | `exec.dynamic`, `exec.shell`, `native.code` | runtime source files |
| `read_only` | absence | `fs.write` | runtime source files |
| `no_binary` | absence | always UNVERIFIABLE | binary assets outside scan scope |
| `license` | presence | a different LICENSE text or a conflicting manifest field | LICENSE file and manifest fields |

`license` takes an argument: MIT, Apache-2.0, BSD-3-Clause, GPL-3.0,
MPL-2.0 or ISC. License identity is a text match against known templates, not
legal advice.

## Advisory capabilities

These appear in receipts and diffs. They never contradict a claim on their
own.

| Capability | Why it is advisory |
|---|---|
| `network.endpoint` | A hard-coded URL may be a schema URI, an error message or documentation. |
| `build.network` | CI install steps are build-time, not runtime behaviour. |
| `env.read` | Reading an environment variable is not exfiltration. |
| `fs.write` | Advisory for most claims; contradicting only for `read_only`. |

## Three-state semantics

- **CONTRADICTED** requires positive Evidence. Every such verdict lists at
  least one file and line (or a root-level manifest fact at `line: 0`).
- **VERIFIED** for a negative claim requires `scan_complete: true`. One
  skipped file, one undecodable byte or one exhausted budget moves the claim
  to UNVERIFIABLE.
- An explicit `--exclude` is a **deliberate narrowing of the declared scan
  scope**, not an accidental coverage loss. It is recorded as a `note`-level
  `excluded_path`, named in every verdict's limitations, and printed in the
  receipt. `scan_complete` stays true because every file inside the narrowed
  scope was read. VERIFIED therefore means "no contradicting capability in
  the scope you chose". Reviewers must read the limitations before trusting
  it. Automatic skips and budgets are different: they are coverage failures
  the caller did not intend, so they set `scan_complete: false`.
- **UNVERIFIABLE** is a first-class result. `proveit` never upgrades
  missing evidence into proof.

Every verdict carries limitations. They name the static-only nature of the
analysis, the exclusion of binary assets and vendored directories, the
build/runtime split, and the concrete paths excluded on that run.

## Non-goals

- Parsing arbitrary prose or judging intent.
- Executing, building, installing or importing target code.
- Proving absence of behaviour for all inputs.
- Deciding whether a program is malicious, safe or legally compliant.
- Replacing a human review, a sandbox, an SBOM generator or a license lawyer.

## Adding a claim kind

Add one row to `CLAIM_PATTERNS` and one entry to `KIND_POLARITY` and
`KIND_SCOPE`. Add a rule to `NEGATIVE_REQUIREMENTS` only when the new kind
can be contradicted by positive evidence. Add a test in
`tests/test_proveit.py` that covers both VERIFIED and CONTRADICTED. Update
`docs/OUTPUT_SCHEMA.md` if the JSON shape changes.
