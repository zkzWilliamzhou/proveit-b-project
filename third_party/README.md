# third_party

Everything in this directory is material that is not `proveit` source. The
declared scan scope excludes it by design, and `docs/adr/ADR-0004-claim-source-scope.md`
records why: quoted research notes and vendored skill READMEs are not promises
made by this project.

| Path | Origin | License / note |
|---|---|---|
| `skills/anthropics__skills/` | `github.com/anthropics/skills` | Apache-2.0 for example skills; document skills are source-available. See the upstream README. |
| `skills/mattpocock__skills/` | `github.com/mattpocock/skills` | See upstream LICENSE. |
| `skills/vercel-labs__agent-skills/` | `github.com/vercel-labs/agent-skills` | See upstream LICENSE. |
| `skills/vercel-labs__skills/` | `github.com/vercel-labs/skills` | See upstream LICENSE. |
| `skills/obra__superpowers/` | `github.com/obra/superpowers` | See upstream LICENSE. |
| `skills/tomerose__stop-slop/` | `github.com/tomerose/stop-slop` | MIT. |
| `skills/proveit-audit/`, `skills/proveit-review/` | Written for this project | MIT, same as the project. |
| `research/` | Three research reports produced for this project | Internal working notes. Figures are labelled approximate or unverified. |
| `examples/` | Hand-written honest, dishonest and version-diff fixtures | MIT, same as the project. |
| `archives/` | Original GitHub tarballs (except the 4 MB anthropics archive, removed after installation) | Upstream licenses apply. |

Only Markdown, JSON, YAML and text files were installed from the upstream
tarballs. No executable code, script or hook from those repositories is
invoked by `proveit`. See `docs/SKILLS_INSTALLED.md` for which skills were used
and how.

`third_party/examples/` is intentionally inside the excluded directory. Run
the demos with their full paths:

```console
python3 -m proveit check third_party/examples/clean_repo
python3 -m proveit check third_party/examples/dirty_repo
python3 -m proveit diff third_party/examples/v1 third_party/examples/v2
```
