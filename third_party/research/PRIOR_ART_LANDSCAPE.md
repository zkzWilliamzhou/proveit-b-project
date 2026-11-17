# Prior-Art Landscape for a “Software Honesty Auditor”

## Executive conclusion

A general-purpose, offline, deterministic, language-agnostic “software honesty auditor” that accepts a project’s README, docs, and metadata as claims, checks them against both source code and executed behavior, emits only **VERIFIED / CONTRADICTED / UNVERIFIABLE**, and also supports a two-version behavior-diff mode does not appear to exist as a mature, maintained open-source tool. The strongest prior art is **fragmented across several mature tool families** rather than unified: documentation-drift checkers extract and verify some claims; SBOM/SCA and license tools inventory software and metadata; static analyzers detect potentially telemetry- or network-related code patterns; runtime monitors observe actual network, filesystem, and process behavior; and differential fuzzers or differential executors compare two program versions. None of the directly relevant projects verified here simultaneously combines all six hard requirements.

The closest recent work includes **Docverity**, which extracts documentation claims and pairs a deterministic reference engine with an LLM-backed claim verifier; **Receipts**, which uses a local model for extraction and deterministic code for a four-state verdict; **claimcheck**, which uses concrete tests and a structured-evidence model; and **openworkers**, which audits README claims with an extract–research–check pipeline. These are meaningful prior art for claim extraction, evidence-bearing findings, and verdicts, but each falls short of the requested complete specification: LLM dependence, limited claim ontology, no cross-language runtime-behavior policy, absence of two-version behavior diffing, or insufficient documentation to confirm maintenance and reproducibility. Likewise, runtime tools such as **airgap-check**, **BHEESHMA**, **Tracee**, and behavior-manifest concepts can observe or specify behavior, but they do not claim to adjudicate prose claims from a README against evidence.

The proposed combination is therefore **not obviously preempted in full**, and a defensible novelty case can be made around the integrated claim ontology, source-and-behavior evidence model, strict three-verdict semantics, offline-deterministic execution policy, and release-to-release behavior diff. That novelty is **conditional, not absolute**: it depends on demonstrating actual language-agnosticism and determinism, on producing reliable evidence for unruly claims such as “privacy first,” and on showing that the behavior-diff mode is more than a generic differential executor with a marketing layer. Several recent projects were sparsely documented or had repository access restrictions, so this conclusion is a diligent “not found / not verified” rather than a guarantee that no unpublished, private, proprietary, or very new tool exists.

## 1. The requested tool is a bundle of six distinct technical capabilities

The proposal is not a single conventional linter or scanner. It combines (1) documentation parsing and claim extraction; (2) claim-to-evidence reasoning; (3) static and dynamic evidence gathering; (4) a strict three-valued verdict; (5) reproducible offline execution; and (6) differential analysis between two software versions. Existing tools generally specialize in one or two of these planes. Treating them as interchangeable obscures the real gap: the novelty is architectural integration, but each component has substantial prior art.

A useful way to express the target is as a pipeline:

`document claim → normalized claim type → static evidence → dynamic evidence → policy → {VERIFIED, CONTRADICTED, UNVERIFIABLE}`

The tool must then serialize a second pipeline:

`version A → observed behavior profile` and `version B → observed behavior profile → semantic diff → evidence-linked change report`.

The proposal’s most demanding constraints are not “produce a report” but the interaction of constraints. For example, “offline” must cover model inference, dependency installation, SBOM feeds, vulnerability databases, and remote package metadata. “Deterministic” must mean that identical tool, rules, OS baseline, inputs, and executed artifacts produce equivalent claims and verdicts; it cannot mean that arbitrary software is deterministic. “Language-agnostic” must mean the orchestration layer works across ecosystems, even if some deep semantic checks remain language-specific. And “behavior diff” must distinguish source change, executable divergence, observed-environment divergence, and meaningful semantic-behavior change.

