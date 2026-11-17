# Security and Robustness Threat Model for an Offline Local CLI Repository Analyzer

## Executive summary: an untrusted repository must remain data, never an execution or control primitive

This tool must treat every repository as hostile input, not as a collection of ordinary files. It parses document formats and source code, walks a filesystem tree, names paths and diagnostics, and produces structured reports. All of these surfaces can become control inputs. A malicious repository can exploit a permissive document parser to consume unbounded memory or CPU, induce path confusion, influence a report consumer through injected syntax, or—if any plugin or analysis step executes target-supplied code—gain arbitrary command execution. The most important design decision is therefore not a long list of defenses, but a strict separation between **analyzed data** and **tool control**. A repository may supply strings, byte streams, paths, and configuration documents; it must never supply executable code, command arguments, URLs, credentials, regular expressions, schema definitions, or report structure.

The central trust boundary is the operating system call that opens a repository file. Before that call, the implementation must validate size, type, path, symbolic-link policy, and resource accounting; after that call, it must keep the resulting bytes distinct from commands, terminal display operations, and downstream report fields. Even when the user invokes the tool, the repository remains untrusted. A local-only architecture limits network exposure but does not remove filesystem, code-execution, or denial-of-service risk. Least privilege, isolated directories, bounded recursion, safe parsing, constant-time or linear-time matching where feasible, atomic path checks, no shell interpretation, and machine-readable output encoding are therefore mandatory.

Several conclusions follow.

First, **the safest execution policy is to analyze only, never to run**. The implementation should not invoke repository binaries, scripts, tests, package managers, language servers, build tools, hooks, `Makefile` targets, or downloaded programs. If an external program is indispensable, it must run with a frozen, fully qualified executable path; an explicit argument vector; a private temporary directory; no inheritable secrets; and a constrained user and cgroup.

Second, **“offline” is a negative control and must be testable**. The CLI should default to no network access and fail closed when DNS, HTTP, proxy, update, model, or telemetry activity occurs. An opt-in network command should be separately documented and audited; it must never be triggered implicitly by repository content.

Third, **exit-code semantics must be narrow and stable**. A non-zero exit should mean a configured policy violation, not a crash, parser failure, resource limit, configuration error, or internal bug. CI jobs should additionally verify provenance, schema validity, and digital signature before treating a report as a gate. A tool can be robust yet analytically weak: memory safety and resource limits do not guarantee correct findings.

Finally, **the tool must be considered a workstation utility rather than a sandbox**. It operates with the invoking user’s authority and cannot protect itself against a privileged caller, malicious kernel, or hostile working directory. A vulnerable language runtime, native dependency, or unsafe parser can still turn malformed input into code execution. The correct operational response is isolation, patching, conservative filesystem permissions, and separation of untrusted analysis from trusted release decisions.

## 1. The repository is an attacker-controlled input boundary, and the parser is not a sandbox

**The repository is untrusted data, while the CLI, its configuration, and its built-in analyzers are trusted control paths.** Every repository-supplied artifact—including Markdown, JSON, TOML, YAML, filenames, symlink targets, Git hooks, package manifests, lockfiles, workflow files, generated sources, and text encoding—must be treated as potentially hostile. Repository files should not influence tool behavior except through explicit, validated findings or advisory metadata. In contrast, built-in analysis rules, CLI flags, user-supplied configuration, and pinned dependencies may affect execution. This distinction should appear in code reviews, issue triage, and release notes: parser defects and input-handling defects have different blast radii.

JSON is a language-independent text format composed of values, objects, arrays, strings, numbers, Booleans, and null [1]. TOML maps unambiguously to a hash table and specifies UTF-8 encoding and permitted value types [2]. Neither format should need or receive access to executable objects, remote resources, external entities, or dynamic code. Yet parsers remain complex software components and can fail through excessive recursion, deeply nested structures, duplicate keys, number conversion, alias expansion, or sheer size. Safe document parsing is therefore necessary but insufficient: it prevents known unsafe object construction, while schema validation and resource limits prevent malformed but otherwise ordinary data from destabilizing analysis.

**The tool has two distinct trust boundaries: one around execution and one around evidence.** The execution boundary separates repository data from process state, the filesystem outside the requested tree, and downstream automation. The evidence boundary separates repository strings from the semantics of the terminal, HTML, SARIF, JSON, logs, and issue trackers. Confusing these layers allows an attacker to turn a quoted path, severity label, code snippet, or rule identifier into code, markup, terminal control, or a CI policy outcome.

| Trust boundary | Repository-supplied input | Trusted control | Required boundary check |
|---|---|---|---|
| Document parsing | Document bytes, document size, declared encoding, custom schema | CLI flags and built-in schema | Reject oversize input; enforce UTF-8 where required; use safe parser and explicit schema [1][2] |
| Filesystem walk | Paths, symlink targets, file kinds, Git metadata | Scan root and explicit output path | Canonicalize and revalidate; block directory and symlink escapes; never follow device nodes |
| Text matching | Source text, commit messages, paths | Compiled built-in patterns | Use linear-time engines where possible; precompile; bound steps and time |
| Reporting | Findings, snippets, messages, rule IDs | Output format schema and writer | Encode through a typed serializer; validate the resulting document |
| Automation | Reports, exit code, artifacts | Release policy and human review | Treat the report as untrusted; verify signature and schema before gating |
| Supply chain | Plugins, hooks, fetched binaries, dependency manifests | Reviewed built-ins and pinned dependencies | Never load repository code; require signatures, hashes, and allowlists |

**The repository should be considered capable of causing denial of service even without code execution.** A single maliciously constructed string can cause catastrophic regex backtracking. A deep directory, nested JSON or TOML document, long alias chain, huge file, or rapid sequence of findings can exhaust CPU, memory, file descriptors, or time. These are not merely quality defects: under a quota, they can halt an analysis job or crowd out legitimate work. The implementation should therefore publish hard operational limits for total input bytes, individual-file bytes, parse depth, alias expansion, finding count, walk entries, CPU time, wall-clock time, file descriptors, and memory.

