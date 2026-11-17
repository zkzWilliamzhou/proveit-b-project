# Review log

Twelve rounds. Each round names what was examined, what was found, what
changed, and the command that proved the change. Round 7 is the architecture
deepening required by the brief; its golden outputs show that no function
changed. Rounds 10-12 were added after the first zip was handed over, after
further adversarial probing found three real false positives.

The verification command used throughout:

```console
$ python3 -m unittest discover -s tests -v
$ python3 -m proveit selftest
$ python3 -m proveit check . --format json
```

## Round 1 - Output integrity and CLI trust boundary

**Examined:** `cli._emit`, error handling, `-o`, `--force`.

**Found:**
- `os.write` can return a short count. A long JSON report could be truncated
  while the CLI still returned success. A truncated report is worse than no
  report because CI would parse a partial document.
- Error messages printed raw exception text. A scan root containing an ANSI
  escape sequence could inject control characters into the operator's
  terminal.

**Changed:**
- Loop until every byte is written; raise a CliError on a zero-length write.
- All stderr text passes through `sanitize.plain`.
- `-o` keeps `O_NOFOLLOW` and `O_EXCL` unless `--force` is given.

**Proved:** `test_output_file_contains_full_report`,
`test_output_file_not_overwritten_without_force`,
`test_error_message_sanitizes_control_characters`.

## Round 2 - Evidence integrity

**Examined:** every CONTRADICTED path.

**Found:**
- The license verdict cited a LICENSE file in its reason but carried no
  Evidence object. That broke the contract "CONTRADICTED needs positive
  evidence with a file location".
- `claims.extract` returned a note when the claim budget was hit, but the CLI
  discarded it. Dropped claims vanished silently.

**Changed:**
- `manifests.attach` emits a `manifest.license` Evidence for the LICENSE text
  at `line: 0`.
- `Receipt.with_notes` attaches budget Notes and recomputes
  `scan_complete`, so a dropped claim degrades negative verdicts.
- `test_contradicted_has_positive_evidence` now asserts non-empty evidence for
  every CONTRADICTED verdict.

**Proved:** `test_license_verdict_carries_license_file_evidence`,
`test_claim_budget_note_degrades_coverage`.

## Round 3 - False positives in matching

**Examined:** `scanner.scan`, `rules.py`, the repository's own source.

**Found:**
- A commented-out call still produced Evidence. A documentation example
  would become a false CONTRADICTED.
- `proveit/rules.py` holds the literal names of the behaviours being
  detected. The first self-audit reported 58 fake telemetry and network
  findings and 4 CONTRADICTED claims against its own README.
- `setup.cfg` parsing treated every indented line under `[options]` as a
  dependency, so `packages = find:` became a package name.

**Changed:**
- Skip comment-only lines.
- Skip lines composed only of string literals, commas and whitespace. A bare
  string constant does not call anything. This removed the rule-table
  self-accusation without a hidden exclusion for `check .`.
- Rewrite `_setup_cfg` to read only `install_requires` continuations.

**Proved:** `test_comment_line_is_not_a_call`,
`test_bare_string_literal_is_not_a_call`,
`test_setup_cfg_only_reads_install_requires`,
`test_rule_table_does_not_accuse_itself`. `check .` moved from 4 CONTRADICTED
to 0.

## Round 4 - Denial of service

**Examined:** `workspace.walk`, `workspace._read_regular`, `Limits`.

**Found:**
- `sorted(os.scandir(dir))` materialised every entry before the entry budget
  was checked. A million-name directory could exhaust memory before the
  budget fired.
- Symlinks, FIFOs, sockets and device nodes were reachable through the walk.
- Invalid UTF-8 and binary content could reach the decoder unchecked.

**Changed:**
- Consume the scandir iterator with an explicit cap of one more entry than
  the remaining budget, sort only that bounded list, then stop.
- Reject non-regular files, symlinks and paths that resolve outside the
  canonical root. Open with `O_NOFOLLOW` and verify inode/device after open.