| Requirement | What the tool must do | Why it is hard |
|---|---|---|
| Documentation input | Parse README, other docs, manifests, and metadata | Marketing prose is ambiguous; exact claim boundaries are unclear |
| Static evidence | Find file/line definitions, imports, config keys, calls, and build/test artifacts | Same concept has many syntactic and framework-specific encodings |
| Dynamic evidence | Run the program safely and observe behavior relevant to a claim | Programs have environment-dependent, nondeterministic, or dangerous behavior |
| Verdict semantics | Only VERIFIED, CONTRADICTED, or UNVERIFIABLE | A probabilistic model score or finding severity is not a valid verdict |
| Offline guarantee | No network at audit time, with locked inputs and recorded nondeterminism | Toolchains and dependencies routinely fetch resources |
| Behavior diff | Compare semantically typed behavior between two releases | Differences include false positives, nondeterminism, and uncovered code paths |

The most credible novelty claim is therefore not “a linter for READMEs,” but a **claim-centric audit kernel with an evidence model that spans both static source facts and controlled runtime observations**, governed by explicit incompleteness rather than a generic risk score.

## 2. Claim-focused documentation auditors are the nearest prior art, but none clears all requirements

The nearest tools show that the field has moved beyond checking Markdown syntax into extracting and validating assertions. They still do not provide the requested full-system guarantee.

### 2.1 Docverity is the strongest direct evidence that claim-to-source auditing is an active design space

**Docverity’s reference checker is deterministic and language-agnostic, but its semantic verifier and broader operation are not the proposed tool.** Docverity documents a reference-checking engine that searches the source tree for files, CLI flags, environment variables, and symbols. It also documents an LLM-backed claim verifier, a coverage direction from code to docs, narrative checks, and git-history awareness. It supports Markdown, reStructuredText, AsciiDoc, and plain text, and its reference checker is described as language-agnostic while its coverage checks detect environment variables and flags in several languages. This overlaps strongly with claim extraction, reference verification, code-to-docs coverage, and CI-style reporting. It also reports errors and warnings rather than only the requested three verdicts [1].

Docverity is important prior art because it has already identified the asymmetry between checking code blocks and checking prose. Its reference engine could support “symbol exists” or “file exists” claims; its model-assisted verifier targets behavioral or semantic prose; its coverage pass seeks undocumented behavior. However, its model-assisted pass introduces external dependence and nondeterminism that the requested design explicitly excludes. More importantly, the retrieved documentation describes behavior observation primarily through source-code and git evidence, not a controlled execution harness and release-diff mode. The package listing also indicates it is a relatively new, single-maintainer project; that does not make it irrelevant, but it weakens any assumption that it is a mature community standard [2].

### 2.2 Receipts demonstrates local AI extraction plus deterministic adjudication, but not general source/behavior verification

**Receipts proves that a four-state evidence report is feasible, but it is scoped to documentation, configuration, results, and datasets rather than arbitrary source-and-runtime behavior.** It uses an Ollama-hosted local model to extract claims and deterministic code to decide among **VERIFIED, CONFLICT, AMBIGUOUS, and UNVERIFIABLE**. Its report includes provenance and it avoids sending documentation to a remote model. This is conceptually close to the requested verdict model and its local-first design addresses part of the privacy and offline concern [3].

The overlap is significant but not complete. Receipts does not execute the target project and does not appear to provide a two-version behavior diff. Its verdict set is not the requested three-state set: **AMBIGUOUS** and **CONFLICT** are distinct outcomes. Its local model still makes extraction nondeterministic unless prompts, weights, sampling, and runtime are pinned and validated. The available primary-style write-up is also an author’s project description rather than a peer-reviewed source or exhaustive specification, and direct repository access was unavailable during research. These limits matter because the proposal’s claim space includes executable assertions such as “no telemetry” and “works offline,” which Receipts does not observe dynamically.

### 2.3 claimcheck is rigorous about falsifiable claims, but focuses on agent transcripts and tests

