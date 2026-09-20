# Engineering standards

STATUS: DEFAULTS

<!-- The rules everyone who writes code follows on every project. The first software project (new-project or import-project skill) settles "House style" with the CEO and sets the status to SET. Project-specific choices (tech stack, commands) live in each project's own CLAUDE.md, not here. -->

Anyone who writes code, employee or Chief of Staff, reads this file and the project's `CLAUDE.md` before starting. Both are binding.

**Imported codebases keep their own standards.** A project with a `plans/<project>/PROFILE.md` existed before the company (`import-project` skill). There, new code looks like the code around it: on how code is written (rules 3, 4 and 6, commit message format, QA identifiers, House style, test style) the project wins, unless its `CLAUDE.md` records that the CEO decided otherwise. Company process always applies: rules 1, 2 and 8, no secrets, and the test-first order of rule 5, with the project's own test tools.

## Always

1. **Stay inside the stack.** The project's `CLAUDE.md` lists the tech stack the CEO chose. Adding a language, framework or major dependency needs CEO approval, and the approved change updates that file in the same commit.
2. **Build from an approved spec or plan, in your own worktree.** The Chief of Staff creates `worktrees/<project>/<your-name>--<slug>` on branch `<your-name>/<slug>` and gives you its base commit. You never touch the project's main checkout, and several developers can work on the same project at once. A fresh worktree has nothing installed: run the install command first.
3. **Design deep modules.** A lot of behaviour behind a small interface, tested through that interface. Use the vocabulary of the `codebase-design` skill (module, interface, seam, adapter, depth). Do not add a seam until something actually varies across it.
4. **Prefer direct, boring code.** No wrappers that only pass through, no flags bolted onto busy functions, no special cases scattered through shared paths, no file pushed past 1000 lines. If a change needs any of these, the design is wrong: restructure first.
5. **Test first.** Work by the `tdd` skill: write a failing test, then only enough code to pass it, one vertical slice at a time. Never write the code first and the tests after, and never write all the tests up front. Tests go through a module's public interface at the seams the plan names, integration-style where you can, with expected values that come from the spec and not from the code. Mock only at system boundaries. Record the failing run and the passing run in your progress file, run the full test and lint commands before handing back, and include the output. Refactoring is not part of this loop; it happens in the refinement check.
6. **Use the domain language.** Name things with the terms in the project's `CONTEXT.md`. Add terms the spec settled to `CONTEXT.md` on your feature branch. Hard-to-reverse decisions get an ADR in `docs/adr/` (see the `domain-modeling` skill).
7. **Small commits** with messages that say what changed and why. No secrets in any repo.
8. **Hand back** the project, worktree, base, branch, list of changed files, and test and lint output. You never merge or push.

## After every implementation

Before anything is pushed or merged, `REVIEW.md` runs three things on the change: an independent review (which also checks that the tests came first), the `refinement-check` skill (rule 4 above is what its code quality review enforces), and, for anything a user sees or touches, hands-on QA with the `qa-check` skill in a real browser or emulator.

## Building things that can be QA'd

- The project's `CLAUDE.md` says how to run the product locally. Keep that command working; QA starts there.
- Give interactive elements stable identifiers: `data-testid` on the web, `testID` in React Native, `Semantics(identifier:)` in Flutter, accessibility identifiers in native apps. Without them, browser and emulator automation falls back to guessing from pixels.
- Every screen handles its loading, empty and error states. QA looks for them.

## House style

_Not set. The CEO's own rules go here: naming, comments, error handling, typing strictness, formatting, dependency policy, anything they always or never want. Each rule must be specific enough that a reviewer can tell whether a diff follows it._