- Decode strictly as UTF-8 and skip binary content with a warning Note.

**Proved:** `test_entry_budget_stops_before_materializing_everything`,
`test_symlink_is_rejected`, `test_special_file_is_rejected`,
`test_invalid_utf8_is_skipped`, `test_redos_shaped_input_completes`,
`test_long_line_is_skipped`.

## Round 5 - Scope honesty and report completeness

**Examined:** `adjudicator`, `render`.

**Found:**
- Limitations existed on every Verdict but the Markdown report never printed
  them. A user could read VERIFIED without seeing "static evidence only".
- Excluded directories were recorded as Notes but not named in verdict
  limitations, so a caller-supplied `--exclude` was easy to miss.
- SARIF messages dropped limitations entirely.

**Changed:**
- Add `_scope_notes` and append concrete excluded paths, excluded files and
  claim-budget Notes to every verdict's limitations.
- Render a `## Limitations` section in Markdown.
- Append limitations to SARIF message text.

**Proved:** `test_limitations_visible_in_markdown`,
`test_exclusion_is_disclosed`, `test_sarif_valid_structure`.

## Round 6 - Injection, determinism, read-only behaviour

**Examined:** `sanitize.py`, `render.py`, JSON encoding, exit codes.

**Found:**
- Repository text could carry ANSI/OSC escapes, bidi overrides, zero-width
  characters, pipes, backticks and `<script>` into terminal or Markdown
  output.
- Directory entry names used in Notes were only partially cleaned.
- No test proved the tool leaves the target tree untouched or that two runs
  are byte-identical.

**Changed:**
- Route every repository-derived string through `sanitize.plain` or
  `markdown_cell`. `plain_name` now calls the same sanitiser.
- Add tests for injection, read-only scanning, determinism, all four exit
  codes, `--fail-unverifiable`, `diff --allow-risk` and SARIF shape.

**Proved:** `test_ansi_and_markdown_injection_are_neutralized`,
`test_plain_and_markdown_cell`, `test_scan_does_not_modify_target_tree`,
`test_two_runs_are_byte_identical`, `test_bad_root_is_exit_2`,
`test_fail_unverifiable_exit_3`.

## Round 7 - Architecture deepening, function preserved

**Examined:** module depth, locality, seams, the deletion test. The
`improve-codebase-architecture` skill from `mattpocock/skills` drove the
review; its HTML report is `architecture-review.html` beside the repository.

**Found:** `cli.collect` and `selftest.run` duplicated a five-step sequence.
`manifests.attach` rebuilt a Receipt by hand, so a new field could be dropped
at a call site. Both are shallow modules.

**Changed:**
- Add `pipeline.py` with `read_tree` and `audit_tree`. `cli.collect` and
  `selftest.run` became thin wrappers.
- Add `Receipt.with_manifests` and `Receipt.with_notes` in `model.py`.
- Add `GLOSSARY.md`, `docs/ARCHITECTURE.md` and
  `docs/adr/ADR-0003-pipeline-seam.md`.

**Function preservation check (golden outputs, before and after):**

| Command | Before | After |
|---|---|---|
| `check .` | 7 VERIFIED / 0 CONTRADICTED / 1 UNVERIFIABLE, exit 0 | identical |
| `check third_party/examples/clean_repo` | 4 / 0 / 1, exit 0 | identical |
| `check third_party/examples/dirty_repo` | 0 / 4 / 1, exit 1 | identical |
| `diff v1 v2` | 5 added capabilities, exit 1 | identical |
| `selftest` | ok, 5 checks | identical |
| Full suite | 50 tests | 50 tests |

No flag, field, capability, exit code or verdict changed.

## Round 8 - Self-accusation and first-run reliability

**Examined:** `proveit check .` as a new user's first command.

**Found:** after adding `tests/`, the adversarial fixture strings in the test
file produced 8 capability hits and 3 CONTRADICTED claims against the tool's
own README. The first run returned exit 1 for a clean project.

