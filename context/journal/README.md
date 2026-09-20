# context/journal/

The Chief of Staff's running journal, one file per day: `YYYY-MM-DD.md`. It records what happened in the order it happened, in enough detail that a new session can continue without the CEO explaining anything again.

Append an entry with `python3 scripts/journal.py add "what happened" [--job <job-id>]` (it stamps the time; the job, worktree, agent and project scripts add their own lines) whenever:

- the CEO asks for something or decides something (their words, briefly, and your restatement of the outcome)
- you ask the CEO a question or for an approval (the question and the options, word for word), so a new session knows what is still waiting for an answer
- you start something that takes more than a minute, **before** you start it (what, why, which job)
- something finishes, fails, blocks, or surprises you (what came back, where the evidence is)
- you change course, and why

Format: `- HH:MM what happened (job id or file path)`. Facts, not prose. `python3 scripts/journal.py close "..."` ends the day with a `## Day summary` block; `journal.py unclosed` lists days that never got one. The end-of-day routine reads these files to find the lessons of the day; `context/log.md` keeps only the one-line record of finished work.
