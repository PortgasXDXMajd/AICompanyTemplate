#!/usr/bin/env python3
"""Product repos under projects/ and the registry in projects/README.md.

  project.py init NAME                  validate the name, mkdir, git init -b main
  project.py commit NAME [-m MSG]       first commit of README.md and CLAUDE.md
  project.py commit NAME --all -m MSG [--allow PATH]...
                                        first commit of everything (a folder brought in with import-local --init);
                                        refuses files that look like secrets unless each is named with --allow
  project.py clone OWNER/NAME|URL [NAME]
  project.py import-local PATH [NAME] [--init] [--remote NAME] [--branch NAME]
                                        bring in a codebase from a folder on this machine: a git repo is cloned
                                        (its origin URL is kept, the folder itself is never touched); a folder
                                        without git is copied and `git init`ed when you pass --init
  project.py survey NAME [--out FILE]   read-only inventory of an existing codebase: git habits, manifests,
                                        tooling, tests, CI, containers, data, env variable NAMES, docs
  project.py register NAME --repo OWNER/NAME --purpose "..." [--status active] [--url URL]
  project.py list

Creating the GitHub repo and pushing are NOT in here on purpose: run `gh repo create ...` yourself,
so Claude Code asks the CEO (see .claude/settings.json).
"""
import argparse
import fnmatch
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib as L

REG = L.ROOT / "projects" / "README.md"
COLS = ["Name", "GitHub repo", "Purpose", "Status", "Created"]
STATUSES = ["active", "importing", "local only", "paused", "archived"]

# Never copied by `import-local --init`: dependency and cache folders that are rebuilt by the install command.
JUNK_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
             ".next", ".nuxt", ".turbo", ".gradle", ".idea", ".vs", "Pods", ".dart_tool", ".terraform"}
JUNK_FILES = {".DS_Store", "Thumbs.db"}
# File NAMES that usually hold secrets. The scripts never open these; they only warn about them.
SECRETISH = re.compile(
    r"(^|/)(\.env(\.[^/]*)?|\.envrc|\.npmrc|\.netrc|\.pypirc|[^/]*\.(pem|pfx|p12|key|keystore|jks|tfvars|tfstate)"
    r"|id_(rsa|dsa|ecdsa|ed25519)|credentials[^/]*\.json|service-?account[^/]*\.json"
    r"|secrets?\.(json|ya?ml|toml|env|txt|properties))$", re.I)
EXAMPLE_FILE = re.compile(r"[.-](example|sample|template|dist)$", re.I)


def looks_secret(path):
    return bool(SECRETISH.search(path)) and not EXAMPLE_FILE.search(path)


def scrub(url):
    """A remote URL without the user:token@ part, so credentials never reach the journal, the survey or the screen."""
    return re.sub(r"://[^/@\s]+@", "://", url or "")


def check_name(name):
    L.valid_name(name, "project name")
    if name.startswith("_"):
        L.die("project names must not start with '_' (worktrees/_hq is reserved)")
    return name


def reg_rows():
    lines = REG.read_text().splitlines()
    try:
        i = next(k for k, l in enumerate(lines) if l.strip().startswith("| Name |"))
    except StopIteration:
        L.die("projects/README.md has no registry table")
    rows = []
    for l in lines[i + 2:]:
        if not l.strip().startswith("|"):
            break
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        rows.append(dict(zip(COLS, c + [""] * 5)))
    return lines[:i + 2], rows, lines[i + 2 + len(rows):]


def cmd_init(a):
    name = check_name(a.name); p = L.ROOT / "projects" / name
    _, rows, _ = reg_rows()
    if p.exists() or any(r["Name"] == name for r in rows):
        L.die(f"project {name} already exists")
    p.mkdir(parents=True)
    L.run(["git", "-C", str(p), "init", "-b", "main"], check=True)
    L.journal_add(f"project {name}: local repo created at projects/{name}")
    print(f"created projects/{name} (empty repo on main). Now write README.md and CLAUDE.md there, then: project.py commit {name}")