**Changed:**
- Assemble every rule literal in the test file from pieces, so the fixture
  stays adversarial at runtime without making the test source a capability
  fixture.
- Keep `tests` and `proveit/rules.py` as disclosed exclusions in `selftest`,
  but require `check .` to pass with no exclusions at all.

**Proved:** `check .` returns exit 0 with 7 VERIFIED / 0 CONTRADICTED /
1 UNVERIFIABLE. `test_rule_table_does_not_accuse_itself` guards this.

## Round 9 - Final regression and documentation audit

**Examined:** every command, every format, README examples, documentation
consistency, installed skill provenance.

**Found:** README demo snippets had drifted from the real output (`1
contradicting capability` versus the actual 4, three added capabilities
versus the actual 5). Research notes and third-party skill catalogues sat in
`docs/` and `skills/`, where they would be scanned as project material.

**Changed:**
- Replace README demo output with verbatim tool output.
- Move skills, research and example fixtures under `third_party/`, which the
  declared scan scope excludes. Document provenance in `third_party/README.md`.
- Add `docs/CLAIM_ONTOLOGY.md`, `docs/OUTPUT_SCHEMA.md`, `SECURITY.md`,
  `CONTRIBUTING.md`, `AI_DEVELOPMENT.md`, `CHANGELOG.md` and CI workflows.

**Proved:** 50/50 tests pass, `selftest` passes, `check .` exit 0, all three
README demos reproduce their stated output, `ontology --format json` matches
`docs/CLAIM_ONTOLOGY.md`.

## Round 10 - String and comment precision

**Examined:** three hand-built hostile fixtures, then the tool's own source.

**Found (all reproduced before the fix):**

| Fixture | Result before | Expected |
|---|---|---|
| `NAME = "posthog"` | CONTRADICTED, `telemetry.sdk` | VERIFIED |
| `x = 1  # posthog ...` | CONTRADICTED, `telemetry.sdk` | VERIFIED |
| `"""Uses posthog internally."""` | CONTRADICTED | VERIFIED |
| `NAME = "posthog"; posthog.capture(1)` | risk of losing the real call | CONTRADICTED |

Round 3's `_literal_only` fast path only covered lines made entirely of
literals. A single-line assignment, an inline comment and a docstring all
still reached the rule table. A simple "skip the whole line if anything is in
a string" patch would have hidden real calls, so it was rejected.

**Changed:**
- `scanner._string_mask` returns a per-line mask plus a carry state for
  triple-quoted docstrings. Consecutive backticks are treated as one run, so
  reStructuredText `` ``literal`` `` spans are fully masked.
- `scanner._comment_cut` finds inline `#` and `//` markers outside strings,
  preserving Rust `#[` attributes.
- `rules.Rule.find` accepts a predicate, scans every occurrence and returns
  the leftmost acceptable hit. No regex, still `str.find` on a bounded line.
- `scanner._comment_only` no longer treats `#[link(` as a comment, which had
  silently removed the `native.code` capability.
- Added the string-masking limitation to `NEGATIVE_LIMITATIONS`.

**Also fixed:** `claims.extract` appended one budget Note per remaining line
(38 duplicate Notes for a 40-line README). It now appends exactly one and
stops reading.

**Concrete false positive removed:** `dirty_repo/pyproject.toml` contains
`dependencies = ["requests", "posthog"]`. Before this round that line matched
the `posthog` rule and inflated the `no telemetry` reason from 3 to 4
contradicting capabilities. A dependency name is not a telemetry call. The
four remaining detections are all real: `import posthog`, `posthog.capture`,
`requests.get`, and the manifest dependency facts. The `offline` reason moved
from 5 to 4 for the same reason. The README demo was re-copied from the new
output; the verdict counts (0 CONTRADICTED verdicts vs 4) never changed.

