# Engineering standards

STATUS: DEFAULTS

<!-- The rules everyone who writes code follows on every project. The first software project set up with the new-project skill grills the CEO on "House style" and sets the status to SET. Project-specific choices (tech stack, commands) live in each project's own CLAUDE.md, not here. -->

Anyone who writes code, employee or Chief of Staff, reads this file and the project's `CLAUDE.md` before starting. Both are binding.

## Always

1. **Stay inside the stack.** The project's `CLAUDE.md` lists the tech stack the CEO chose. Adding a language, framework or major dependency needs CEO approval, and the approved change updates that file in the same commit.
2. **Build from an approved spec or plan**, on a branch named `<your-name>/<short-name>`, never on a product repo's default branch. Note the branch and commit you started from: it is the base for review.
3. **Design deep modules.** A lot of behaviour behind a small interface, tested through that interface. Use the vocabulary of the `codebase-design` skill (module, interface, seam, adapter, depth). Do not add a seam until something actually varies across it.
4. **Prefer direct, boring code.** No wrappers that only pass through, no flags bolted onto busy functions, no special cases scattered through shared paths, no file pushed past 1000 lines. If a change needs any of these, the design is wrong: restructure first.
5. **Test behaviour, not internals.** New behaviour comes with tests that go through the module's interface. Run the project's test and lint commands before handing back, and include the output.
6. **Use the domain language.** Name things with the terms in the project's `CONTEXT.md`. Add terms the spec settled to `CONTEXT.md` on your feature branch. Hard-to-reverse decisions get an ADR in `docs/adr/` (see the `domain-modeling` skill).
7. **Small commits** with messages that say what changed and why. No secrets in any repo.
8. **Hand back** the project, base, branch, list of changed files, and test and lint output.

## After every implementation

The `refinement-check` skill runs on the change before anything is pushed or merged. See `REVIEW.md` section 3. Rule 4 above is what its code quality review enforces, so following it is the cheap way to pass.

## House style

_Not set. The CEO's own rules go here: naming, comments, error handling, typing strictness, formatting, dependency policy, anything they always or never want. Each rule must be specific enough that a reviewer can tell whether a diff follows it._