def cmd_commit(a):
    p = L.repo_main(a.name)
    if a.all:
        if not a.message:
            L.die("--all needs -m \"<message>\"")
        if L.run(["git", "-C", str(p), "rev-parse", "--verify", "-q", "HEAD"])[0] == 0:
            L.die("--all is only for the very first commit of an imported folder; this repo already has commits")
        L.run(["git", "-C", str(p), "add", "-A"], check=True)
        _, staged, _ = L.run(["git", "-C", str(p), "diff", "--cached", "--name-only"])
        risky = [f for f in staged.splitlines() if looks_secret(f) and f not in (a.allow or [])]
        if risky:
            L.run(["git", "-C", str(p), "reset", "-q"])
            L.die("these look like secrets and would be committed:\n  " + "\n  ".join(risky) +
                  "\nAdd them to .gitignore. For a file the CEO confirms is harmless, rerun with --allow <that path> (repeatable).")
        if not staged:
            L.die("nothing to commit")
    else:
        missing = [f for f in ("README.md", "CLAUDE.md") if not (p / f).exists()]
        if missing:
            L.die(f"write these first: {', '.join(missing)}")
        L.run(["git", "-C", str(p), "add", "README.md", "CLAUDE.md"], check=True)
    L.run(["git", "-C", str(p), "commit", "-q", "-m", a.message or "Initial commit: README and CLAUDE.md with tech stack"], check=True)
    _, sha, _ = L.run(["git", "-C", str(p), "rev-parse", "--short", "HEAD"])
    print(f"committed {sha} in projects/{a.name}.\nNext (asks the CEO): gh repo create <owner>/{a.name} --private|--public "
          f"--source projects/{a.name} --remote origin --push")


def cmd_clone(a):
    src = a.source
    name = check_name(a.name or re.sub(r"\.git$", "", src.rstrip("/").split("/")[-1]).lower())
    p = L.ROOT / "projects" / name
    if p.exists():
        L.die(f"projects/{name} already exists")
    if "://" in src or src.startswith("git@"):
        code, _, e = L.run(["git", "clone", src, str(p)])
    else:
        code, _, e = L.run(["gh", "repo", "clone", src, str(p)])
        if code != 0:
            code, _, e = L.run(["git", "clone", f"https://github.com/{src}.git", str(p)])
    if code != 0:
        L.die(f"clone failed: {scrub(e)}")
    has = (p / "CLAUDE.md").exists()
    L.journal_add(f"project {name}: cloned {scrub(src)}")
    print(f"cloned into projects/{name}. CLAUDE.md present: {has}")
    if scrub(src) != src:
        print(f"NOTE: the URL contains a credential. It stays in projects/{name}/.git/config only; it was not written anywhere else.")


