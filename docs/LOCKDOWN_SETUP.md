# Repo Lockdown Setup — one-time admin steps

The issue → PR pipeline is merged. These steps need repository **admin**
(none of the bot accounts have it) — ~5 minutes total.

## 1. Secrets (Settings → Secrets and variables → Actions)

Add both, same values as exp-manager:

| Secret | Value |
|---|---|
| `ANTHROPIC_AUTH_TOKEN` | the GLM proxy token (from `~/.claude/settings.json` on the hgx box, or copy from exp-manager's secret) |
| `ANTHROPIC_BASE_URL` | the GLM proxy base URL (same source) |

Without these the issue-fixer job dies on its first `claude` call.

## 2. Self-hosted runner (Settings → Actions → Runners)

The workflows use `runs-on: [self-hosted, Linux, X64]` — the hgx box that
runs exp-manager's jobs. Confirm it appears in this repo's runner list; if
not, register it (Settings → Actions → Runners → New self-hosted runner;
the box can serve multiple repos). A workflow on a runner that isn't
registered queues forever — the first test issue will reveal it either way.

The runner needs on PATH (front-loaded in the workflow env, verify they
resolve under the runner's systemd context):
- `uv` (`/home/sani/.local/bin`)
- `cargo` (`/home/sani/.cargo/bin`)
- `node`/`npm` (`/home/sani/.nvm/versions/node/v24.14.0/bin`)

## 3. Branch protection (Settings → Branches → Add rule, `main`)

- ✅ Require a pull request before merging
  - ✅ Require approvals: **1**
  - ✅ Require review from Code Owners *(optional — add a CODEOWNERS file if you want specific reviewers forced)*
- ✅ Require status checks to pass before merging
  - Required checks: `test`, `rust-core`, **`test-review / gate`**
    *(type the names into the search box; `test-review / gate` appears once the workflow has run once)*
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above settings
- ✅ Restrict who can push to matching branches *(nobody but admins, i.e. you)*

With this: direct pushes to main are blocked; PRs from the fixer carry
`needs-test-review`, which makes `test-review / gate` fail → merge
impossible. The ticket creator comments `/tests-approved` → label removed
→ gate passes → all three checks green → you merge.

## 4. The flow after setup

```
user files issue
      │
      ▼  (actor-gated: khursani8 opens, or labels any issue)
claude-issue-fixer runs on hgx box
  claude -p --dangerously-skip-permissions
  edits Rust + regenerates fixtures + adds tests
  ALL gates green locally (cargo/pytest/clippy/ruff) or no PR
      │
      ▼
PR opened: claude/issue-N, labeled needs-test-review, "Closes #N"
      │
      ▼
ticket creator reviews the unit tests in the diff
      │  comments /tests-approved (creator or khursani8 only)
      ▼
label removed → test-review / gate passes
      │
      ▼
test + rust-core green (CI: wheel build, 498-suite, snapshots, clippy)
      │
      ▼
admin merges
```

## Opt-out

Label an issue `no-autofix` and the fixer will not pick it up.