**Local execution does not imply trust, and offline operation is a property to enforce rather than assert.** The tool inherits the invoking user’s filesystem and process permissions. It can read or overwrite files outside the repository, follow a symlink into sensitive directories, or—if it executes target content—run attacker-chosen code. The absence of a network feature is useful only if the tool can demonstrate that no code path reaches the network. A single plugin, dependency, update check, language server, subprocess, or HTTP callback can nullify the “offline” claim.

**Plugin support fundamentally changes the threat model.** If plugins are ordinary executable modules, then a repository that can place or name a plugin can potentially execute code. The only safe default is to load no repository-supplied code. Signed, version-pinned, separately installed analyzers may be loaded from an administrator-controlled directory, but they should remain out of scope for ordinary repository scans.

## 2. Safe parsing must be paired with size, schema, and complexity controls

**Safe parsing removes known execution paths, but it does not make untrusted data safe to use.** A document parser must reject malformed, ambiguous, or excessive input before the application assigns semantic meaning to any value. The implementation should define a maximum document size, a maximum nesting depth, and a maximum number of values or keys; cancel parsing on the first limit violation; and record structured diagnostics rather than rendering unbounded snippets. These limits should be deterministic and externally configurable only through user-supplied policy. A malicious document must never choose timeouts, recursion depth, schema endpoints, file paths, or executable helpers.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|---|---|---|---|
| Billion-laughs, quadratic alias expansion, or deeply nested JSON/TOML | Memory exhaustion, stack overflow, or hang (CWE-400) | Stream or chunk the parser where feasible; enforce document size, depth, object/array length, alias and entity budgets; parse with a robust library; fail fast on budget exhaustion | Fuzz nested arrays, duplicate keys, and repeated aliases; assert peak resident memory and parse time remain under fixed thresholds for a hostile 10 MiB corpus |
| Malicious YAML tags or custom loader hooks | Arbitrary code execution during parsing (CWE-502) | Use the parser’s safe document mode; disable custom tags and resolver extensions; allow only simple scalars, mappings, and sequences; deserialize to typed application models only after validation | Supply `!!python/object/apply:os.system` and equivalent language- or implementation-specific tag payloads; assert the parser raises an error and no subprocess appears in an audit log |
| JSON/TOML type confusion | Logic error, path traversal, command injection, or privilege escalation (CWE-20) | Enforce schema after parsing; verify value types, ranges, and enumerations; reject unknown keys and duplicate definitions; treat numbers as untrusted text until validated | Submit `"port": "22; rm -rf /"`, negative sizes, and out-of-range integers; assert validation rejects them and no string reaches a command or path API |
| Markdown HTML, reference, or directive injection | XSS, hidden content, or malicious links when the report is rendered (CWE-79) | Parse Markdown with a restrictive renderer; disable raw HTML and unsafe extensions; turn URLs into text or use only `http`/`https` with no autolinking of `javascript:`, `data:`, or `file:` | Include `<script>`, `javascript:`, and malformed Unicode URLs; assert they are rendered as inert text or rejected, never as executable markup |
| YAML/JSON/TOML ambiguity or duplicate keys | Unpredictable rule behavior or an incorrect analysis result | Define duplicate-key, merge-key, date-guessing, and float-parsing policy explicitly; retain only the first or last allowed value after validation; log schema version and parser mode | Provide a file with conflicting keys and several interpretations of `1.10`; assert the chosen policy is deterministic and covered by contract tests |
| Malformed UTF-8 or encoding mismatch | Mojibake, panics, truncated paths, or hidden different bytes (CWE-838) | Read repository paths in the platform-native form; decode document contents strictly as UTF-8 unless a format specifies otherwise; replace invalid bytes only at output boundaries; retain raw bytes for hashes and comparison | Provide overlong, surrogate, and invalid byte sequences; assert no crash, no silent path match, and identical hash behavior across platforms |
| Document parser vulnerability in a dependency | Remote-code-equivalent compromise on the workstation | Keep parsers patched and minimized; avoid unnecessary format features; fuzz the input corpus; monitor advisories; avoid native extensions where a memory-safe library is sufficient | Run an OSS-Fuzz-style corpus and a public exploit sample; assert no crash or memory error under sanitizers |
| Huge valid documents | Latency spikes or job starvation | Apply cumulative and per-file quotas; parse only the leading region needed for analysis where the format permits | Create a valid 2 GiB document with a late finding; assert the tool stops after the size limit and emits a quota diagnostic |

JSON permits only the listed structural types, and the parser must not infer executable semantics from a string or number [1]. TOML is specified as a UTF-8 Unicode document and allows only defined value types; its specification also forbids most control characters in comments [2]. These properties support safe deserialization, but they do not eliminate complexity or resource-exhaustion defects.

The implementation should therefore establish an explicit type model for each configuration file. A rule severity should become an enumerated value only after validation. A path should become a filesystem path only after normalization and boundary checks. A port, timeout, or memory limit should become a numeric scalar only after range and unit validation. A parser may turn bytes into strings and containers, but it should not turn repository content into executable behavior.

## 3. Path canonicalization must occur before each filesystem use, not once at startup

**A path that is safe when checked may become unsafe when opened.** A directory entry may be replaced, a symlink may be re-pointed, or the scan root may be moved between validation and use. The tool must therefore validate the path, file kind, and containment immediately before the system call that opens the file. Caching an early canonical form and reusing it later widens the race window. Where supported, the implementation should open by file descriptor or handle and then verify the descriptor’s identity.

