# context/

The shared memory of the company.

- `company.md`: what we sell, to whom, and the current goal. Loaded by every session. Keep it under a page.
- `team.md`: the roster. Loaded by every session.
- `engineering.md`: coding standards for every developer on every project. Read by developer employees, not loaded by everyone. Each project's tech stack lives in that project's own `CLAUDE.md`.
- `decisions.md`: append-only decision log.
- `log.md`: append-only work log, one line per finished item.
- `journal/`: the Chief of Staff's detailed running journal, one file per day. Read by the `job-status` skill after a crash and by the end-of-day routine.

Add other reference files here when several employees need them (pricing, brand voice, competitors). Do not import them in `CLAUDE.md` unless every session needs them; point to them from the role files that do.
