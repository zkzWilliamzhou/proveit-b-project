# ADR-0002: analyse only, never execute

Status: accepted.

## Context

Dynamic observation would answer "does it phone home" better than a literal
scan. It would also require building the target, installing its dependencies,
running its scripts, and giving an untrusted repository a process. The threat
model in `third_party/research/THREAT_MODEL.md` lists the resulting blast
radius: install hooks, shell injection, credential reads, network egress,
resource exhaustion.

## Decision

`proveit` reads files as bytes and text. It never imports, evals, builds,
installs, resolves or runs target content. It never opens a socket. It never
writes into the target tree. Rule matching uses fixed lowercase literals and
`str.find` on lines bounded by `max_line_chars`, so a hostile string cannot
induce catastrophic backtracking.

## Consequences

- Obfuscated code, dynamically assembled module names, generated sources and
  behaviour inside unscanned dependencies can evade detection. Every verdict
  prints that limitation.
- A URL literal is advisory evidence, never a contradiction by itself.
- The tool survives as a workstation utility without a sandbox, container,
  package manager or privileged account.
- `no_binary` is permanently UNVERIFIABLE because binary assets are outside
  scan scope.

## Revisit trigger

A future ``--sandbox`` mode would be a separate command with its own trust
boundary, its own audit and its own ADR. It must not become an implicit step
of `scan` or `check`.
