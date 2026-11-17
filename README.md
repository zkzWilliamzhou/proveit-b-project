# proveit

Your README makes promises. `proveit` checks the code.

A repository says "works offline", "no telemetry", "zero dependencies", "MIT licensed". Those sentences shape what people install, what CI pipelines trust, and what agents execute. Nobody checks them. `proveit` reads the repository as data and returns one of three answers for each claim: VERIFIED, CONTRADICTED, UNVERIFIABLE. It never runs the target program, never writes to the target tree, and never opens a socket.

## Run it

Python 3.9 or newer. No install step, no packages, no account.

```console
$ git clone https://github.com/your-org/proveit.git
$ cd proveit
$ python3 -m proveit check .
```

Or install the command:

```console
$ python3 -m pip install .
$ proveit check /path/to/some/repo
```

## A 60-second demo

The repository ships two tiny fixtures. One tells the truth. One lies.

```console
$ python3 -m proveit check third_party/examples/clean_repo --format markdown
# proveit claim audit

Root: `.`
Scan complete: yes
VERIFIED: 4 | CONTRADICTED: 0 | UNVERIFIABLE: 1
```

```console
$ python3 -m proveit check third_party/examples/dirty_repo --format markdown
# proveit claim audit

Root: `.`
Scan complete: yes
VERIFIED: 0 | CONTRADICTED: 4 | UNVERIFIABLE: 1

| State | Claim | Kind | Location | Reason |
|---|---|---|---|---|
| **CONTRADICTED** | No telemetry. | `no&#95;telemetry` | `README.md:6` | 3 contradicting capabilities found in source: telemetry.event, telemetry.sdk. |
| **CONTRADICTED** | Works offline. | `offline` | `README.md:7` | 4 contradicting capabilities found in source: network.http, telemetry.event, telemetry.sdk. |
| **CONTRADICTED** | Zero dependencies. | `zero&#95;dependencies` | `README.md:8` | 2 runtime dependencies are declared in manifests. |
| **CONTRADICTED** | MIT licensed. | `license` | `README.md:9` | LICENSE text at LICENSE reads as Apache-2.0, not MIT. |
```

Then watch a release add a network call:

```console
$ python3 -m proveit diff third_party/examples/v1 third_party/examples/v2
# proveit capability diff

Left: `left` (complete: yes)
Right: `right` (complete: yes)

Added capabilities: `manifest.dependency`, `network.endpoint`, `network.http`, `telemetry.event`, `telemetry.sdk`
Removed capabilities: none
```

Exit code 1 means a contradiction or an added risk capability. Wire that into a pull request check and a silent analytics SDK cannot land without a diff.

## What `proveit` decides

Nine claim kinds, each mapped to a fixed set of static capabilities. Run `python3 -m proveit ontology` to print the whole table.

| Claim in prose | What counts as proof |
|---|---|
| `no network` / `works offline` | No HTTP client, socket, DNS or download call in any in-scope source file, plus full scan coverage |
| `no telemetry` / `no tracking` | No known analytics SDK and no telemetry event call |
| `no data leaves your machine` | No network or telemetry capability in source |
| `zero dependencies` | Every supported root manifest declares an empty runtime dependency set |
| `MIT licensed` and other SPDX names | A LICENSE file matching that template, with no conflicting manifest field |
| `never executes` / `no shell commands` | No dynamic evaluation, subprocess or native loader call |
| `never writes` | No filesystem mutation call |
| `no binaries` | Always UNVERIFIABLE. Binary assets are outside the scan scope |

A hard-coded URL is a hint. It lands in the receipt and in the diff. It never contradicts a claim on its own, since schema URIs and error messages contain URLs without sending a byte.

## Three rules that make the answers honest

1. **Absence of findings is not proof.** A negative claim is VERIFIED only when the scan covered every eligible file. One skipped file, one undecodable byte, one exhausted budget, and the claim drops to UNVERIFIABLE. `proveit` prints the reason.
2. **CONTRADICTED needs positive evidence.** A missing LICENSE file, a missing manifest, or a low score never produces CONTRADICTED.
3. **Conditional claims are UNVERIFIABLE.** "No telemetry by default" depends on configuration. `proveit` refuses to decide it and says why.

Every verdict carries its scope and its limitations. VERIFIED means "no contradicting evidence inside the declared scan scope", not "mathematically proven for all inputs". Read the limitations column before you quote a result.

## Commands

| Command | Output |
|---|---|
| `proveit scan PATH` | Capability receipt: every match with file and line |
| `proveit check PATH` | Verdicts for each recognized claim |
| `proveit diff LEFT RIGHT` | Added and removed capability evidence between two trees |
| `proveit selftest` | Audits `proveit` with `proveit` |
| `proveit ontology` | Prints the claim table and capability list |

Every command accepts `--format json` or `--format markdown`. `check` and `diff` also accept `--format sarif` for GitHub code scanning. `-o FILE` writes the report to a file; add `--force` to overwrite.

| Flag | Effect |
|---|---|
| `--exclude RELATIVE_PATH` | Narrow the declared scan scope. The path is printed in the receipt and named in every verdict's limitations. |
| `--claim-docs` | Also read claims from Markdown under `docs/`. |
| `--max-claims N` / `--max-evidence N` | Stop reading claims or capabilities after N hits. A budget stop sets `scan_complete: false`. |
| `--max-file-bytes`, `--max-total-bytes`, `--max-files`, `--max-line-chars` | Raise the read budgets for a large repository. All remain hard ceilings. |

An `--exclude` is a deliberate scope narrowing, so `scan_complete` stays true and negative claims can still be VERIFIED with the exclusion disclosed. An unreadable file, an invalid UTF-8 file, an oversize file or an exhausted budget is an unintended coverage failure: it sets `scan_complete: false` and moves negative claims to UNVERIFIABLE.

```console
$ proveit check . --format json | jq '.counts'
{
  "CONTRADICTED": 0,
  "UNVERIFIABLE": 1,
  "VERIFIED": 4
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | No contradicted claim, no added risk capability |
| 1 | At least one contradicted claim, or a new risk capability in `diff` |
| 2 | Bad root, bad limit, unwritable output, internal error |
| 3 | No contradictions, but UNVERIFIABLE claims exist and `--fail-unverifiable` was set |

`diff --allow-risk` returns 0 even when capabilities were added. `selftest` returns 1 on any failed check.

## What `proveit` is not

It is not a sandbox, a malware detector, a legal opinion, a coverage tool, or a replacement for reading the code. It does not execute, build, install, or resolve anything in the target tree. It does not parse arbitrary English, and it does not claim a program is safe. Static analysis misses obfuscated code, dynamically assembled strings, and behaviour that lives in a dependency you never scanned. Those limits are printed in every report.

`proveit` shows the gap between what a project says and what its source contains. That gap is where review starts.

## Development

```console
$ python3 -m unittest discover -s tests -v
$ python3 -m proveit selftest
```

`tests/` covers path escapes, symlinks, oversize files, long lines, invalid UTF-8, terminal escapes, Markdown injection, ReDoS-shaped input, manifest parsing, verdict semantics, string-literal precision, budget behaviour, determinism, and exit codes. `docs/REVIEW_LOG.md` records twelve review rounds and every fix they forced.

Read `docs/CLAIM_ONTOLOGY.md`, `docs/OUTPUT_SCHEMA.md`, `docs/ARCHITECTURE.md`, and `SECURITY.md` before you change a rule.

## License

MIT licensed. See `LICENSE`.