The initial scan root must be resolved to an absolute, fully canonical location before traversal begins. Each candidate path should be joined only with that root, normalized without symlink resolution, and checked to ensure it remains lexically within the root. The implementation should then inspect the actual file kind and parent chain. If the entry is a symlink or an unexpected object, the operation must be rejected before opening.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|---|---|---|---|
| `../` segments or absolute paths in tree entries | Read or write outside the scan root (CWE-22) | Use a robust path library; reject entries that escape after root-relative joining; open only within a precomputed canonical root | Place `../../etc/passwd` and an absolute `/etc/passwd` entry in a tree; assert access is denied and no external path appears in the report |
| Symlink or hardlink escape | Read of sensitive files, credential disclosure, or clobbering outside the repository (CWE-59) | Resolve the real path after opening; compare device/inode or equivalent identifiers; reject non-regular files; optionally provide an opt-in bounded symlink mode | Create a symlink to `/etc` and a hardlink to a sensitive file; assert both are rejected and counted as policy failures |
| TOCTOU between validation and file open | Follow a malicious symlink after a safe check (CWE-367) | Open by file descriptor, `O_NOFOLLOW`, `O_PATH`, or equivalent; verify inode and containment after opening; avoid check-then-open patterns | Race a benign entry with a symlink swap on a fast loop; assert the open rejects the changed target and no escaped content reaches the report |
| Directory permissions or writable scan root | Repository data is modified or exfiltrated through a writable cache | Default to read-only mode; use a dedicated non-root account; place temporary files in a private `tmpfs` or scoped directory; run in a sandbox or container where available | Attempt writes during analysis and symlink replacement; assert they fail and no files are created in the scan root |
| Filesystem loop through circular symlinks | Infinite walk or stack overflow | Track visited device/inode pairs in a strict set; limit symbolic-link depth; treat cycles as structural errors | Create `a -> b` and `b -> a`; assert the walk terminates and reports the cycle |
| Special files, devices, FIFOs, or sockets | Hang, kernel-side resource use, or disclosure (CWE-410) | Open only regular files; exclude devices, FIFOs, sockets, and doors; set open and read timeouts; ignore unsupported file types | Place `/dev/urandom`, a FIFO, and a Unix socket in the tree; assert they are skipped or rejected without blocking |
| Case-insensitive or Unicode-normalized collisions | Two repository paths overwrite one another or bypass an allowlist | Preserve bytes used by the platform; compare paths case- and normalization-sensitively as the platform requires; canonicalize once per operation | Create `A` and `a` on a case-insensitive filesystem; assert both retain distinct evidence and no allowlist bypass occurs |

**Symlink safety must apply to every output path as well.** Reports, caches, lockfiles, diffs, and supplemental artifacts should be written only to paths selected by the user or administrator—not to a repository-supplied filename. Before writing, the tool should ensure the target is inside the designated output directory, is not a symlink, and does not overwrite an unexpected existing file. A malicious repository should not be able to choose the report filename, prepend `../../`, begin the name with `--`, or induce argument injection through a later shell command.

## 4. Repository content must never be interpolated into a command, shell, or evaluator

**Any use of `eval`, `exec`, `pickle`, or a shell turns text into a programming language.** Repository content includes not only source code but also filenames, branch names, commit messages, dependency URLs, environment variables, rule messages, and configuration values. These strings may contain quotes, newlines, leading dashes, shell metacharacters, or Unicode control characters. Passing them to a shell, an `eval` family function, a template engine, or a deserializer makes the repository an indirect author of commands or objects.

If execution is genuinely required, the tool should construct a fixed program invocation from trusted constants and pass all repository-derived values as distinct, uninterpreted arguments. There should be no string templating of shell commands, no `sudo` or setuid behavior, no automatic hook execution, and no use of repository-supplied interpreters. Files should be supplied through safe paths or sealed temporary files. The subprocess should run under a dedicated account with no access to the user’s secrets, no network, and a private temporary directory.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|---|---|---|---|
| Filename passed to a shell or `os.system` | Arbitrary command execution (CWE-78) | Prohibit shell invocation; invoke executables by fixed `argv[0]`; pass repository strings as opaque arguments | Name a file `$(touch /tmp/pwn)` and `--exec=cmd`; assert no shell interpretation and that the filename is rejected or quoted correctly |
| Filename treated as a CLI flag | Argument injection, option smuggling, or command substitution (CWE-88) | Insert a `--` separator before positional operands; reject arguments beginning with `-` unless explicitly allowed | Use filenames starting with `--config` and `@file`; assert they are not parsed as options |
| `eval`, `exec`, `Function`, `compile`, `ast.literal_eval` misuse, or template execution | Remote-code-equivalent execution from text or comments | Do not evaluate repository text; allow only a reviewed rule-expression language; sandbox it without relying on blocklists; ban dynamic imports | Include `import os; os.system(...)` and template payloads; assert they are reported as literal text, never executed |
| `pickle`, `marshal`, `yaml.load`, `java.io.ObjectInputStream`, or custom deserialization | Arbitrary code execution or resource exhaustion (CWE-502) | Deserialize only through safe document APIs; disallow arbitrary types and custom hooks; use versioned schemas and integrity checks | Supply crafted payloads for each deserializer; assert loading fails and execution does not occur |
| Running `npm`, `pip`, `go`, `cargo`, `mvn`, or other package tooling on the repository | Dependency confusion, malicious install scripts, or exfiltration | Do not build or resolve dependencies during analysis; treat lockfiles as static data; use offline vendored copies where necessary | Place a malicious `postinstall` script and an untrusted registry entry in the tree; assert no subprocess or network call occurs |
| Git hooks, workflow files, Make targets, or `package.json` scripts | Native execution of attacker content (CWE-829) | Parse hooks and workflows as inert text; never invoke `.git/hooks`, CI commands, or repository-supplied automation | Add `post-checkout` and `pre-commit` hooks; assert they are never executed and their paths are not trusted as plugins |
| Passing repository-supplied environment variables or secrets to a process | Credential disclosure or privilege escalation | Clear the environment except for an explicit allowlist; do not read `.env`, vault files, or cloud-metadata values from the repository | Include a hook or script that reads `AWS_`, `GITHUB_TOKEN`, and similar variables; assert the subprocess environment does not contain them |
| Argument-list overflow or unbounded subprocess fan-out | Resource exhaustion or shell invocation failure | Bound concurrency, total subprocesses, and argument length; aggregate work where possible; enforce timeouts and reap children | Generate hundreds of findings and filenames; assert subprocess counts and argument lengths stay within limits |