**claimcheck narrows the audit problem to claims that can be tested and avoids accepting untestable confidence as verification.** It uses tools such as `verify_guard`, `check_claim_shape`, and `evidence_digest`, with results including **KILLED, DECORATIVE, BROKEN_TEST, NO_ASSERTIONS, and REJECTED**. It runs code with guards against obviously external operations and hashes evidence so later results can be checked. This is relevant because it advances the methodological point that a passing test does not verify a claim unless the test is capable of failing when the property is absent [4].

Its relevance is narrower than Docverity or Receipts. claimcheck is an MCP-oriented verifier for claims such as “this is fixed” or “tests cover it,” not a general README/doc/metadata auditor for claims like “MIT licensed” or “zero dependencies.” It does not offer language-agnostic source-analysis rules, a controlled cross-ecosystem runtime sandbox, or a documented two-release behavior-diff mode. Its custom five-state result system is also more detailed than, and different from, the requested three-state schema.

### 2.4 openworkers and driftcheck cover claim audits or repository drift, but not the integrated target

**openworkers has a claim-to-code review pipeline, while driftcheck is primarily a deterministic state and documentation reference checker.** openworkers describes an LLM-based planner/researcher and a deterministic grep-based researcher/checker. It returns **verified, drifted, contradicted, and unsupported** outcomes and intentionally excludes the audited README from the evidence pool. driftcheck, by contrast, describes repository-state, documentation, and session-drift checks, and emphasizes zero runtime dependencies and no LLM/API calls at runtime [5][6].

Neither is the requested tool. openworkers uses an LLM stage and, based on the retrieved description, is not shown to execute target programs or diff releases. driftcheck’s advertised scope is reference existence and documentation drift; it does not claim to observe runtime behavior or to adjudicate behavioral claims. Together they show a maturing design vocabulary—claim states, evidence provenance, deterministic fallback, and repository drift—but none has yet assembled the complete stack.

![Closest claim auditors](/data/workspace/dr:research_prior_art/fig_claim_tools.png)

*Figure 1: The closest claim auditors verify documentation or claims, but do not all provide offline-deterministic claim verification and two-version behavior diffing. Data sources: project documentation and repository descriptions retrieved 2026-11-10 [1]–[6].*

The closest-tool evidence supports a precise conclusion: **document claim verification is no longer novel in isolation**. Novelty must be tied to the combination and to stricter semantics—especially the explicit exclusion of probabilistic judgments from final verdicts, the evidence graph spanning manifest/static/dynamic evidence, and the repeatable behavior diff.

## 3. README and prose linters solve document quality, not factual correspondence

Markdown and prose linters are mature and abundant, but their success criteria are different from an honesty audit. markdownlint, markdownlint-cli2, Vale, mdl, remark-lint, PyMarkdown, alex, and textlint primarily check style, structure, inclusive language, terminology, or syntax. They may catch a malformed link or inconsistent heading, but they generally do not decide whether “supports Windows” is true in the source. A 2026 academic literature review likewise separates Markdown linters that evaluate textual style from those that evaluate content or prose style; it lists Vale, alex, write-good, proselint, and textlint as adjacent approaches [7].

There is also a family of “doctest” and embedded-example tools that execute code in documentation. These tools verify runnable examples, not prose claims. Executable examples can support a small subset of claims—for instance, that a command runs—but cannot establish that a program is “privacy first” or “zero telemetry.” A passing example can also represent only one code path, while the opposite behavior may occur under a different configuration, user input, or dependency.

**The enduring gap is semantic correspondence rather than document formatting.** A general claim auditor must resolve which statement is being made, identify the artifact that can prove it, decide whether available evidence is sufficient, and express uncertainty without upgrading it into a positive verdict. This is fundamentally an evidence and verification-condition problem, not a lint rule. It is also recursive: if a tool uses a language model to extract claims, its own model output becomes an audited artifact rather than a trusted authority.

A Markdown linter can still be a useful component of the proposed system as a **front-end parser and quality gate**, but it cannot be the audit kernel. Likewise, doctest-like execution can become one evidence adapter among many, not the universal truth oracle.

## 4. SBOM, SCA, and license tools are deep prior art for inventory—not honesty verdicts

