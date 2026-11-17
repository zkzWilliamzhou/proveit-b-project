# Skills installed into this program

The brief asked for GitHub skill collections to be installed and for the
useful ones to be brought into the program. They live in `third_party/skills/`.
They are text definitions, not executable plugins. No code from these
repositories runs inside `proveit`.

| Repository | Installed | What landed |
|---|---|---|
| `anthropics/skills` | 184 Markdown files | Agent Skills specification, template and example skills. Used as the format reference for our own `SKILL.md` files. |
| `mattpocock/skills` | 141 Markdown files | `improve-codebase-architecture`, `codebase-design`, `grill-me`, `grilling`, `tdd`, `diagnosing-bugs`, `to-spec`, `implement-spec`, `wayfinder`, `writing-for-agents`. |
| `vercel-labs/agent-skills` | 213 Markdown files | `writing-guidelines`, `react-best-practices`, `react-native-guidelines`, `react-view-transitions`, `vercel-optimize`. |
| `vercel-labs/skills` | 3 Markdown files | The `npx skills` distribution tool README and manifests. |
| `obra/superpowers` | 66 Markdown files | `brainstorming`, `writing-plans`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `requesting-code-review`, `subagent-driven-development`, `dispatching-parallel-agents`. |
| `tomerose/stop-slop` | 5 Markdown files | `SKILL.md`, README and the phrase/structure/example references. |

Total: 99 `SKILL.md` files, about 4.5 MB of text, including the two local
`proveit-*` definitions. Original tarballs are in
`third_party/archives/` (the 4 MB `anthropics/skills` archive was fetched,
installed from, then removed to keep the distribution small).

## How they were used

- `obra/superpowers:brainstorming` - the design gate. Approaches were laid
  out, the design was written, and the plan followed before implementation.
- `mattpocock/skills:grill-me` and `grilling` - the adversarial
  self-questioning that produced the three-state verdict contract and the
  "absence is not proof" rule.
- `obra/superpowers:writing-plans` - the workflow that assigned specialist
  research agents (prior art, adoption, threat model) before any code.
- `obra/superpowers:test-driven-development` and
  `mattpocock/skills:tdd` - RED / GREEN / REFACTOR for the fixtures and the
  verdict engine.
- `obra/superpowers:systematic-debugging` - reproduce, isolate, hypothesise,
  fix, add a regression test. Round 3 of `docs/REVIEW_LOG.md` is a direct
  example.
- `obra/superpowers:verification-before-completion` - the final suite,
  self-audit, README-example checks and clean-extraction verification in
  rounds 9 and 12.
- `obra/superpowers:requesting-code-review` - the nine review rounds.
- `tomerose/stop-slop` - prose rules for README and docs: active voice, no
  filler, no adverbs, no em dashes, no "not X, it's Y" constructions.
- `vercel-labs/agent-skills:writing-guidelines` - documentation structure,
  stable help text and machine-readable output discipline.
- `mattpocock/skills:improve-codebase-architecture` - review round 7, the
  deepening of `pipeline.py` and `model.Receipt`, and
  `architecture-review.html`.
- `scientific-brainstorming` and `scientific-critical-thinking` (pre-installed
  in this environment) - labelled claims as idea / assumption / decision,
  preserved dissent, and kept the novelty conclusion conditional.

## Our own skills

`skills/` inside the distribution was deliberately not created. Instead the
project ships its own local skill definitions in
`third_party/skills/proveit-*`:

- `proveit-audit` - how to run an audit and read the three states.
- `proveit-review` - the nine-round review checklist.

These follow the `anthropics/skills` SKILL.md format.