**The safe subprocess rule is: trusted executable, untrusted argument, no shell.** A fixed built-in program may be trustworthy, but a repository path is not. Likewise, a repository may supply a path to a binary without that binary becoming trustworthy. If a path is executable only because it resides in the repository, the repository has effectively chosen the program to run. The implementation should therefore resolve every executable independently of repository content and open every input as data.

**Argument injection must be handled even when no shell is present.** A repository string beginning with `-` or `@` may be parsed as an option by the child program. Passing arguments as a list rather than a string prevents shell expansion but does not automatically prevent option parsing. The tool should place a `--` separator before positional arguments where the target executable’s interface supports it, and should reject dangerous-looking filenames or sanitize them according to a documented policy.

## 5. ReDoS defenses must assume every repository string can induce worst-case backtracking

**Catastrophic backtracking is a remote or local denial-of-service primitive when the attacker controls either the regex or the matched text.** An attacker may contribute source text, Markdown, JSON, TOML, YAML, filenames, commit messages, or log lines that contain repeated characters. If a vulnerable pattern contains overlapping alternation, repeated groups, or backreferences, evaluation time may rise exponentially rather than linearly with input length. The tool must therefore treat matching as a potential worst-case operation even when the regex itself is built into the analyzer.

Mitigations should address both inputs and patterns. Use deterministic finite automata or engines with atomic groups and possessive quantifiers where available. Prefer simpler anchored character classes and avoid overlapping alternation. Do not let repository configuration add, modify, or compile patterns. Precompile every built-in pattern during startup and reject any pattern that uses dangerous features. Enforce a per-match step limit or timeout, and replace repeated matching across the same file with a single linear scan where feasible.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|-------|--------|---------------------|------------------------------------------|
| Overlapping alternation or nested quantifiers | Near-hang on crafted source files (CWE-1333) | Audit patterns with a ReDoS scanner; use bounded or DFA-style engines; impose a global matching budget and a timeout watchdog | Build the classic `a¹⁶!` pattern and equivalents in the tool’s engine; assert completion within a few seconds and within the step budget |
| Repository-supplied regex in configuration | Attacker-chosen pattern with unbounded behavior (CWE-94) | Do not accept regex from repositories; if custom rules are needed, sign and review them as trusted policy; compile them at startup only | Add a repository configuration field that supplies a regex; assert it is rejected by schema validation |
| Backreferences and lookaround | Quadratic or exponential matching | Disable or restrict those features unless the engine guarantees linear-time execution; replace them with targeted parsers | Use patterns containing backreferences and overlapping lookahead; assert policy rejection or bounded execution |
| Repeated scanning of the same file | Multiplicative CPU amplification | Scan each accepted file once; share matches through a structured result cache; subtract per-file overhead from the global budget | Create one huge file and many rules; assert total time is bounded and each byte is processed a limited number of times |
| Unicode case folding or normalization inside matches | False boundaries and unexpected slowdown | Match on original bytes where appropriate; normalize deliberately; document Unicode handling; avoid hidden case-insensitive traversals | Include Greek, Cyrillic, and emoji sequences with different normalization forms; assert deterministic behavior and bounded execution |
| Greedy multi-line patterns over huge files | Latency and memory spikes | Reject or chunk files before matching; set line-length and offset limits; stop after the first policy-relevant match where appropriate | Create a single-line file without a newline and a pattern requiring repeated backtracking; assert it is dropped at the file-size boundary |

A ReDoS regression suite should be part of every release. It should include known evil patterns, generated repetitions, adversarial source files, fuzz-generated text, and files that exercise both matches and non-matches. The suite should fail when the worst-case match exceeds a deterministic budget, when a pattern is added without review, or when the matching engine changes.

**Safe loaders and safe parsers do not make regex safe.** `safe_load` prevents object construction, but it does not prevent a valid string from later reaching a vulnerable pattern. Schema validation checks types and values, but it does not bound matching time. Each of these controls addresses a different layer: deserialization safety, semantic validation, and execution complexity must be enforced separately.

## 6. Offline analysis still requires quotas, read-only access, and process isolation

**The primary resource threat is not malice alone but the combination of malice and a shared workstation.** A hostile repository can create huge files, deeply nested directories, long lines, millions of small entries, or pathological parser input. Even without code execution, it can monopolize CPU, memory, file descriptors, or time. If the analysis runs in CI, this can waste runner capacity or delay trusted jobs. If it runs on a developer machine, it can interfere with other processes. Quotas must therefore be mandatory, not optional performance hints.

Every scan should begin with an accounting snapshot and a deadline. File discovery, document parsing, matching, reporting, and subprocess activity should each receive an explicit budget. Long-running operations should support cancellation. When a budget is exhausted, the tool should record the responsible limit and artifact—for example, file size, parse depth, or match count—rather than terminating silently.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|-------|--------|---------------------|------------------------------------------|
| Huge text or binary files | Out-of-memory error, swap use, or long reads | Measure file size before reading; enforce a default maximum such as 1–10 MiB; use streaming line or chunk readers; never load the entire repository into memory | Create files of 1 MiB, 100 MiB, and 10 GiB; assert only the allowed prefix is read and the tool exits cleanly |
| Extremely long lines | String-buffer blow-up or slow line splitting | Enforce a maximum line length; break scanning into fixed buffers; record the offending line number and truncation point | Generate a single-line 1 GiB file; assert it is skipped at the line boundary |
| Massive directory breadth or depth | Walk latency, descriptor exhaustion, or stack overflow | Enumerate in bounded batches; limit depth and total entries; use iterative traversal; cap open file descriptors | Create 1,000,000 entries and a 10,000-deep tree; assert completion within budget and no descriptor leak |
| Archive, git-pack, or compression bombs | Resource exhaustion after one small entry | Do not decompress repository contents unless explicitly requested; bound decompressed bytes, entries, and ratios; restrict archive formats | Add a small compressed file that expands to many gigabytes; assert it is not opened or is rejected by the format policy |
| Fork or subprocess flood | Runner starvation or denial of service | Serialize external calls; pool with a concurrency limit of one unless explicitly configured; cancel after timeout; reap children | Simulate slow external programs and rapid retries; assert the concurrency and deadline are enforced |
| Temp-file or cache growth | Disk full or cross-job contamination | Use a private, short-lived temporary directory; set disk quotas where available; remove temporary files even after cancellation | Run repeated scans and inject write failures; assert the tool cleans up and reports the failure |
| CPU or wall-clock monopolization | Job failure or inability to scan other work | Set a per-scan deadline and per-rule CPU accounting; abort remaining work cleanly; emit a diagnostic rather than a finding | Create a CPU-intensive pathological match or parse workload; assert the global deadline is honored |

