# Rule: file discipline

Constraints on writing, editing, or deleting project files.

## Read-only by default

These directories are read-only unless an explicit, user-approved execute-phase task says otherwise:

- `data/raw/` — **never modified**, period. No exceptions. If raw data needs to be corrected, the correction goes in a cleaning script that produces output to `data/clean/`.
- `code/` — only modified during execute-phase tasks the user has approved
- `paper/` — same as code; manuscript edits go through fix plans, not direct edits
- `vendor/` — never modify; vendored code updates via submodule pull

These directories are write-allowed:

- `.planning/` — workflow state lives here; STATE.md gets appended frequently
- `output/`, `tables/`, `figures/` — regenerable outputs
- `data/clean/`, `data/derived/` — outputs of cleaning/derivation scripts

## Before any write

Confirm the write is in a write-allowed directory. If not, surface as a question: "this would modify `paper/main.tex`; is this an approved fix-plan task or do you want me to skip?"

## Before any delete

Always confirm with the user. Particularly:

- `.planning/` files: every file in here is potentially load-bearing for the audit trail
- Anything tracked by git: prefer `git rm` and let the user commit, rather than file-system delete
- Submodules: never `rm -rf vendor/X`; always `git submodule deinit` first

Never delete `.planning/STATE.md` or `.planning/ROADMAP.md` — these are the framework's memory.

## Glob and grep are free

Reading is cheap and has no side effects. Use generously: when in doubt about project structure, glob first. Don't ask the user where a file is if you can find it.

## Don't generate code in commands that aren't execute-phase

The `/gsd-plan-empirics` command produces a plan, not code. The `/gsd-discuss-identification` command produces a discussion record, not code. Code generation happens in `/gsd-execute-phase`. If you find yourself wanting to write code in a non-execute command, stop — surface the question of whether this should become a fix plan instead.
