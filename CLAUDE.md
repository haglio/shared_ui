
## Test fixtures must be fabricated, never copied from the real library

Every fixture value that stands in for library data — a video title, a filename,
a performer or studio name, prompt text — must be **invented**. Never paste a
real one out of the media library to make a test feel realistic.

This is not a style note. It is the single thing that has actually leaked private
data into these repos: an agent writing a test reached for a real filename or
performer name because it was handy, and it rode into a public commit. Nothing in
the app's *design* pulls library text into source — the library lives outside
every repo, read at runtime through the git-ignored overlays — so this habit is
the only remaining path for a real name to get committed, and the only thing
stopping it is you following this rule.

Do not lean on the sanitize guard to catch it. `app_support.sanitize` fails
the suite when a **known** blocked term appears in the tracked tree, but a brand-
new performer name it has never seen passes every check and lands. The guard is a
backstop for names already known; it cannot see the next one.

So fabricate fully. Use `Jane Doe`, `Example Studio`, `scene one`, the
`alpha`/`beta`/`gamma` act placeholders the family's committed overlay examples
use. The near miss that still counts: taking a real filename and
changing a character or two — it is still that clip, still that performer. Make
it up from scratch, don't lightly edit a real one.

## No pane's contents touch its edges — every pane takes the standard inner margin

Every pane an app builds with this package gets the family's standard inner
margin, and that margin comes from the one shared constant,
`shared_ui.spacing.MARGIN_STANDARD` — never a number typed in at the call site,
which drifts from every other pane the first time either changes. Content flush
against a splitter handle or a window edge reads as cut off. A splitter adds no
margin of its own, so a scroll area or a panel handed straight to one lands hard
against the handle although no line of code ever set a margin of zero: apply the
margin wherever the app makes its panes, in every app that draws panes with this
package.

## The loading screen answers the click — every wait before an app is up is a step on it

The loading screen exists so that a click on a launcher is answered at once with
what is happening and how far along it is. So it comes up the moment the
launcher is clicked, and everything the launch waits on before the app is usable
is a step on it with the bar moving: an update the launcher waits out, a hosted
app's boot, a check before the first window. A wait with nothing on screen reads
as a click that did nothing, and gets clicked again. The near miss that still
counts: a note or message box of the launcher's own for the wait, which says
apart from the loading screen what the loading screen is for.

## Landing — GitHub merge queue, not local ff-merge

This repo is public at `github.com/haglio/shared_ui` with a merge-queue ruleset on
`main`, so the global "ff-merge into the primary checkout under
`.git/agent-merge.lock`" flow does NOT apply here:

- **Land through a pull request.** From your worktree: commit, `git fetch origin
  && git rebase origin/main`, `git push -u origin <branch>`, then
  `gh pr create --fill`. Auto-merge arms itself; the queue rebases your PR onto
  `main`, runs the required check, and merges it when green. Don't ff-merge into
  the primary checkout, don't push `main` directly, and never force-push `main`.
- **The `.git/agent-merge.lock` is retired here** — the GitHub queue serializes.
- **The production updater moves the primary checkout; never pull it yourself.**
  `main` advances only on origin (via the queue), and app_support's production
  updater brings the primary checkout up to it within a few minutes, so
  worktrees update with `git rebase origin/main` and the primary is never
  pulled, reset or merged into by hand.
- **A red required check** (`.github/workflows/merge-gate.yml`) can't land.

Everything else in the global CLAUDE.md — work in a worktree, green tests before
you push, clean handoff — still applies.