Composition-analysis and license tools provide strong evidence about dependencies, manifests, and licenses, which makes them highly relevant adapters. They do not, however, verify marketing claims or runtime behavior.

**Syft is a mature polyglot SBOM generator, not a claim adjudicator.** It generates software bills of materials from container images and filesystems, supports many packaging ecosystems, and can output SPDX and CycloneDX. It is maintained and widely integrated with Grype and the broader container-security toolchain [8]. This makes it valuable for claims such as “zero dependencies” or “no transitive network library,” but only after translating the prose claim into a defined scope: production vs. development dependencies, direct vs. transitive dependencies, bundled binaries, and generated code.

**Trivy combines filesystem, SBOM, vulnerability, misconfiguration, secret, and license scanning across many ecosystems.** Its documentation lists container images, filesystems, repositories, virtual-machine images, and Kubernetes as targets; its scanners cover dependencies, known vulnerabilities, infrastructure-as-code issues, secrets, and software licenses [9]. Trivy therefore could test a subset of dependency, secret-exposure, and licensing claims. It still operates primarily as a scanner and policy system, not as a documentation-prose auditor with a fixed three-verdict schema.

**cdxgen is a polyglot CycloneDX generator with broad language and package-format coverage.** Its documentation lists C/C++, Node.js, PHP, Python, Ruby, Rust, Java, .NET, Dart, Haskell, Elixir, Go, Docker/OCI images, GitHub Actions, Linux, and Windows targets [10]. Its breadth supports the feasibility of language-agnostic composition evidence, but it remains an SBOM generator. It cannot determine whether a README’s sentence about offline operation is true.

**ScanCode Toolkit performs detailed license, copyright, and dependency discovery in source and binary files.** It runs on Windows, macOS, and Linux and emphasizes full comparison against a license database rather than approximate matching [11]. **Licensee** detects the license of a project by comparing LICENSE-file text against known licenses and can show a diff, but explicitly does not examine dependencies or README license references [12]. These are excellent prior art for claims such as “MIT licensed,” especially when a claim must be tested against the actual license text, package manifest, and dependency tree.

| Tool family | Representative projects | Claim-type overlap | What it does not provide |
|---|---|---|---|
| SBOM / SCA | Syft, Trivy, cdxgen, Grype, Dependency-Check | Dependencies, components, vulnerabilities, licenses | Semantic correspondence to prose; behavior guarantees |
| License scanning | ScanCode Toolkit, Licensee | License identity, copyright, dependency licensing | Legal judgment; README/metadata consistency by default |
| Markdown / prose linting | markdownlint, Vale, remark-lint, textlint | Document structure and style | Evidence-based truth verdicts |
| Documentation testing | doctest-like tools | Runnable examples may execute | General claim semantics and coverage |
| Claim verification | Docverity, Receipts, openworkers, claimcheck | Extract claims; return evidence or verdict | Full offline-deterministic + dynamic + diff bundle |

**The key insight is that “MIT licensed” is actually several different auditable propositions.** It may mean: (a) the repository contains an MIT LICENSE file; (b) the LICENSE text matches a canonical template; (c) the package manifest declares MIT; (d) no source file contains a conflicting proprietary restriction; (e) all dependencies permit the intended use; or (f) attribution requirements are satisfied. A useful auditor must preserve this distinction rather than emit one binary label. This is a contribution-worthy design point, but it is also a warning: a generic “license check” can produce false confidence if the claim’s legal scope is not modeled.

## 5. “No telemetry” is already a recognizable feature category, but current tools detect narrow signals

Tools that scan for telemetry or network behavior already exist, but they are mostly registry-based, ecosystem-specific, static detectors, or runtime monitors. They do not universally prove a “no telemetry” or “privacy first” claim.