def kebab(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def cmd_import_local(a):
    src = Path(a.path).expanduser().resolve()
    if not src.is_dir():
        L.die(f"no such folder: {src}")
    if src == L.ROOT or L.ROOT in src.parents:
        L.die("that folder is inside this HQ repo. Product code lives outside HQ; give the folder it lives in today.")
    if src in L.ROOT.parents:
        L.die("this HQ repo is inside that folder. Move HQ out of it first, or import the code from its git remote.")
    name = check_name(a.name or kebab(src.name))
    p = L.ROOT / "projects" / name
    if p.exists():
        L.die(f"projects/{name} already exists")
    code, top, err = L.run(["git", "-C", str(src), "rev-parse", "--show-toplevel"])
    if code != 0 and (src / ".git").exists():
        L.die(f"{src} has a .git, but git cannot read it:\n{err}\nFix that first (often: git config --global --add safe.directory {src}).")
    if code == 0 and Path(top).resolve() != src:
        L.die(f"{src} is a subfolder of the git repo at {top}. Import the repo root; a subfolder cannot be its own project.")
    if code != 0 and not a.init:
        L.die(f"{src} is not a git repo. With the CEO's yes, rerun with --init: the folder is copied (without "
              f"dependency and cache folders) and `git init`ed, nothing is committed yet, and the original is not touched.")
    tmp = p.with_name(f".{name}.importing")          # built here and renamed at the end, so a failure leaves nothing behind
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        what, notes = import_git(src, tmp, name, a.remote, a.branch) if code == 0 else import_plain(src, tmp, name)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    tmp.rename(p)
    L.journal_add(f"project {name}: {what}")
    print(what)
    for n in notes:
        print(n)


def import_git(src, dest, name, want_remote, want_branch):
    os.environ["GIT_TERMINAL_PROMPT"] = "0"           # never hang on a password prompt

    def sgit(*args):
        return L.run(["git", "-C", str(src), *args])[1]

    def dgit(*args, check=False):
        return L.run(["git", "-C", str(dest), *args], check=check)
    if L.run(["git", "-C", str(src), "rev-parse", "--verify", "-q", "HEAD"])[0] != 0:
        L.die(f"{src} is a git repo without a single commit. Make the first commit there, then import again.")
    notes = []
    remotes = sgit("remote").split()
    remote = want_remote or ("origin" if "origin" in remotes else remotes[0] if len(remotes) == 1 else "")
    if remote and remote not in remotes:
        L.die(f"the source has no remote called {remote!r} (it has: {', '.join(remotes) or 'none'})")
    if remotes and not remote:
        L.die(f"the source has several remotes and none is called origin: {', '.join(remotes)}. Ask the CEO which one the "
              f"company pushes to, then rerun with --remote <name>.")
    url = sgit("remote", "get-url", remote) if remote else ""
    if remote and remote != "origin":
        notes.append(f"NOTE: the source's remote is called {remote!r}; in projects/{name} it is called origin.")

    local = sgit("for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines()
    head = sgit("symbolic-ref", "--short", "-q", "HEAD")
    default, rule = "", ""
    ohead = "" if want_branch else sgit("symbolic-ref", "--short", "-q", f"refs/remotes/{remote}/HEAD") if remote else ""
    if "/" in ohead:
        default, rule = ohead.split("/", 1)[1], f"{remote}/HEAD in the source"
    if not default and url and not want_branch:
        m = re.search(r"^ref: refs/heads/(\S+)\s+HEAD", L.run(["git", "ls-remote", "--symref", url, "HEAD"])[1], re.M)
        if m:
            default, rule = m.group(1), "the remote's HEAD"
    if not default and want_branch:
        if want_branch not in local:
            L.die(f"the source has no local branch called {want_branch!r}")
        default, rule = want_branch, "--branch"
    if not default:
        usual = [b for b in ("main", "master") if b in local]
        if head in usual or (head and not usual):
            default, rule = head, "the branch checked out in the source"
        elif usual:
            default, rule = usual[0], f"its name: a guess, the source has {head or 'a detached HEAD'} checked out. If that is wrong, tell the CEO; with their yes remove projects/{name} and rerun with --branch <name>"
    if not default:
        L.die(f"cannot tell the default branch of {src}: its HEAD is detached and it has no remote, main or master. "
              f"Check out the default branch there and import again.")

    c, _, e = L.run(["git", "clone", "-q", "--no-checkout", str(src), str(dest)])
    if c != 0:
        L.die(f"clone failed: {e}")
    if default in local:
        dgit("checkout", "-q", default, check=True)   # from the source's own branch, so commits never pushed come along
    fetched = False
    if url:
        dgit("remote", "set-url", "origin", url, check=True)
        fetched = dgit("fetch", "-q", "--prune", "origin")[0] == 0
        notes.append(f"origin: {scrub(url)}" + ("" if fetched else "  (could NOT fetch it just now: offline, or no access. "
                     "worktree.py add pulls first, so settle access with the CEO before any work starts)"))
        if scrub(url) != url:
            notes.append(f"NOTE: the origin URL contains a credential. It stays in projects/{name}/.git/config only.")
    else:
        dgit("remote", "remove", "origin", check=True)
        notes.append("origin: none. The code has no remote: register it with --status 'local only'. From now on "
                     f"projects/{name} is the company's copy; the original folder no longer receives the work.")
    if default not in local:
        if dgit("checkout", "-q", default)[0] != 0:
            L.die(f"the default branch is {default} ({rule}), but the source has no local branch of that name and it could "
                  f"not be fetched. Check it out in the source, or fix access to the remote, and import again.")
    notes.insert(0, f"default branch: {default} (from {rule}). Confirm it with the CEO if that surprises you.")
    if fetched:
        ahead = dgit("rev-list", "--count", f"origin/{default}..{default}")[1]
        if ahead.isdigit() and int(ahead) > 0:
            notes.append(f"NOTE: {default} has {ahead} commit(s) that are not on origin yet. They came along; pushing them is the CEO's call.")
    dirty = sgit("status", "--short")
    if dirty:
        notes.append(f"NOTE: {len(dirty.splitlines())} uncommitted file(s) in {src} were NOT imported. "
                     f"If they matter, the CEO commits them there and you pull them in.")
    others = [b for b in local if b != default]
    if others:
        notes.append(f"NOTE: other local branches there were not carried over: {', '.join(others[:8])}" + (" ..." if len(others) > 8 else ""))
    if (dest / ".gitattributes").is_file() and "filter=lfs" in (dest / ".gitattributes").read_text(errors="ignore"):
        notes.append(f"NOTE: this repo uses Git LFS. Run: git -C projects/{name} lfs pull")
    return f"cloned {src} into projects/{name} on {default}", notes


def import_plain(src, dest, name):
    nested = []

    def skip(folder, names):
        if ".git" in names and Path(folder) != src:
            nested.append(str(Path(folder).relative_to(src)))
        return [n for n in names if n in JUNK_DIRS or n in JUNK_FILES]
    shutil.copytree(src, dest, symlinks=True, ignore=skip)
    L.run(["git", "-C", str(dest), "init", "-q", "-b", "main"], check=True)
    files = [f for f in L.run(["git", "-C", str(dest), "ls-files", "-z", "--others", "--exclude-standard"])[1].split("\0") if f]
    big = sorted(((dest / f).stat().st_size, f) for f in files if (dest / f).is_file())[-5:]
    notes = [f"files that would be committed: {len(files)}; .gitignore present: {(dest / '.gitignore').exists()}"]
    notes += [f"large: {f} ({size // 1024} KB)" for size, f in reversed(big) if size > 1_000_000]
    notes += [f"WARNING looks like a secret, not ignored: {f}" for f in files if looks_secret(f)]
    if nested:
        notes.append(f"NOTE: nested git repos were copied as plain files, without their history: {', '.join(nested[:8])}")
    notes.append(f"next: write or fix projects/{name}/.gitignore (the CEO approves the edit), show the CEO the counts above, "
                 f"then: project.py commit {name} --all -m \"Import existing code\"")
    return f"copied {src} into projects/{name} (new git repo on main, nothing committed yet)", notes


# ---------------------------------------------------------------- survey

CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".cs", ".fs", ".go", ".rs", ".java", ".kt", ".swift", ".rb",
            ".php", ".dart", ".ex", ".exs", ".vue", ".svelte", ".c", ".cc", ".cpp", ".h", ".hpp", ".m", ".scala", ".sql", ".sh"}
TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|e2e|integration-tests?)/|(^|/)(test_[^/]*\.py|[^/]*_test\.(py|go|rb|dart|exs)"
    r"|[^/]*\.(test|spec|e2e)\.[cm]?[jt]sx?|[^/]*Tests?\.(cs|fs|java|kt|swift)|[^/]*_spec\.rb)$"
    r"|(^|/)[^/]*\.Tests?/", re.I)
