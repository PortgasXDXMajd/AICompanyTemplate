---
name: qa-check
description: Hands-on QA of finished work - run the product from the employee's worktree and use it like a customer would. Web apps in a real browser (Claude in Chrome, or Playwright), mobile apps in an Android emulator or iOS simulator (Maestro), APIs and CLIs through their real entry point. Judges whether it works and whether the UI and UX are good, and saves evidence. Use after review fixes are in and before handing code with a user-facing surface to the CEO, and whenever the CEO asks to "try it", "click through it" or "test it in the browser / emulator".
argument-hint: <job-id or project> [flows to check]
---

# Hands-on QA

Tests prove the code does what the developer thought of. QA finds what nobody thought of: the button that does nothing, the error no one sees, the screen that makes no sense on a phone.

Target: $ARGUMENTS

## Who runs it, and with what

The tools decide who can do this:

| Surface | First choice | Fallback |
|---|---|---|
| Web app, site | **Claude in Chrome**: a real browser the CEO can watch. Needs the Claude in Chrome extension and a session started with `claude --chrome` (or `/chrome`). It does not work in headless `-p` runs, and in-process subagents do not get its tools. | **Playwright MCP**, headless and available to any session: `claude mcp add playwright -- npx -y @playwright/mcp@latest` |
| Mobile app (native, React Native, Flutter, Expo) | **Maestro** on an Android emulator or iOS simulator: `claude mcp add maestro -- maestro mcp` (needs Java 17+). iOS simulators exist only on macOS with Xcode. | Android without Maestro: `adb` (`uiautomator dump` for element bounds, `input tap`, `exec-out screencap -p`). Responsive web or PWA target: browser device emulation, reported as "web-emulated, not device-verified". |
| API, CLI, background job | Call it for real: `curl`, the CLI binary, a script. | none needed |

- Inside Herdr, start a QA helper in its own tab with the `delegate` skill (`python3 scripts/agent.py start --job <job-id> --helper qa --chrome`), so the browser tools are in that session and the CEO can watch. Brief: this file, the plan's QA section or the spec's definition of done, the worktree path, and how to run the product (from the developer's hand-back).
- In a plain terminal, the Chief of Staff runs QA itself in its own session if that session has the browser tools, or delegates to a helper subagent when only Playwright or Maestro (MCP servers, available to subagents) are needed.
- The project's `CLAUDE.md` names the QA tooling the CEO chose ("Hands-on QA" row). Use that.

Probe before you promise anything:

```bash
python3 scripts/qa_probe.py          # Playwright and Maestro MCP servers, Maestro, Java, adb, emulators and acceleration, devices, iOS simulators
```

It ends with what web QA and mobile QA can use on this machine. Claude in Chrome cannot be probed from a script: look for `mcp__claude-in-chrome__*` in your own tool list.

An MCP server added now is only available after the session restarts; the job system survives that. No hardware acceleration (`emulator -accel-check` fails) and no device in `adb devices`: mobile QA is not possible on this machine. Never boot an unaccelerated emulator; offer a USB device or a run on the CEO's Mac instead.

**If the tools are not there, say so.** Write `qa.md` with `Verdict: not performed: <what is missing>`, tell the CEO the one command that would fix it, and for mobile still write the Maestro flows so they can be run later. Never describe a check you did not do.

## Steps

1. **Run it from the worktree**, not the main checkout: install, then start it with the project's run command as a background process. Wait until it answers with `python3 scripts/qa_probe.py wait-url <url>` (it polls and gives up after five minutes), or poll `adb shell getprop sys.boot_completed` for an emulator; never sleep for a fixed time. Mobile: boot the emulator or simulator (`maestro start-device --platform android|ios`, or `emulator -avd <name>`, add `-no-window` on a machine without a display), build and install a development build. Expo Go cannot run custom native code and cannot be launched by app id, so prefer `npx expo run:android` / `run:ios`.
2. **Walk the flows** from the plan's QA section, or derive them from the definition of done. At minimum: the happy path from a cold start as a first-time user; one way it can fail (bad input, empty form, no network, wrong password); the empty state before any data exists; and coming back to it (reload, reopen the app).
3. **Look under the surface.** Web: console errors and failed network requests on every page you touch. Mobile: `adb logcat` or the simulator's crash logs. An API: status codes and error bodies for bad input.
4. **Look at it on more than one size.** Web: a phone width (about 375 px) and a desktop width; resize the window and take a screenshot of each key screen. Mobile: one small and one large device if both are available.
5. **Judge the experience**, not only whether it works:
   - Can a first-time user finish the flow without guessing what to do next?
   - Does every action get feedback: loading, success, and an error they can understand and recover from?
   - Are empty, loading and error states designed, or blank?
   - Is anything cut off, overlapping, unreadable, or too small to tap at phone width?
   - Does the keyboard work: tab order, focus you can see, Enter submits?
   - Is the wording clear, consistent, and in the buyer's language (`context/company.md`)?
   - Does it keep the promise the company makes to this buyer?
6. **Save evidence** in `jobs/<job-id>/qa/`: a named screenshot of each key screen and of every problem, a GIF of the main flow when the tool can record one, console or log excerpts, and for mobile the Maestro flow files. You do not change the product repo. Name the flows worth keeping as regression tests in `qa.md`; the Chief of Staff puts them into the developer's next fix brief (`.maestro/`, or the project's end-to-end test folder).
7. **Write `jobs/<job-id>/qa.md`**: what you ran and how, the tools and device sizes, each flow with pass or fail, then findings ranked **blocker** (broken, misleading, or a first-time user gets stuck), **should fix**, and **polish**, each with its screenshot. End with the line `Verdict: pass | pass with fixes | fail`. When nothing a user sees or touches changed, the whole file is one line: `Verdict: skipped: no user-facing surface`.
8. **Clean up.** Stop the dev server and the emulator you started, close the browser tabs you opened, and leave `git status` in the worktree as you found it.

Blockers go back to the developer as a fix round in the same worktree, and QA re-checks only those (`qa-2.md`). Two fix rounds at most; `REVIEW.md` section 4 says what else is re-checked. Should-fix items go into the hand-off for the CEO to decide. After QA passes, the Chief of Staff copies the best evidence into `demos/`.

## Rules

- Never type real credentials, payment details or customer data. Use the test accounts named in the project's `CLAUDE.md`; if there are none, ask the CEO.
- A login wall, a CAPTCHA or a permission dialog you cannot pass: stop and ask the CEO to handle it in the browser, then continue.
- Avoid anything that opens a native browser dialog (`alert`, `confirm`, `prompt`): it freezes browser automation. If the product does that, it is a finding.
- Only localhost and the project's own staging URLs. Production is for the CEO.
- You change no code. You report.