**no-telemetry is a useful opt-out checker, not a behavioral proof.** It reads a project’s `package.json`, matches direct dependencies against a curated registry, and reports whether documented environment-variable opt-outs are set. The retrieved documentation states that it makes no runtime network requests and covers a defined list of JavaScript/TypeScript ecosystem tools [13]. This can directly test a limited interpretation of “no telemetry” for a project that depends only on known tools and uses documented flags. It cannot detect unknown telemetry mechanisms, dynamically loaded code, or telemetry outside its curated registry.

**airgap-check is a stronger behavior-oriented precedent because it combines static analysis with network-disabled dynamic verification.** It scans repositories, can run a supplied command in a Docker container with `--network none`, and observes DNS and socket attempts. Its documentation states that the static path parses code without execution and that the dynamic path uses container isolation [14]. This is directly relevant to “works offline,” “no telemetry,” and “no data leaves your machine.”

However, airgap-check is scoped to offline/telemetry observations and an AI-repository context. It does not parse a README, construct a general claim ontology, map prose claims to evidence, or produce the requested fixed verdict set. Its dynamic detector is also environment-specific and path-dependent: exercising more code paths may reveal more behavior, while failing to trigger a network call cannot prove that no call exists under every valid input.

**BHEESHMA demonstrates runtime monitoring of npm dependencies.** It describes observation of environment-variable access, filesystem reads/writes, network connections, HTTP requests, and shell execution, attributing events to packages and versions [15]. It produces a deterministic trust score, not a source-and-documentation claim verdict. Its scope is Node.js, so it is not language-agnostic in the requested sense.

**General-purpose static analysis and system-call tracing provide lower-level detection primitives.** Tools such as Semgrep support pattern matching and taint/source-to-sink analysis for selected languages, which can help find network, logging, or data-flow patterns [16]. Tracee and similar eBPF-based tools can observe syscalls, file access, network events, and capabilities at runtime. These are valuable observation back ends, but they are not claim auditors and do not certify absence of behavior.

**“Privacy first,” “no data leaves your machine,” and “no tracking” are especially difficult claims.** A network call may be benign or essential; data may be anonymized or may contain identifiers; offline operation may depend on a cache; and “tracking” may be a policy judgment rather than a technical event. A rigorous tool should convert such claims into falsifiable predicates with explicit scope, for example: “no outbound TCP/UDP/DNS occurs during a defined workload under a declared environment,” rather than claiming to prove “privacy first” in the abstract.

## 6. Supply-chain behavior manifests and runtime monitoring exist, but they answer different questions

The supply-chain-security field has developed the conceptual vocabulary needed for behavior evidence, particularly around expected and observed behavior. It has not yet integrated that vocabulary with prose claims.

**The Bill of Behavior (BoB) is a direct conceptual predecessor to a machine-readable behavior contract.** It proposes a vendor-supplied profile describing expected runtime behavior—syscalls, file access, network communication, and capabilities—that can be shipped with OCI artifacts. Its rationale includes verifying an installer against a known benign profile and detecting anomalies at runtime [17]. This is strong support for modeling behavior as a first-class artifact rather than an afterthought.

The gap remains deliberate and substantial. BoB describes known benign behavior; it does not automatically derive that behavior from a README claim, adjudicate whether the program stays within its declared bounds, or compare two releases in terms of the user-facing claims those releases make. The retrieved material also characterizes the implementation as a rapid-prototype design and explicitly warns that its regex output is not yet stable enough to rely on [17]. This is important negative evidence: the behavior-manifest idea is plausible but not yet a dependable general standard.

**xorg/xz-style hidden-behavior detection is an active problem class, but there is no universal “hidden behavior” scanner.** The 2024 xz-utils incident involved malicious build/compression objects hidden in test data, triggered only under particular build conditions; it was ultimately uncovered through anomalous runtime performance rather than a single conventional SCA scan. A behavior manifest and differential runtime monitor could help detect a mismatch between expected and observed behavior, but neither alone proves that a release is safe.

A two-version behavior diff is therefore best understood as **change detection under controlled workloads**, not a guarantee of supply-chain safety. If release B introduces a new DNS lookup under one configuration, the tool should report the added behavior, its trigger conditions, and the code path that produced it. It should not infer maliciousness unless an explicit policy maps that evidence to a risk class.

