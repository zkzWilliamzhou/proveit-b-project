# GLOSSARY

Shared domain language for `proveit`. Architecture reviews in
`docs/adr/` and `docs/ARCHITECTURE.md` use these words exactly.

| Term | Meaning |
|---|---|
| **Claim** | One bounded sentence from a claim source that maps to a machine-checkable proposition. A claim has a kind, an argument, a location, a polarity and a scope. |
| **Claim source** | A root-level README, SECURITY, PRIVACY or CONTRIBUTING document. Markdown under `docs/` becomes a claim source only with `--claim-docs`. |
| **Capability** | A static observation about source text: an HTTP client call, an analytics SDK, a subprocess call, a declared dependency. Capabilities are named in `proveit/rules.py`. |
| **Evidence** | One capability located at a file and line. File-level facts use `line: 0`. |
| **Receipt** | The complete, ordered set of Evidence, Notes and Manifest Facts for one tree. A receipt is a value, not a process. |
| **Note** | A skipped path, an excluded directory or an exhausted budget. A warning Note degrades negative claims to UNVERIFIABLE. |
| **Manifest Fact** | Dependency and license information read from a root-level package manifest. |
| **Verdict** | The adjudication of one Claim: VERIFIED, CONTRADICTED or UNVERIFIABLE. Every Verdict carries a reason, Evidence and limitations. |
| **Scan scope** | The set of files the walk will read. Binary assets, vendored dependency directories, hidden directories other than `.github`, and `--exclude` paths sit outside it. |
| **Adjudication** | The pure function that maps a Claim and a Receipt to a Verdict. |
| **Capability diff** | The set of Evidence fingerprints added or removed between two Receipts. |
| **Module** | A Python file with one responsibility and one interface. |
| **Interface** | The set of calls a Module offers to its callers. |
| **Seam** | The place where one Module meets another. |
| **Adapter** | A Module behind a Seam that can be replaced without changing its callers. |
| **Depth** | How much implementation sits behind a small Interface. A deep module hides complexity; a shallow one exports it. |
| **Locality** | Code that changes together lives together. |
| **Leverage** | How much behaviour one small Interface controls. |
| **Deletion test** | Delete a suspected shallow module. If complexity merely moves elsewhere, the module was shallow. If complexity concentrates, the module earns its place. |