**Least privilege must be the default execution environment.** The tool should run as an ordinary, dedicated user; read only the scan root; and write only to an explicit output location. If it is invoked inside CI, it should use an isolated runner for pull requests from unknown authors. Self-hosted runners should be ephemeral where practical. No repository-controlled script should be able to read the token used to fetch the repository.

The implementation should separate read-only discovery, optional trusted processing, and output writing into distinct phases. It should not rely on repository permissions to enforce security. Even a world-readable sensitive file outside the scan root should remain outside the tool’s authorized namespace.

**“Offline” must be verifiable, not merely documented.** Builds should be reproducible without network access. All checksums, signatures, rules, and dependencies should be resolved before the scan. A repository file or configuration should never trigger an update, lookup, download, webhook, or DNS resolution.

## 7. Untrusted text must be rendered through encoding, neutralization, or explicit confirmation

**Display and reporting are security-sensitive transformations.** Repository text may contain escape sequences, bidirectional overrides, homoglyphs, zero-width characters, null bytes, or control characters. If such text reaches a terminal, log aggregator, web viewer, issue tracker, or LLM without isolation, it can spoof filenames, conceal code, manipulate a human reviewer, or corrupt structured output. The appropriate control depends on the destination: terminals require filtering, bidirectional text requires disclosure or isolation, and structured formats require schema-compliant encoding.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|-------|--------|---------------------|------------------------------------------|
| ANSI/CSI/OSC escape sequences in source, filenames, or findings | Terminal hijack, prompt spoofing, fake output, or hidden content (CWE-150) | Strip or escape control bytes below 0x20 and 0x7F; remove CSI, OSC, DCS, and similar sequences; use a terminal-safe writer or `--plain` mode | Embed `\x1b[31m`, `\x1b]0;...`, and cursor-movement sequences; assert plain output contains none and color is produced only by the tool’s own writer |
| Bidirectional overrides and zero-width characters | Hidden malicious code or misleading filenames (CWE-451) | Preserve original bytes for evidence; surface invisible or bidi codepoints in a separate “display anomalies” report; avoid rendering raw source in security-sensitive contexts | Include U+202E, U+200B, and U+2066 in identifiers; assert the report exposes the anomaly and no logical code is hidden in rendered output |
| Homoglyphs and IDN confusion | False attribution, misleading package or domain findings | Canonicalize identifiers using Unicode confusable data where relevant; display both original and ASCII-transcribed forms; flag mixed-script identifiers | Use Cyrillic `а` and Latin `a` in a package name; assert both code points and confusable status are recorded |
| Encoded newlines or control characters in filenames | Log forgery, terminal desync, or argument injection | Reject or escape control characters according to destination; do not use filenames in shell commands; use a safe logging encoder | Use newlines, tabs, CR, and escape bytes in filenames; assert logs remain single-record and arguments remain positional |
| Null-byte injection | Truncated string confusion or C-interop bug | Reject null bytes at input boundaries unless explicitly allowed; preserve byte strings through FFI; use explicit length arguments | Insert `\0` into a filename or JSON string; assert safe rejection or correct handling |
| Newlines in JSON, SARIF, or Markdown fields | Report injection, broken toolchain, or XSS (CWE-74 / CWE-79) | Use the format’s standard encoder; do not concatenate strings into JSON; validate generated files with a JSON parser and JSON Schema | Include quotes, backslashes, newlines, `<script>`, and control bytes in a message; assert they are escaped and the document re-parses |
| Repository-controlled rule IDs, severities, or URLs | Policy bypass, cache poisoning, or spoofed links | Restrict these fields to tool-defined enumerations and an allowlist; never interpret repository strings as policy | Add `../../etc`, `javascript:`, and `rule: rm -rf` values; assert they are rejected or emitted as inert strings |

**The terminal is an output device, not a sanitizer.** A library may faithfully reproduce every byte it receives, including escape sequences that move the cursor, rewrite the prompt, or execute terminal-specific commands. Filtering must occur before text is written. A robust implementation should use a hardened encoder for untrusted strings or a plain mode that maps non-printable bytes to a visible placeholder.

A safe display contract should include the following controls:

- Allow only a fixed palette of tool-controlled styling codes.
- Remove CSI, OSC, DCS, SOS, PM, APC, and similar sequences.
- Replace control characters outside the allowed display set with a visible placeholder.
- Preserve original evidence separately from rendered output.
- Prevent repository content from opening hyperlinks, changing window titles, or executing terminal features.
- Keep unsafe raw output out of logs, terminal recordings, and HTML previews.

**Bidirectional text should produce an explicit disclosure rather than silent normalization.** Normalizing identifiers can change evidence, hide differences, or introduce collisions. The safer approach is to retain the original codepoints, flag suspicious directionality, and show the logical and visual representations separately. Where automated repair is necessary, every change should be auditable.

## 8. Safe serialization prevents injection, but a valid report is not necessarily a correct report

**Output formats should be produced through format-native serializers and then validated.** Markdown should be rendered through a hardened Markdown library or explicit escaping. JSON and SARIF should be generated from typed objects and written through a standard JSON serializer. None of these formats should be assembled by string concatenation. After writing, the tool should re-parse the artifact with a strict parser and validate it against the declared schema. This protects downstream consumers from malformed or malicious repository content, but it does not establish that the findings are true.

