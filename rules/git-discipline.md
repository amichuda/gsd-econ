# Rule: git discipline

Constraints on commits, branches, and history.

## Atomic commits

One logical change per commit. Examples of atomic units:

- A regression specification added or modified
- A robustness column added to an existing table
- A paragraph rewrite in the manuscript
- A figure regeneration with new caption
- A pre-commit lint fix
- A bug fix in cleaning code, with corresponding output change

Examples of non-atomic commits to avoid:

- "WIP" omnibus commits
- "Fix various things"
- A commit that mixes manuscript edits, code edits, and table regeneration in one shot

## Commit message conventions

Format: `<type>(<scope>): <summary>`

Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `polish`. Scope is the affected area (e.g., `methodology`, `tables`, `paper`, `cleaning`).

The summary line is imperative ("add Conley SEs to Table 3", not "added"). Below it, when needed, a longer explanation of *why*.

## Never force-push without explicit user approval

Force-pushing rewrites history and can erase coauthors' work. If you find yourself wanting to `git push --force` or `git push --force-with-lease`, stop and ask. The only acceptable use is rewriting your own local feature branch that no one else has based work on, and even then confirm with the user.

## Never `git rebase` shared branches

If a branch has been pulled by anyone else, don't rebase it. Use merge commits instead.

## Submodule updates are deliberate

Never bump a submodule reference (`git add vendor/research-unit-tests`) without explicit user approval, especially if the submodule has new commits the user hasn't reviewed. The point of the submodule is intentional version pinning.

## Don't commit large files

Anything over 50 MB → `.gitignore` it and use Git LFS, dataverse, or a separate storage. Don't add it. Particularly:

- Compiled PDFs of working papers (regenerable from source)
- Compiled HTML reports
- `.RData`, `.RDS`, large parquet files
- Image files larger than 5 MB unless they're the actual paper figures

## Don't commit credentials or PII

`.env` files, API tokens, paths containing usernames-as-IDs, names-as-village-IDs in any data file — these never get committed. Add to `.gitignore` first, commit second.

## When unsure

Stage but don't commit. Show the user `git diff --cached` and ask whether to proceed.