## 7. Trust scoring and reputation tools do not establish local factual truth

OpenSSF Scorecard automates security-posture analysis and assigns heuristic check scores. Its documentation explicitly says its checks are heuristics with false positives and false negatives, and that an aggregate score says nothing about which individual behaviors a repository performs [18]. Scorecard is valuable for maintenance, security policy, and release-monitoring practices, but it does not extract “no telemetry” from a README and verify it against execution.

This distinction is central. A trust score answers: *how well does this project follow a selected set of security practices?* A software-honesty audit answers: *what explicit claim is being made, what evidence supports or refutes it, and is the available evidence sufficient?* The latter should resist collapsing uncertainty into a single score. A repository can have excellent Scorecard results while falsely claiming to be dependency-free, and a brand-new project can have incomplete security practices while truthfully stating that a current build contains no telemetry.

A claim auditor can use trust/reputation data as contextual evidence, but it must keep that evidence separate from claim adjudication. Otherwise, “VERIFIED” becomes a proxy for popularity or security hygiene, defeating the purpose.

## 8. Two-version behavior comparison is independently developed, but no tool closes the claim-audit loop

Several projects compare two program versions, yet none integrates that capability with a general claim-evidence workflow.

**RunBoth is a particularly important prior-art example for behavior diff.** It materializes two Git commits, matches functions, generates boundary-sensitive inputs, executes both versions in separate processes with CPU/memory/filesystem/network restrictions, and reports behavioral divergence including over functions not directly changed. Its documentation emphasizes that identical source text does not imply identical behavior because an unchanged function can call changed dependencies [19].

This is a serious challenge to novelty. RunBoth demonstrates that a tool can already run two versions and look for differences without a model or external calls. The proposed behavior-diff mode must therefore be differentiated by its claim-aware evidence schema, its use of controlled workload specifications, its mapping from a changed system-call/file/network event to a prose claim, and its audit-grade reproducibility—not by the mere act of running two versions.

**Differential fuzzing can discover behavioral divergences between patched and unpatched binaries.** A LibAFL-based differential-fuzzing pipeline can build instrumented v1 and v2 binaries and search for divergences. This is useful for low-level semantic-difference detection, especially in security research, but it is not a documentation claim verifier and is not aimed at general end-user claims [20].

**Standard system-call and test-output comparison tools provide smaller building blocks.** `strace`, file-system snapshots, network-capture tools, differential testing, and property-based testing can compare observed events across runs. Their limitation is interpretation. A raw diff might show that a process opened `/etc/hosts` or made a different syscall, but it cannot say whether that contradicts a README’s statement about privacy or offline use without a claim-specific policy and evidence provenance.

![Behavior-diff tools](/data/workspace/dr:research_prior_art/fig_behavior_diff.png)

*Figure 2: Behavior-diff projects can execute and compare two versions, but they do not provide the requested end-to-end documentation-claim audit. Data sources: project documentation and repository descriptions retrieved 2026-11-10 [4], [14], [19], [20].*

A credible behavior-diff design should therefore combine four layers: a workload specification, an observation adapter, a normalized behavior ontology, and a semantic diff policy. Without all four, a “diff mode” risks being either an impressive but uninterpretable syscall dump or a narrow test runner.

## 9. The precise remaining gap is an evidence model, not another scanner

The evidence shows that no single surveyed project simultaneously satisfies the six required constraints. The exact remaining work is to build and validate an evidence model that links prose claims to code, dependencies, configuration, build artifacts, controlled execution, and release comparisons.