SURVEY = [
    ("Manifests and lockfiles", [
        ("Node", ["package.json"]),
        ("Node lockfile", ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock"]),
        ("Node workspace", ["pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json"]),
        ("Deno", ["deno.json", "deno.jsonc"]),
        ("Python", ["pyproject.toml", "requirements*.txt", "Pipfile", "setup.py", "setup.cfg"]),
        ("Python lockfile", ["uv.lock", "poetry.lock", "Pipfile.lock"]),
        (".NET", ["*.sln", "*.slnx", "*.csproj", "*.fsproj", "*.vbproj", "Directory.Build.props",
                  "Directory.Packages.props", "global.json", "nuget.config"]),
        ("Go", ["go.mod"]), ("Rust", ["Cargo.toml"]),
        ("JVM", ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"]),
        ("Ruby", ["Gemfile"]), ("PHP", ["composer.json"]), ("Elixir", ["mix.exs"]),
        ("Dart / Flutter", ["pubspec.yaml"]),
        ("iOS / Swift", ["Package.swift", "Podfile", "project.pbxproj"]),
        ("Android", ["AndroidManifest.xml"]),
        ("React Native / Expo", ["app.config.js", "app.config.ts", "metro.config.js", "eas.json"]),
        ("Runtime versions", [".nvmrc", ".node-version", ".python-version", ".tool-versions", "mise.toml",
                              ".ruby-version", "rust-toolchain", "rust-toolchain.toml"]),
        ("Task runners", ["Makefile", "justfile", "Justfile", "Taskfile.yml", "Taskfile.yaml", "Tiltfile"]),
        ("Frontend build and UI config", ["vite.config.*", "next.config.*", "nuxt.config.*", "svelte.config.*", "astro.config.*",
                                          "angular.json", "webpack.config.*", "tailwind.config.*", "postcss.config.*",
                                          "components.json", "openapi-ts.config.*", ".storybook/"]),
    ]),
    ("Tooling config: lint, format, types, hooks", [
        ("Editor", [".editorconfig"]),
        ("JS / TS lint and format", [".eslintrc*", "eslint.config.*", ".prettierrc*", "prettier.config.*", "biome.json",
                                     "biome.jsonc", ".stylelintrc*"]),
        ("TypeScript", ["tsconfig*.json", "jsconfig.json"]),
        ("Python lint and types", ["ruff.toml", ".ruff.toml", ".flake8", "mypy.ini", "pyrightconfig.json", ".pylintrc",
                                   "tox.ini", "noxfile.py"]),
        (".NET analyzers", [".globalconfig", "stylecop.json", "*.ruleset", ".csharpierrc*"]),
        ("Other linters", [".golangci.y*ml", "rustfmt.toml", "clippy.toml", ".rubocop.yml", "phpcs.xml*", "phpstan.neon*",
                           "analysis_options.yaml", ".swiftlint.yml", "detekt.yml", "checkstyle.xml"]),
        ("Git hooks and commit rules", [".pre-commit-config.yaml", ".husky/", "lefthook.yml", "lefthook.yaml",
                                        "commitlint.config.*", ".commitlintrc*", ".lintstagedrc*", ".releaserc*",
                                        "release-please-config.json", ".changeset/"]),
    ]),
    ("Test setup", [
        ("Test runner config", ["jest.config.*", "vitest.config.*", "vitest.workspace.*", "playwright.config.*",
                                "cypress.config.*", "karma.conf.*", "pytest.ini", "conftest.py", ".mocharc*", "phpunit.xml*",
                                ".rspec", "*.runsettings", "xunit.runner.json", "codecov.yml", ".coveragerc", ".nycrc*"]),
        ("Mobile UI tests", [".maestro/", "maestro/"]),
    ]),
    ("CI and delivery", [
        ("GitHub Actions", [".github/workflows/"]),
        ("Other CI", [".gitlab-ci.yml", "azure-pipelines*.yml", "bitbucket-pipelines.yml", ".circleci/", "Jenkinsfile",
                      ".buildkite/", ".drone.yml", ".travis.yml"]),
        ("PR and ownership rules", ["CODEOWNERS", "pull_request_template.md", "PULL_REQUEST_TEMPLATE*",
                                    ".github/ISSUE_TEMPLATE/", "dependabot.yml", "renovate.json*"]),
        ("Hosting config", ["vercel.json", "netlify.toml", "fly.toml", "render.yaml", "Procfile", "app.yaml",
                            "railway.json", "railway.toml", "wrangler.toml", "wrangler.jsonc", "firebase.json",
                            "amplify.yml", "serverless.y*ml", "azure.yaml", "heroku.yml", "fastlane/"]),
    ]),
    ("Containers and infrastructure", [
        ("Docker", ["Dockerfile*", "*.dockerfile", ".dockerignore"]),
        ("Compose", ["docker-compose*.y*ml", "compose.y*ml", "compose.*.y*ml"]),
        ("Kubernetes / Helm", ["Chart.yaml", "kustomization.y*ml", "skaffold.yaml"]),
        ("Infrastructure as code", ["*.tf", "Pulumi.yaml", "cdk.json", "*.bicep"]),
        ("Dev container", [".devcontainer/"]),
    ]),
    ("Data and contracts", [
        ("Migrations", ["migrations/", "Migrations/", "alembic/", "db/migrate/", "flyway/", "liquibase/", "drizzle/"]),
        ("Schema and ORM config", ["schema.prisma", "alembic.ini", "knexfile.*", "drizzle.config.*", "ormconfig.*",
                                   "data-source.ts", "schema.rb", "*.dbml", "sqlc.yaml", "atlas.hcl"]),
        ("API contracts", ["openapi*.y*ml", "openapi*.json", "swagger*.json", "swagger*.y*ml", "*.proto", "*.graphql",
                           "*.graphqls", "codegen.y*ml", "codegen.ts"]),
        (".NET settings", ["appsettings*.json", "launchSettings.json"]),
    ]),
    ("Docs and agent instructions", [
        ("Readme and docs", ["README*", "CONTRIBUTING*", "ARCHITECTURE*", "CHANGELOG*", "LICENSE*", "SECURITY*"]),
        ("Decision records", ["docs/adr/", "doc/adr/", "adr/", "docs/decisions/"]),
        ("Domain glossary", ["CONTEXT.md", "GLOSSARY*"]),
        ("Agent instructions", ["CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".windsurfrules", ".cursor/rules/",
                                "copilot-instructions.md", ".claude/", ".agents/"]),
    ]),
]


def survey_hits(files, pat):
    """Paths matching one pattern. 'name/' means any folder with that path; otherwise fnmatch on the base name."""
    if pat.endswith("/"):
        found = Counter()
        for f in files:
            i = ("/" + f).find("/" + pat)
            if i >= 0:
                found[f[:i] + pat] += 1
        return [f"{d} ({n} files)" for d, n in sorted(found.items())]
    return [f for f in files if fnmatch.fnmatchcase(f.rsplit("/", 1)[-1], pat)]


def code_list(items, cap=8):
    shown = ", ".join(f"`{x}`" for x in items[:cap])
    return shown + (f" (+{len(items) - cap} more)" if len(items) > cap else "")


def fence(lines):
    return ["", "```text", *[l.replace("`", "'") for l in lines], "```", ""]


def cmd_survey(a):
    p = L.repo_main(a.name)

    def git(*args):
        return L.run(["git", "-C", str(p), *args])[1]
    files = sorted({f for f in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0") if f})
    if not files:
        L.die(f"projects/{a.name} has no files")
    has_commits = L.run(["git", "-C", str(p), "rev-parse", "--verify", "-q", "HEAD"])[0] == 0
    o = [f"# Survey: {a.name}", "",
         f"Generated by `python3 scripts/project.py survey {a.name}` on {L.today()}"
         + (f", at commit `{git('rev-parse', '--short', 'HEAD')}` on `{git('symbolic-ref', '--short', 'HEAD') or 'detached HEAD'}`." if has_commits else ", before the first commit.")
         + " Facts from file names and git history only. The only file contents read are `.gitattributes`, the image lines of compose files "
           "and the variable names of example env files. It says what exists, not what it means: open the files before "
           "concluding anything.", ""]

    o += ["## Git", ""]
    if has_commits:
        subjects = git("log", "-200", "--format=%s").splitlines()
        merges = len(git("log", "-200", "--merges", "--format=%h").splitlines())
        prs = sum(1 for s in subjects if s.startswith("Merge pull request") or re.search(r"\(#\d+\)$", s))
        conv = sum(1 for s in subjects[:50] if re.match(r"(feat|fix|chore|docs|refactor|test|build|ci|perf|style|revert)(\([^)]*\))?!?: ", s))
        dates = git("log", "--format=%ad", "--date=short").splitlines()
        authors = git("shortlog", "-sn", "--no-merges", "HEAD").splitlines()
        remote = scrub(git("remote", "get-url", "origin"))
        o += ["- Remote: " + (f"`{remote}`" if remote else "none"),
              f"- Working tree clean: {'yes' if not git('status', '--short') else 'NO'}",
              f"- Commits: {len(dates)}, first {dates[-1]}, last {dates[0]}",
              f"- Authors with commits: {len(authors)}" + (" (more than one: ask the CEO who else works in this repo)" if len(authors) > 1 else ""),
              f"- Last {len(subjects)} commits: {merges} merge commits, {prs} that came through a pull request"
              + (" (looks like a pull-request workflow)" if prs >= 5 else ""),
              f"- Conventional-commit subjects in the last {min(50, len(subjects))}: {conv}",
              f"- Submodules: {'yes' if (p / '.gitmodules').exists() else 'no'}; "
              f"Git LFS: {'yes' if 'filter=lfs' in ((p / '.gitattributes').read_text(errors='ignore') if (p / '.gitattributes').is_file() else '') else 'no'}",
              "", "Top authors, recent commit subjects, remote branches, latest tags:"]
        remote_branches = [b for b in git("branch", "-r", "--format=%(refname:short)").splitlines() if "/" in b]
        o += fence([" ".join(x.split()) for x in authors[:5]] + ["--"] + subjects[:12] + ["--"]
                   + (remote_branches[:15] or ["(no remote branches)"]) + ["--"]
                   + (git("tag", "--sort=-creatordate").splitlines()[:5] or ["(no tags)"]))
    else:
        o += ["- No commits yet.", ""]

    o += ["## Size and shape", "", f"- Files: {len(files)}"]
    tops = Counter(f.split("/", 1)[0] + "/" if "/" in f else "(root files)" for f in files)
    exts = Counter(Path(f).suffix.lower() or "(none)" for f in files)
    o += ["- Top level: " + ", ".join(f"`{d}` {n}" for d, n in tops.most_common(15)),
          "- Extensions: " + ", ".join(f"`{e}` {n}" for e, n in exts.most_common(15)), ""]

    for title, groups in SURVEY:
        o += [f"## {title}", ""]
        lines = []
        for label, pats in groups:
            hits = sorted({h for pat in pats for h in survey_hits(files, pat)}, key=lambda h: (h.count("/"), h))
            if hits:
                lines.append(f"- {label}: {code_list(hits)}")
        counted = title in ("Test setup", "Data and contracts", "Docs and agent instructions")
        o += (lines or ([] if counted else ["- Nothing found."])) + [""]
        if title == "Test setup":
            tests = [f for f in files if TEST_PATH.search(f)]
            dirs = Counter(f.rsplit("/", 1)[0] if "/" in f else "." for f in tests)
            o[-1:] = [f"- Files that look like tests: {len(tests)} of {len(files)}"
                      + (". Most in: " + code_list([d for d, _ in dirs.most_common(6)]) if tests else ""), ""]
        if title == "Containers and infrastructure":
            images = set()
            for f in files:
                if re.fullmatch(r"(docker-)?compose[^/]*\.ya?ml", f.rsplit("/", 1)[-1]) and (p / f).is_file():
                    images |= set(re.findall(r"^\s*image:\s*[\"']?([^\s\"'#]+)", (p / f).read_text(errors="ignore")[:200_000], re.M))
            if images:
                o[-1:] = [f"- Images named in compose files: {code_list(sorted(images), 20)}", ""]
        if title == "Data and contracts":
            o[-1:] = [f"- `.sql` files: {sum(1 for f in files if f.lower().endswith('.sql'))}", ""]
        if title == "Docs and agent instructions":
            root_md = [f for f in files if "/" not in f and f.lower().endswith(".md")]
            docs = sum(1 for f in files if f.lower().startswith(("docs/", "doc/")))
            o[-1:] = [f"- Markdown files at the root: {code_list(root_md, 15) or 'none'}", f"- Files under `docs/`: {docs}", ""]

    o += ["## Environment", ""]
    names = []
    examples = [f for f in files if re.search(r"(^|/)([^/]*\.)?env[^/]*$", f, re.I) and EXAMPLE_FILE.search(f)
                or re.search(r"(^|/)(example|sample)\.env$", f, re.I)]
    for f in examples:
        if (p / f).is_file():
            names += re.findall(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", (p / f).read_text(errors="ignore")[:200_000], re.M)
    tracked = [f for f in git("ls-files", "-z").split("\0") if f and looks_secret(f)]
    o += [f"- Example env files: {code_list(examples) or 'none'}",
          f"- Variable names in them (names only, values never read): {code_list(sorted(set(names)), 60) or 'none'}"]
    o += [f"- WARNING tracked in git and looks like a secret (not opened; tell the CEO): {code_list(tracked, 20)}"] if tracked else []
    o += [""]

    sizes = []
    for f in files:
        q = p / f
        if Path(f).suffix.lower() in CODE_EXT and q.is_file() and q.stat().st_size < 3_000_000:
            with open(q, "rb") as fh:
                sizes.append((sum(1 for _ in fh), f))
    o += ["## Largest source files", ""]
    o += [f"- `{f}`: {n} lines" for n, f in sorted(sizes, reverse=True)[:10]] or ["- No source files recognised."]
    o += [""]

    text = "\n".join(o)
    if a.out:
        dest = Path(a.out).expanduser()
        dest = dest if dest.is_absolute() else L.ROOT / dest
        if not dest.parent.is_dir():
            L.die(f"no such folder: {dest.parent}")
        L.write_md(dest, text)
        print(f"survey of projects/{a.name} written to {L.rel(dest)} ({len(files)} files looked at)")
    else:
        print(text)


def cmd_register(a):
    if a.status not in STATUSES:
        L.die(f"status must be one of: {', '.join(STATUSES)}")
    head, rows, tail = reg_rows()
    url = scrub(a.url) or (f"https://github.com/{a.repo}" if re.fullmatch(r"[\w.-]+/[\w.-]+", a.repo) else "")
    repo = L.clean_cell(scrub(a.repo))
    cell = f"[{repo}]({url})" if url else (f"`{repo}`" if re.search(r"[:/\\]", repo) else repo)
    row = next((r for r in rows if r["Name"] == a.name), None)
    if row:
        row.update({"GitHub repo": cell, "Purpose": a.purpose or row["Purpose"], "Status": a.status})
    else:
        rows.append({"Name": a.name, "GitHub repo": cell, "Purpose": a.purpose or "", "Status": a.status, "Created": L.today()})
    body = [L.table_row([L.clean_cell(r[c]) if c != "GitHub repo" else r[c] for c in COLS]) for r in rows]
    L.write_md(REG, "\n".join(head + body + tail))
    L.journal_add(f"project {a.name}: registry row set ({a.status})")
    print(f"registered {a.name} [{a.status}]")


def cmd_list(a):
    _, rows, _ = reg_rows()
    for r in rows:
        here = (L.ROOT / "projects" / r["Name"] / ".git").exists()
        print(f"{r['Name']}  [{r['Status']}]  {r['GitHub repo']}  local clone: {'yes' if here else 'NO'}")
    if not rows:
        print("no projects registered")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("name")
    c = sub.add_parser("commit"); c.add_argument("name"); c.add_argument("-m", "--message")
    c.add_argument("--all", action="store_true"); c.add_argument("--allow", action="append", metavar="PATH")
    cl = sub.add_parser("clone"); cl.add_argument("source"); cl.add_argument("name", nargs="?")
    il = sub.add_parser("import-local"); il.add_argument("path"); il.add_argument("name", nargs="?")
    il.add_argument("--init", action="store_true"); il.add_argument("--remote", help="which remote of the source becomes origin, when it has several")
    il.add_argument("--branch", help="the default branch, when the script cannot tell or guesses wrong")
    sv = sub.add_parser("survey"); sv.add_argument("name"); sv.add_argument("--out")
    r = sub.add_parser("register"); r.add_argument("name"); r.add_argument("--repo", required=True)
    r.add_argument("--purpose"); r.add_argument("--status", default="active"); r.add_argument("--url")
    sub.add_parser("list")
    a = ap.parse_args()
    {"init": cmd_init, "commit": cmd_commit, "clone": cmd_clone, "import-local": cmd_import_local, "survey": cmd_survey,
     "register": cmd_register, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