SARIF is a JSON-based format for exchanging static-analysis results. Its security depends on both correct JSON encoding and adherence to the published schema. A repository must not supply JSON syntax, schema version, property names, or output destinations. Rule identifiers, severity levels, result messages, and locations should be drawn only from the trusted analyzer policy. Messages should contain literal values or structured arguments supplied to a serializer; they should never be evaluated as templates.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|-------|--------|---------------------|------------------------------------------|
| Unescaped snippet, path, or message in Markdown | XSS, prompt injection, or fake findings in a viewer (CWE-79) | Escape HTML and Markdown special characters; disable raw HTML and autolinks; use a renderer built for untrusted text | Include backticks, `<script>`, headings, and link syntax; assert the output renders them as inert text |
| Manual JSON or SARIF construction | Syntax breakage or finding injection (CWE-94) | Use a JSON library and SARIF object model; validate against the schema; make unknown fields non-injectable | Include braces, quotes, newlines, and `../` in a snippet; assert the document remains valid and contains no structural injection |
| Repository-controlled SARIF properties or rule metadata | Schema confusion or renderer exploitation | Allow only a reviewed subset of properties; use enumerations; sign or hash embedded content if provenance matters | Supply `rules`, `partialFingerprints`, and unknown extension keys; assert they are rejected or isolated from policy |
| Path confusion in report locations | Wrong-file attribution or hidden evidence | Store repository-relative paths with a fixed root URI; canonicalize; include byte offsets rather than relying on mutable line text | Create symlinked and absolute-path findings; assert the report uses the authorized relative path and root |
| Unsafe temporary report location | Symlink overwrite or world-readable sensitive data | Write only to an explicit, private, symlink-free output path; set restrictive permissions; create the directory safely | Pre-create a symlink at the output path; assert the write fails and no linked target is modified |
| Exfiltration through report fields | Secret disclosure in CI artifacts or logs | Redact secrets before rendering; allow only known fields; prevent whole-file snippets by default; review field additions | Add a fake secret to source; assert it is masked and does not appear in stdout, logs, or JSON |
| Downgrade of SARIF schema or malformed artifact | Toolchain failure or incorrect gating | Pin and validate the schema version; verify required fields and types; run a contract test on every change | Alter the schema version or remove a required field; assert validation fails before the report is published |

**CI should not trust the report merely because it parses.** The report should be verified independently of the tool that produced it. Verification should confirm schema validity, structural integrity, provenance, and policy compliance before the report becomes a release gate. The producer’s exit code is a convenience signal; it is not a substitute for evidence.

A CI gate should therefore validate at least the following properties:

1. The report exists and conforms to the declared SARIF or JSON schema.
2. All rule IDs, severity levels, and result locations are well-formed.
3. The file hash or signature matches the expected release artifact.
4. The report was produced by an authorized binary or policy bundle.
5. The policy outcome distinguishes blocking errors from internal failures and resource violations.

If any of these checks fails, the workflow should treat the result as inconclusive rather than passing or failing on the raw exit status alone.

## 9. Exit codes must express policy outcome, while a plugin model must keep execution explicit and narrow

**Exit-code semantics must remain stable across releases and error classes.** Otherwise, a change in parser behavior, logging level, resource limit, or operating-system interaction can silently alter CI gating. The CLI should define exactly one success code and small set of failure codes, such as configuration failure, internal failure, resource exhaustion, and policy violation. Internal failures must never be collapsed into success. A scan that detects zero issues is not the same as a scan that could not complete.

CI should map the exit code to a policy only after verifying that the scan finished, the report is valid, and the intended policy version was used. The tool should support dry-run and explain modes so that administrators can inspect mapping changes without exposing repository contents.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|-------|--------|---------------------|------------------------------------------|
| `0` returned on internal error | Silent policy bypass | Return a distinct internal-error code; treat non-zero codes as scan failures; never infer success from stderr | Inject a parser crash; assert the exit code indicates internal failure and CI does not pass |
| Exit-code meanings change between releases | Brittle or incorrect CI gates | Freeze a machine-readable exit-code contract; add compatibility tests; document deprecation | Run historical invocations against new binaries; assert codes and stdout contracts remain stable |
| Repository content changes the policy or severity | Attacker-controlled blocking behavior | Keep policy in a signed, read-only configuration outside the repository; validate it before scanning | Add a policy file inside the repository; assert it is ignored and no rule or severity changes |
| Secrets embedded in debug output | Credential disclosure | Keep secret scanning off by default; redact values; write verbose logs to a private location; avoid full-file dumps | Include fake tokens in source and filenames; assert they are masked across all verbosity levels |
| Repository-controlled crash reports or bug URLs | Phishing or outbound request | Do not interpret text as URLs; disable bug reporting unless explicitly configured by the operator | Add `https://attacker` to a diagnostic message; assert no outbound request occurs |
| Binary diff, provenance, or signing weakness | Forged or tampered release | Reproducibly build releases; sign artifacts; verify hashes and signatures before execution; pin dependencies | Modify a distributed binary or report; assert verification fails |

**A plugin system must never import or execute code from the analyzed repository.** The safe default is static analysis without plugin loading. If extensibility is necessary, built-in extension points should use a restricted domain-specific language or data-driven rules. Dynamic code must be limited to an administrator-controlled, out-of-tree, digitally signed plugin directory.

Each plugin should be identified by a fully qualified name, exact version, and content hash. Its permissions should be declared in advance and limited to analysis-only operations. It should not access the network, execute subprocesses, write outside its private state directory, or modify other analyzers. Its lifecycle—installation, update, enablement, and removal—should be reviewed as a supply-chain change rather than as ordinary user configuration.

| Plugin threat | Impact | Mitigation | Regression test |
|---|---|---|---|
| Repository-supplied analyzer loaded automatically | Arbitrary code execution (CWE-829) | Ignore `plugins/`, `.analysis/`, and import paths inside the repository; load only from an explicit trusted directory | Place a Python or shared-library file in the repository; assert it is never imported or `dlopen`ed |
| Unsigned or tampered plugin | Supply-chain compromise | Require signature verification, hash pinning, and an allowlist; verify before import | Alter a plugin after signing; assert the loader rejects it |
| Plugin with overly broad filesystem access | Read or overwrite outside the scan | Run the plugin in a separate process or capability-restricted environment; deny network and shell access | Attempt reads and writes outside the scan root; assert they fail |
| Plugin panic, slow loop, or memory error | Host crash or denial of service | Isolate the plugin in a subprocess; enforce time, memory, and finding quotas; restart cleanly | Create an infinite loop or malformed output; assert the host remains responsive and collects diagnostics |
| Plugin with access to the repository token | Secret leakage | Pass no credentials, environment variables, or network proxies to plugins | Inspect the subprocess environment and packet traffic; assert no token or network access exists |

