# AGENTS.md

Agent instructions for the RevNext-TUNE monorepo. Nested `packages/AGENTS.md` adds Python package conventions when working under `packages/`.

## Project structure

### Two independent packages only

- **packages/tune_dms/** → installable as `tune-dms` (`pip install tune-dms`). TUNE DMS GUI automation; depends on pyautogui only; includes reference images in `tune_dms/images/`.
- **packages/revnext/** → installable as `revnext` (`pip install revnext`). Revolution Next report downloads via REST API; depends only on `requests`.

There is **no meta package**. Users who want both run:
`pip install tune-dms revnext`

Do not add a root-level installable package that depends on both. Do not add a `revnext_tune`-style shim that re-exports from both.

### Layout

- Root has **no** `pyproject.toml` that builds an installable package there. The installable packages live under **packages/** only.
- All installable code lives under **packages/** with one folder per package; each package has its own `pyproject.toml`.
- Configuration: each package has its own `config` module (e.g. `TuneConfig`, `RevNextConfig`) with `from_env()` and optional env vars. No shared config package across the two.

### DRY (Don't Repeat Yourself)

- **Between packages:** Do not duplicate code across `tune_dms` and `revnext`. They are independent: no shared Python modules, no cross-imports. If logic is conceptually shared, implement it once per package in the package that needs it; do not create a third shared package unless we explicitly add one.
- **Within a package:** Avoid duplicate logic inside the same package. Use helpers, config objects, and clear function boundaries. Reuse via composition and parameters (e.g. `base_url`, `cookies_path`) rather than copy-paste.
- **Config/env:** Each package reads its own env vars and exposes its own config API; document in README and .env.template. No shared env module.

### README as developer docs (and PyPI long description)

- **Treat each package README as the developer documentation** for that package: it is the primary place for how to install, configure, and use the project.
- **Root README** describes the monorepo and points to the two packages; **package READMEs** (e.g. `packages/revnext/README.md`, `packages/tune_dms/README.md`) are the usage and API docs for that package.
- **PyPI display:** The long description shown on the PyPI package page is typically rendered from the package’s README (via `readme` in `pyproject.toml`). Keep package READMEs clear, up-to-date, and suitable for both GitHub and PyPI so users downloading the package see accurate install/usage instructions.

### Renaming and moving files

- **Use `git mv`** when renaming or moving files (e.g. `git mv old_path new_path`). This preserves history so `git log --follow` and blame work correctly.
- Do not move files by copying content to a new path and deleting the old one; that breaks rename detection and loses history.

### Editable installs

From repo root:

- `pip install -e ./packages/tune_dms`
- `pip install -e ./packages/revnext`

Users import as: `from tune_dms import ...` and `from revnext import ...`.

## READMEs and refactor preference

### Keep READMEs up-to-date

- **Update the relevant README whenever code or usage changes.** When you add, remove, or change features, APIs, scripts, config, or usage, update the corresponding README so it stays accurate.
- **Root** `README.md`: monorepo layout, how to install each package, links to package docs. Update when adding packages, scripts, or changing how the repo is used.
- **Package READMEs** (e.g. `packages/revnext/README.md`, `packages/tune_dms/README.md`): install, config, and usage for that package. Update when adding or changing reports, enquiries, APIs, env vars, or examples.
- Do not leave READMEs out of date after a change. If in doubt, update the README as part of the same task.

### Prefer refactor over fallbacks

- **We are the only users of this repo.** There is no need to preserve backward compatibility for external consumers.
- **Do not add fallbacks** or compatibility layers just to keep previous code working. Prefer to **refactor the code directly** (rename, change signatures, remove deprecated paths).
- When changing behavior or APIs, update call sites and docs in one go rather than supporting old and new behavior.

## Repeated tasks and reminders

### When asked to do something multiple times

- **Complete every instance.** If the user asks to do X for A, B, and C (or “also do X”, “and do Y”), do it for **all** of them. Do not stop after the first item unless the user says so.
- **Batch when possible.** If the same change applies to several files or items, list them, make the changes to all, then verify (e.g. run lint once at the end).
- **Confirm scope.** If “do this for all X” is ambiguous, quickly clarify (e.g. “all reports” vs “all scripts”) then do all of them.

### Using this file as a note / reminder

- **This reminders section is a living note.** You can add or edit the **Reminders** list below. The agent should read it and follow relevant reminders when the conversation context matches (e.g. before committing, when adding a feature, when touching docs).
- **When a reminder applies,** do the thing (or prompt the user) instead of skipping it. If the user said “remind me to X”, add X to the Reminders list and acknowledge it.

### Reminders (edit this section like a note)

- Before pushing or opening a PR: run `ruff check .` and `ruff format --check .` (or `ruff format .` to fix); fix any reported issues.
- When adding a new report or API in revnext: update `packages/revnext/README.md` if it changes how users use the package.
- When adding a new script: consider putting it in `scripts/revnext/` or `scripts/tune/` and document how to run it in the script docstring.
- When changing features, APIs, or usage: keep the relevant README up-to-date (see **READMEs and refactor preference** above).

*(Add more reminders below as needed.)*