| Claim example | Source/metadata evidence | Behavioral evidence | Why a simple scanner fails |
|---|---|---|---|
| “no telemetry” | Analytics SDK imports; manifest dependencies | Outbound network, DNS, sockets during declared workloads | Unknown SDKs, lazy loading, and offline caching can hide or falsely imply telemetry |
| “works offline” | Network APIs in source; required online resources | Network-disabled run succeeds or fails across workloads | One successful run does not prove all modes are offline |
| “zero dependencies” | SBOM / lockfile / build graph | Runtime dynamic linking or downloaded plugins | “Dependencies” may mean production, runtime, build, or system libraries |
| “MIT licensed” | LICENSE text, package manifest, source headers | Not a runtime claim | Legal scope and dependency compatibility still require interpretation |
| “privacy first / no data leaves your machine” | Exfiltration sinks; remote endpoints in code | File, memory, network, and IPC observations | Requires a threat model and data-classification policy |
| “100% test coverage” | Test manifests; coverage-tool output | Test execution results | Coverage tools disagree; 100% line coverage does not imply behavior correctness |
| “supports Windows” | Platform-specific code; CI configuration | Execution on Windows or an ABI/behavior simulation | Build may succeed while runtime behavior fails |
| “no tracking” | Analytics identifiers; fingerprinting APIs | Observation of identifiers crossing trust boundaries | “Tracking” is partly a policy judgment |

The central innovation is not a new detector but a **claim evidence record**. Each record should retain: the original claim text and location; normalized claim type; scope; evidence artifacts; observation environment; confidence-relevant limitations; and the reason a verdict is justified. “UNVERIFIABLE” must be an explicit, respectable output rather than a failure—especially for subjective claims, inaccessible environments, or execution paths not covered by supplied workloads.

The behavior diff should similarly preserve a transition record: `claim` → `old behavior profile` → `new behavior profile` → `stable workload` → `added/removed/changed observation` → `file:line / commit / build evidence`. This allows a user to see that “version 1.2 added an outbound DNS query during startup under workload X,” rather than receiving a generic warning that two binaries differ.

## 10. Novelty is strongest in the integration and guarantees, not in any single component

**A defensible novelty argument exists, but it must be narrow and testable.** The most supportable contributions are:

1. **A claim ontology and semantic mapping from human-facing software statements to auditable predicates.** This goes beyond Markdown linting and SBOM generation by converting claims such as “no telemetry” into explicit, falsifiable verification conditions.
2. **A hybrid static/dynamic evidence graph with stable file:line citations.** This combines dependency analysis, source analysis, configuration analysis, build artifacts, and controlled runtime observation in one report.
3. **A strict three-valued verdict protocol.** Rather than aggregating scores or suppressing uncertainty, the tool must distinguish verified truth, direct contradiction, and insufficient evidence.
4. **A claim-aware two-release behavior diff.** This links observed behavioral changes to the claims a project makes, rather than merely comparing syscalls, tests, or source files.
5. **A declared offline and deterministic execution contract.** This requires pinned adapters, local models where used, locked workloads, and an explicit statement of residual nondeterminism and unexercised paths.

The first four are the strongest differentiators. The fifth is both a feature and a limitation: the tool can be deterministic only at a defined level of abstraction. It should publish the exact OS, kernel/container, interpreter, dependency resolution, test inputs, and observation agents that were used. Without those artifacts, “deterministic” is an unverifiable marketing claim of the kind the tool itself is intended to police.

Novelty is **not** supported merely by placing an LLM in front of existing scanners. If claim extraction or verification relies on a remote model, then the tool is neither fully offline nor deterministic in the strict sense. The more credible design either uses a pinned local model as an explicitly nondeterministic experimental adapter or reserves deterministic logic for the final adjudication.

## 11. Verification limitations and caveats

The research period covered web-accessible project descriptions, repository-oriented retrieval results, documentation pages, package listings, and academic write-ups available by 2026-11-10. Direct access to some GitHub repositories was unavailable during the session, so claims about those repositories rely on retrieved descriptions and project documentation rather than a line-by-line review of the current source. This is particularly relevant to openworkers, claimcheck, Receipts, and driftcheck.

Several candidate projects appear recent, have few public releases, or are distributed primarily through package registries rather than visible mature repositories. Maintenance status should therefore be reassessed at implementation time. Version numbers, feature lists, and repository activity cited here are point-in-time observations; they are not endorsements and do not establish long-term sustainability.