The security of a plugin system is determined less by the language used than by the execution contract. A memory-safe language still allows path traversal, file overwrite, network access, and resource exhaustion. Every privilege given to a plugin should therefore be justified, declared, and tested; broad access should be the exception rather than the default.

## 10. Telemetry must be opt-in, local, and incapable of remote exfiltration by design

**Privacy is a security property, not a documentation claim.** An offline security tool can still collect and transmit filenames, source snippets, dependency graphs, rule configuration, error messages, system details, crash reports, or version information. The safest design transmits none of this by default. The implementation should not initialize a network client, read cloud credentials, or construct remote URLs during ordinary analysis.

Privacy and offline behavior should be enforceable at the build and test levels. The network surface should be auditable from the dependency graph, fuzzed for outbound calls, and verified through a system-call monitor. “No telemetry” should mean that no telemetry path exists on the default execution path—not that telemetry is conditionally disabled.

| Threat | Impact | Concrete mitigation | Regression test that catches a regression |
|-------|--------|---------------------|------------------------------------------|
| Phone-home analytics or crash reporting | Confidential source, filename, or dependency disclosure | Omit networking from the default binary; make remote features opt-in and separately installed; require explicit confirmation | Run the tool under a syscall tracer; assert no socket, DNS, or HTTP call occurs |
| Secret collection through verbose logs | Credential leakage | Do not log file contents; redact sensitive patterns; store logs in a private location | Include fake keys and tokens; assert they are masked in stdout, files, and error messages |
| Local telemetry or cache reuse across users | Cross-user data disclosure | Store local state in a private directory; restrict permissions; support a clean-state mode | Inspect cache and log permissions; assert other users cannot read them |
| Repository-controlled telemetry endpoint | Attacker-chosen exfiltration destination | Never read endpoints from repository files; configure them only through user-supplied settings | Add an endpoint URL to configuration; assert it is rejected |
| Accidental transitive dependency network call | Violation of the offline guarantee | Minimize dependencies; vendor or pin them; block network at the process or CI level; audit lockfiles | Run a full scan under a network deny rule; assert zero DNS or socket calls |

**The default must be no telemetry, no analytics, and no remote schema fetches.** Repository input, configuration, environment, diagnostics, versions, and crash information are sensitive. Even a hash or file count may reveal information about proprietary source. If an optional support mode is offered, it should collect only a reviewed, bounded manifest; store it locally; and require a deliberate user action. It should never be triggered by repository content or a successful scan.

The implementation should separate three reporting modes:

- **Local machine-readable results:** for downstream automation.
- **Operator-selected support bundles:** limited to reviewed non-source metadata.
- **Remote upload:** disabled unless explicitly enabled and separately configured.

This separation prevents an apparently harmless local artifact from becoming an exfiltration channel.

## 11. Correctness requires independent evidence and calibration, not just robustness

**A robust tool can still be analytically wrong.** The consequences depend on the failure direction. False negatives weaken security by omitting real defects. False positives weaken trust by training operators to ignore findings, require costly triage, or induce suppression rules that disable valid analysis. Either failure can make the tool unsuitable as a CI gate, but neither is necessarily a traditional vulnerability.

The threat model should therefore treat analytical correctness as a quality and assurance property. The implementation should provide deterministic reproduction, baseline comparison, confidence metadata, and a documented process for handling disagreements. Severity must be distinguished from blocking status: a high-confidence defect may be advisory, while a low-confidence defect may be configured as blocking only after review.

| Risk | Why it undermines trust | Mitigation | Regression test |
|---|---|---|---|
| False negatives from parser errors | A skipped file hides a real defect | Track parse coverage separately from scan completion; emit a missing-coverage metric; use language-appropriate parser error recovery | Intentionally break a source file; assert it is reported as unparsed rather than silently absent |
| Parser error recovery introduces wrong ASTs | An incorrect program is analyzed | Preserve the original text; require explicit error-recovery policy; re-validate suspicious regions | Create ambiguous syntax; assert findings include the parser-error status and do not claim certainty |
| Generic patterns cause false positives | Users ignore or suppress the entire rule | Calibrate rules against curated true-positive and false-positive corpora; expose confidence; require contextual checks | Run rule updates over a benchmark; assert precision remains above a defined threshold |
| Baseline drift | A previously reviewed issue is silently reintroduced | Store a stable baseline of reviewed findings; compare hashes or stable fingerprints; require approval for newly ignored findings | Revert a fix; assert the regressed issue reappears and is not auto-suppressed |
| File-extension or glob mismatch | Files are scanned out of context or missed | Use explicit include and exclude policies; treat language detection as advisory; verify with explicit tests | Rename files across languages; assert expected inclusion and the absence of accidental coverage |
| Generated or vendored code changes findings | Noise or missed defects in authoritative code | Configure generated-code handling with ownership and review; keep it separate from ordinary suppression | Add a generated-source marker; assert policy treats it as configured, not silently ignored |
| Deterministic reproduction failure | Findings cannot be audited | Record tool version, rule set, configuration hash, and relevant operating-system details; support a replay mode | Run the same scan twice; assert outputs match after permitted timestamps are normalized |
| LLM- or heuristic-generated explanations | Persuasive but incorrect root-cause claims | Label uncertain explanations; require primary evidence and code citations; prevent model output from changing the exit code | Inject a contradictory heuristic; assert it cannot create or suppress a finding |

**False-positive and false-negative rates should be measured against independent ground truth.** The tool should maintain versioned benchmark repositories and known-answer tests. Rule changes should be evaluated on both clean and buggy samples before promotion. A new rule that increases recall but dramatically reduces precision may do more harm than good if it causes reviewers to suppress the rule.

