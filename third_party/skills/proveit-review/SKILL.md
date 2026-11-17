---
name: proveit-review
description: The strict twelve-round review checklist for changes to proveit. Use before declaring a change complete, especially after adding a rule, a claim kind or an output field.
---

# Review a proveit change

Work the rounds in order. Do not skip a round because the change looks small.

1. **Output integrity.** Does `-o` write every byte? Are errors sanitised?
2. **Evidence integrity.** Does every CONTRADICTED verdict carry a file and
   line? Are dropped claims reported?
3. **False positives.** Do comments, bare string literals and the frozen rule
   table stay quiet? Do manifest parsers read only dependency fields?
4. **Denial of service.** Are entry, file, byte, line and depth budgets checked
   before allocation? Are symlinks and special files rejected?
5. **Scope honesty.** Do limitations name the concrete excluded paths? Does
   Markdown print them? Does SARIF keep them?
6. **Injection and determinism.** Are all repository strings sanitised? Are two
   runs byte-identical? Does the scan leave the target tree untouched?
7. **Architecture.** Does the change deepen a module or scatter a sequence?
   Apply the deletion test. Record golden outputs to prove no function changed.
8. **First run.** Does `python3 -m proveit check .` pass with no exclusions?
9. **Docs and demos.** Are README snippets verbatim output? Do the ontology
   and output schema documents match the code?
10. **String precision.** Does a capability name inside a single-line string,
    an inline comment, a triple-quoted docstring or a double-backtick literal
    stay quiet? Does a masked first occurrence still allow a real call later
    on the line? Is `#[link(` still detected?
11. **Budgets and scope.** Does a claim budget emit exactly one Note? Do
    `--max-claims` and `--max-evidence` degrade negative claims to
    UNVERIFIABLE? Is `--exclude` disclosed as deliberate scope narrowing
    while automatic skips set `scan_complete: false`?
12. **Release audit.** Do version, test counts, round counts and demo output
    agree across every document? Does the packaged zip pass the full gate
    after extraction into a clean directory?

## Gate

```console
python3 -m unittest discover -s tests -v
python3 -m proveit selftest
python3 -m proveit check . --format json
```

All three must pass. Record the round, the finding and the fix in
`docs/REVIEW_LOG.md`. Reject work that is incomplete, fabricated or silently
reduces the scan scope.