A comprehensive patent or academic novelty search was not performed. This report surveys the open developer-tool ecosystem, not patent databases, proprietary enterprise products, academic theses behind paywalls, or every language-specific plugin. The conclusion is that **no mature, maintained, open-source project was found that provides the full requested capability bundle**—not that the bundle is mathematically impossible or that no prior work exists anywhere.

Finally, some recent tool descriptions show signs of AI-assisted project generation or marketing language, and not all claims were independently reproducible from canonical repositories. Their inclusion reflects an effort to identify emerging prior art, not a confirmation that every stated feature works as advertised. Any freedom-to-operate or publication decision should include a deeper review of repository history, issues, test suites, releases, and source code for the closest candidates.

## Capability comparison

The downloadable table underlying the figures is available here: [tool capability data](/data/workspace/dr:research_prior_art/data_tool_capabilities.csv).

## References

[1] https://www.claude-updates.com/posts/docverity-gxkgs
> “Reference checker: deterministic, no API key, instant. Catches docs that mention files, CLI flags, environment variables, or symbols that no longer exist anywhere in the source.”

[2] https://socket.dev/npm/package/docverity
> “Docverity reads your documentation, extracts the concrete claims it makes about the codebase, and checks each one against the source.”

[3] https://dev.to/shaurya_mehta/receipts-i-built-a-local-ai-verifier-for-my-friends-project-reports-1614
> “AI proposes the claims. Deterministic code makes the decision.”

[4] https://github.com/ojuschugh1/claimcheck
> “A test that passes both with and without the change it supposedly guards is decoration, and it is the most common way a ‘verified’ claim turns out to be empty.”

[5] https://github.com/DavidHavoc/openworkers
> “Audit factual claims in READMEs and pull requests against the codebase.”

[6] https://github.com/TheArtchitect/driftcheck
> “Driftcheck is an open-source command-line verification tool that detects three categories of repository drift: repository state divergence, documentation inaccuracy, and session-to-session continuity breakdown.”

[7] https://arxiv.org/abs/2603.00331
> “Linters evaluating the textual style of markdown files are reasonably common.”

[8] https://github.com/anchore/syft
> “A CLI tool and Go library for generating a Software Bill of Materials (SBOM) from container images and filesystems.”

[9] https://github.com/aquasecurity/trivy
> “Trivy has scanners that look for security issues, and targets where it can find those issues.”

[10] https://github.com/CycloneDX/cdxgen
> “cdxgen is a cli tool, library, REPL, and server to create a valid and compliant CycloneDX Software Bill-of-Materials (SBOM)”

[11] https://github.com/aboutcode-org/scancode-toolkit
> “ScanCode detects licenses, copyrights, package manifests, direct dependencies, and more both in source code and binary files.”

[12] https://github.com/licensee/licensee
> “Licensee automates the process of reading LICENSE files and compares their contents to known licenses using a several strategies.”

[13] https://github.com/—/no-telemetry
> “The CLI is deliberately narrow: It makes no runtime network requests and never downloads a registry.”

[14] https://github.com/humanetq/airgap-check
> “Static scan. --run requires Docker.”

[15] https://github.com/bb1nfosec/bheeshma
> “Modern applications depend on hundreds of third-party npm packages.”

[16] https://semgrep.dev/?r=cr
> “Combine deterministic static analysis with AI reasoning to understand naming, structure, and developer intent.”

[17] https://github.com/k8sstormcenter/bob
> “A vendor-supplied profile detailing known benign runtime behaviors for software, designed to be distributed directly within OCI artifacts.”

[18] https://github.com/ossf/scorecard
> “Aggregate scores in particular tells you nothing about what individual behaviors a repository is or is not doing.”

[19] https://github.com/—/RunBoth
> “It runs your code. Both versions of it. On the same inputs. In separate processes.”

[20] https://github.com/—/libafl-diff-fuzzer
> “A general-purpose differential fuzzer built on LibAFL that detects behavioral divergences between two versions of a binary.”