Human review remains necessary for high-impact findings. The report should expose the evidence required to reproduce each result, including the rule version, matched text, and location. It should not present unverified explanations as certainties.

## 12. A hardened lifecycle must combine compile-time checks, runtime controls, and adversarial regression gates

**Secure development is part of the runtime security boundary.** Unsafe languages, dynamic parsing, ambient authority, and weak dependency controls can all transform malformed repository input into exploitable behavior. The implementation should minimize language interop, isolate FFI, pin and review dependencies, and avoid dynamic code where a data model is sufficient.

Every change to parsing, filesystem handling, matching, output, or plugin loading should require security-sensitive review. The release process should generate a software bill of materials, verify provenance, and run the adversarial suite before signing artifacts.

| Activity | Minimum control | Evidence or artifact |
|---|---|---|
| Filesystem access | No recursive deletion; read-only default; explicit output directory | Permission, path, and syscall tests |
| Parsing | Safe document APIs; schema validation; depth and size budgets | Fuzz suite and malformed-document tests |
| Matching | Precompiled patterns; ReDoS scanning; time and step budgets | Evil-pattern and adversarial-file suite |
| Process execution | No shell; fixed executable; no repository arguments as options; isolated user | Argument-injection tests and syscall traces |
| Output | Native serializer; schema validation; redaction | JSON/SARIF/Markdown contract tests |
| Resource control | CPU, memory, time, file, and finding quotas | Quota and cancellation tests |
| Privacy | No telemetry in the default binary; opt-in local-only mode | Network and dependency audits |
| Supply chain | Signed, pinned dependencies; reviewed plugin allowlist | SBOM, signature verification, and lockfile review |

**Fuzz testing should target each input parser and the complete CLI.** Test cases should include Markdown, JSON, TOML, YAML, paths, filenames, Git trees, archive entries, terminal sequences, and malformed UTF-8. Coverage-guided fuzzing should run with address, memory, and undefined-behavior sanitizers where available.

Release criteria should require the following conditions:

- Every fuzz bug is fixed and regression-tested.
- Every malicious-document test completes within budget.
- No repository-supplied input reaches a shell, template engine, or deserializer.
- No repository-controlled value changes policy.
- The tool makes no outbound network call on the default path.
- Every report remains valid after re-parsing.

**The residual risk is substantial enough that CI must provide additional isolation.** The tool is not a sandbox. It operates with the invoking user’s authority and may be exposed to malicious filesystem content, a vulnerable language runtime, or a compromised dependency. CI should therefore use ephemeral runners for untrusted pull requests, grant the scan only read access to the repository, and avoid exposing release secrets to the scanning job.

If the tool must write files, it should do so only in an isolated workspace. Sensitive release decisions should not rely solely on the scan exit code. The recommended layered control is:

1. Run the tool in an isolated environment.
2. Verify the report schema and structural integrity.
3. Verify the report’s provenance and policy version.
4. Apply human review to high-impact or uncertain findings.
5. Use the report as evidence within a broader release gate.

## 13. The minimum secure architecture is analysis-only, read-only, bounded, and independently verifiable

**The correct security stance is “analyze only, then write only where explicitly permitted.”** A safe invocation begins with an explicit, canonicalized repository path and an explicit output path outside that repository. The scan runs with an ordinary unprivileged account, read-only access to the repository, no network, and no shell access. It rejects symlinks, special files, and escaped paths; applies uniform size and complexity limits; parses documents safely; encodes every report field; and produces a separately validated result.

Exit codes, report schemas, and release gates should be decoupled. Internal failure, resource exhaustion, policy violation, and clean completion must produce distinct outcomes. A successful analysis should not be inferred from the absence of an error, and a valid report should not be inferred from a non-zero exit code alone.

| # | Requirement | Verification |
|---|---|---|
| 1 | Only the resolved scan root is readable | Syscall and path-containment tests |
| 2 | Symlinks, hardlinks, devices, FIFOs, and sockets are excluded by default | Filesystem corpus tests |
| 3 | No shell or target code execution occurs | Tracer, plugin audit, and repository-hook tests |
| 4 | All regex and parsers are bounded | ReDoS and fuzz suites |
| 5 | Every output field is serialized and validated | SARIF/JSON/Markdown contract tests |
| 6 | Repository text never reaches the terminal unfiltered | ANSI and control-character tests |
| 7 | No telemetry or network access exists on the default path | Network-deny tests and dependency review |
| 8 | Exit-code meanings are stable and narrow | Exit-code contract tests |
| 9 | Plugins are separately installed, signed, and isolated | Plugin lifecycle and permission tests |
| 10 | Resource limits are mandatory and cancellation-safe | Quota, deadline, and cleanup tests |

The final threat-model judgment is that the architecture can be made robust, but it cannot be made self-certifying. Local execution reduces the network attack surface without eliminating it. Resource controls reduce the denial-of-service blast radius without removing all complexity. Safe parsing and output encoding reduce injection risk without proving that findings are correct.

Security, correctness, and operational integrity must therefore be evaluated separately. The repository remains hostile data; the CLI remains a privileged workstation process; and downstream automation remains responsible for independently verifying reports, provenance, and policy outcomes.

## Data sources

1. **JSON: The JSON Data Interchange Syntax**  
   https://www.json.org/json-en.html

2. **TOML v1.0.0**  
   https://toml.io/en/v1.0.0

3. **OWASP: Regular Expression Denial of Service — ReDoS**  
   https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS

4. **OWASP: Path Traversal**  
   https://owasp.org/www-community/attacks/Path_Traversal

5. **OWASP: Deserialization of Untrusted Data**  
   https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data

6. **OWASP Top 10 2025: A08 — Software or Data Integrity Failures**  
   https://owasp.org/Top10/2025/A08_2025-Software_or_Data_Integrity_Failures/

7. **Python Documentation: `subprocess` — Subprocess Management**  
   https://docs.python.org/3/library/subprocess.html

8. **Python Documentation: `tomllib` — Parse TOML Files**  
   https://docs.python.org/3/library/tomllib.html

9. **YAML Official Website**  
   https://yaml.org/