**Proved:** 10 new tests in `TestRound10StringAndCommentPrecision`, including
`test_masked_first_hit_does_not_hide_later_call`,
`test_require_http_still_detected` and
`test_rust_attribute_is_not_an_inline_comment`. `check .` went briefly to 2
false CONTRADICTED from backtick literals in our own docstrings, then back to
7 VERIFIED / 0 CONTRADICTED / 1 UNVERIFIABLE.

## Round 11 - Budget semantics and the exclusion contract

**Examined:** `--exclude`, budget flags, `--claim-docs`, empty claim sets,
output overwrite.

**Found:**
- `docs/CLAIM_ONTOLOGY.md` claimed an excluded path moves a negative claim to
  UNVERIFIABLE. The implementation kept `scan_complete: true` and returned
  VERIFIED with the exclusion disclosed. One of the two was wrong.
- `--max-claims` and `--max-evidence` existed in `Limits` but had no CLI flag,
  so a reviewer could not reproduce a coverage failure without writing Python.
- No test covered `--claim-docs`, a repository with zero recognized claims,
  `--force`, or Markdown output for `scan` / `ontology`.

**Decision:** the implementation was right. An explicit `--exclude` is a
deliberate narrowing of the declared scan scope; every file inside that
narrowed scope was still read, and the exclusion is printed. An automatic
skip or exhausted budget is an unintended coverage failure and must degrade
the verdict. The document was corrected, not the code. This distinction is now
written in `README.md`, `docs/CLAIM_ONTOLOGY.md` and locked by a test.

**Changed:**
- Added `--max-claims` and `--max-evidence` to the CLI.
- Corrected the ontology document and added a README table of budget flags.
- Added 11 tests in `TestRound11BudgetsAndFlags`, including
  `test_claim_budget_emits_one_note_and_degrades_verdict`,
  `test_evidence_budget_stops_the_scan`, `test_oversize_file_is_skipped`,
  `test_depth_budget_stops_walk` and
  `test_explicit_exclusion_is_deliberate_scope_narrowing`.

**Proved:** 71/71 tests pass. `selftest` and `check .` both return exit 0 with
7 VERIFIED / 0 CONTRADICTED / 1 UNVERIFIABLE.

## Round 12 - Release audit

**Examined:** version constants, documentation consistency, demo output,
skill definitions, CI workflow, and the packaged artifact itself.

**Found:** the test count and review-round count had drifted across
`README.md`, `CONTRIBUTING.md`, `docs/AI_DEVELOPMENT.md`,
`docs/ARCHITECTURE.md`, `CHANGELOG.md` and the local `proveit-review` skill.
`architecture-review.html` still reported "50 tests" as its round-7 snapshot.

**Changed:**
- Bumped to 1.0.1. `schema_version` stays `1.0` because no output field
  changed meaning.
- Synced all counts to 71 tests and twelve rounds; added a historical note to
  the HTML review that later rounds grew the suite.
- Re-copied every README demo from real output.
- Verified the zip by extracting it into a clean temporary directory and
  running the full gate there: `--version`, `selftest`, `check .`, clean
  fixture, dirty fixture (exit 1), diff (exit 1), and the complete test suite.

**Proved:** archive integrity check returned no bad member; every gate passed
from the extracted copy, so the delivery is self-contained.

## Residual risks

- Static analysis cannot see obfuscated code, dynamically assembled names,
  generated sources or behaviour inside unscanned dependencies. String
  masking deliberately ignores literal contents, so a capability assembled
  at runtime from string fragments can be missed. An unclosed triple-quoted
  string masks the remainder of its file; that is conservative (no false
  CONTRADICTED) but can hide a real call.
- A caller can exclude a path and hide a capability. The exclusion is printed
  and appears in limitations, but the tool cannot stop a determined liar.
- `VERIFIED` is scoped to the declared scan, not a proof about all inputs.
- License matching is text comparison, not legal advice.
- Star counts measure attention, not utility. `third_party/research/ADOPTION_PLAYBOOK.md`
  states this explicitly; this project targets a real gap, not a growth hack.
