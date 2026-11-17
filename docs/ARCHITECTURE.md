# Architecture

Terms come from `GLOSSARY.md`: module, interface, seam, adapter, depth,
locality, leverage, deletion test.

## Data flow

```
workspace.walk      -> list[FileView]          (read-only adapter)
        |
        +-> scanner.scan       -> Receipt     (capability evidence)
        +-> manifests.attach   -> Receipt     (manifest facts + file evidence)
        +-> claims.extract     -> list[Claim] (bounded prose reading)
        |
pipeline.read_tree  -> (Receipt, license, claims)
        |
adjudicator.build_audit -> AuditReport
        |
render / differ     -> json | markdown | sarif | diff report
```

`FileView` is the seam. Everything above it changes when a new language,
manifest or claim kind arrives; everything below it stays put. Two adapters
already sit behind that seam: `workspace.walk` for a real directory, and the
in-memory `FileView` lists assembled by tests. That is what makes the seam
real rather than hypothetical.

## Module map

| Module | Interface | Depth |
|---|---|---|
| `model.py` | `Receipt`, `Verdict`, `AuditReport`, `DiffReport` and their `to_dict` / `with_*` constructors | Deep. All record construction, sorting and coverage recomputation lives here. |
| `limits.py` | `Limits`, `Budget` | Deep. One place defines every quota and the meaning of `complete`. |
| `workspace.py` | `walk(root, limits) -> (views, budget)` | Deep. Path safety, symlink policy, byte budgets and decoding hide behind one call. |
| `rules.py` | `RULES`, `NEGATIVE_REQUIREMENTS`, `CAPABILITIES` | Frozen data. No behaviour, no user-supplied patterns, no regular expressions. |
| `scanner.py` | `scan(views, budget, excludes)` | Bounded literal matching over `FileView` lines. |
| `manifests.py` | `attach(receipt, views)` | Small, purpose-built parsers. An unparseable manifest yields `incomplete=True`. |
| `claims.py` | `extract(views, budget, include_docs)` | Bounded claim reading from claim sources. |
| `adjudicator.py` | `adjudicate`, `build_audit` | Pure. Maps one Claim and one Receipt to one Verdict. |
| `differ.py` | `compare(left, right)` | Pure. Fingerprint set difference. |
| `render.py` | `to_json`, `render_*`, `to_sarif_*` | Output encoding and sanitisation. |
| `pipeline.py` | `read_tree`, `audit_tree` | Deep. The one place that knows the five-step sequence. |
| `cli.py` | `main(argv)` | Thin. Parsing, exit codes, stream discipline. |
| `selftest.py` | `run(...)` | Thin. Applies the same pipeline to proveit itself. |

## Deepening applied in review round 7

Before round 7, `cli.collect` and `selftest.run` each repeated the same five
calls: walk, scan, attach manifests, extract claims, adjudicate. A coverage
bug fixed in one path could survive in the other. That is shallow: the
interface was nearly as wide as the implementation, and locality was poor.

```
BEFORE                                  AFTER
cli.collect  --+-- walk                 cli.collect  ---> pipeline.read_tree
               +-- scan                                    |
               +-- attach                                   +-- walk
               +-- extract                                  +-- scan
               +-- adjudicate                               +-- attach
                                                            +-- extract
selftest.run --+-- walk                 selftest.run ---> pipeline.read_tree
               +-- scan                                    |
               +-- attach                                   +-- adjudicate
               +-- extract
               +-- adjudicate          adjudicator.build_audit  (unchanged)
```

`pipeline.read_tree` has one interface and one place to test. Deleting it
would not remove complexity; it would scatter the sequence across three call
sites. That is the deletion test passing.

The second deepening moved Receipt construction into `model.Receipt`.
`with_manifests` and `with_notes` concentrate field copying and recompute
`scan_complete` when warning Notes arrive. Callers can no longer rebuild a
Receipt by hand and silently drop a field.

**Function preservation.** No verdict, capability, exit code, flag or output
field changed. `docs/REVIEW_LOG.md` round 7 records the before/after golden
outputs: `check .` stayed at 7 VERIFIED / 0 CONTRADICTED / 1 UNVERIFIABLE,
clean stayed at 4 / 0 / 1, dirty stayed at 0 / 4 / 1, and the diff kept the
same five added capabilities. The full suite passed before and after (50
tests at that point; 71 after rounds 10-11 added a string-precision class and
a budget class, without moving any golden output).

## Invariants

1. A repository is data. Nothing from it is imported, evaluated, executed,
   resolved or written back.
2. No network call exists in the tool. There is no socket, HTTP client,
   download helper, telemetry SDK or update check in `proveit/`.
3. Matching uses `str.find` on bounded lines. No regular expression runs over
   repository text, and the repository cannot add a pattern.
4. Any skipped path, undecodable file or exhausted budget produces a warning
   Note and sets `scan_complete` false.
5. CONTRADICTED always carries positive Evidence. Absence of findings never
   produces CONTRADICTED.
6. All output is deterministic and sanitised before it reaches a terminal or
   a Markdown document.

## Decisions

- `docs/adr/ADR-0001-three-state-verdicts.md`
- `docs/adr/ADR-0002-static-only.md`
- `docs/adr/ADR-0003-pipeline-seam.md`
- `docs/adr/ADR-0004-claim-source-scope.md`
