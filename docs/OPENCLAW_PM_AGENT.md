# OpenClaw PM Agent Setup (chatui-pm)

This repo’s PM loop (`backend/pm_loop_gh.py`) can call an OpenClaw agent to:
- analyze/dedupe feedback before creating GitHub issues (triage mode)
- optionally apply/implement a selected issue (apply mode)

The recommended setup is to create a **dedicated agent** named `chatui-pm` so automation does not contend with your main OpenClaw chat session.

## Prerequisites

- OpenClaw installed and Gateway running
- GitHub CLI installed and authenticated:

```bash
gh auth status
```

- Repo checked out locally

## 1) Create the agent

From your machine:

```bash
openclaw agents add chatui-pm \
  --workspace ~/chatui \
  --model openai-codex/gpt-5.2
```

Notes:
- `--workspace` should point at the **repo root**.
- You can use a different model if desired, but `openai-codex/gpt-5.2` is the default used by this project.

Restart the gateway so the new agent is loaded:

```bash
openclaw gateway restart
```

Verify:

```bash
openclaw agents list
```

You should see an entry like:

- `chatui-pm` (Workspace: `~/chatui`, Model: `openai-codex/gpt-5.2`)

## 2) Configure env vars (optional)

Defaults are fine for the `ninjapapa/chatui` repo, but you can override:

```bash
export PM_AGENT_ID=chatui-pm
export GITHUB_REPO=ninjapapa/chatui
```

## 3) Run the PM loop

### Triage (analyze feedback + create issues)

```bash
cd ~/chatui/backend
source .venv/bin/activate
python pm_loop_gh.py --mode triage
```

### Apply (implement a specific issue)

```bash
cd ~/chatui/backend
source .venv/bin/activate
python pm_loop_gh.py --mode apply --issue 123
# or
python pm_loop_gh.py --mode apply --issue https://github.com/<owner>/<repo>/issues/123
```

Apply mode behavior:
- Requires a clean git working tree
- Uses OpenClaw to implement changes (agent must NOT commit/push)
- Runs tests, commits, pushes

## 4) One-command script

From repo root:

```bash
./scripts/pm_loop_run.sh
```

By default this runs triage and then applies the first newly created issue from the latest daily plan.

You can disable auto-apply:

```bash
PM_LOOP_APPLY=0 ./scripts/pm_loop_run.sh
```

## Troubleshooting

### “Failed to fetch” in the UI
If running Vite on a port other than 5173 (e.g. 5174), ensure your backend CORS allows 517x dev origins.

### “npm test” exit 127 in apply mode
This can happen in non-interactive shells when `node` isn’t on PATH (nvm not loaded). The repo scripts set PATH for you; if you run manually, ensure node is available.
