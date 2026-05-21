# VPM Tools — Project Agent Instructions

## WAT Framework Overview

You are operating within the WAT (Workflows, Agents, Tools) framework, which separates reasoning from execution to ensure reliability and maintainability.

- **Workflows (Layer 1):** Markdown SOPs stored in `/workflows`. Each file defines objectives, inputs, required tools, expected outputs, and edge-case handling.
- **Agents (Layer 2):** You. Your role is to read workflows, coordinate tool execution in sequence, and handle failures gracefully.
- **Tools (Layer 3):** Python scripts stored in `/tools`. These perform deterministic, repeatable actions — API calls, data transformations, file operations, etc.

---

## About This Project

This is the monorepo for VPM (Virginia's home for public media — vpm.org), a public media newsroom. It contains automation tools, workflow documentation, and scripts for the web team.

**Key people:**
- Mike Hayes — web team lead (you're working for him)
- Michael, Leandra — colleagues on newsletter and content work

**Important:** VPM is "Virginia's home for public media" — not "Virginia Public Media." This distinction matters legally and in all copy.

---

## VPM Tech Stack

| System | Purpose | Notes |
|--------|---------|-------|
| Brightspot | Legacy CMS | Being retired — archive workflows, don't build new ones |
| WordPress | Incoming CMS | Migration in progress — stub workflows here first |
| Chartbeat | Analytics | API-based; `insights.py` pulls historical data |
| Mailchimp | Email / Newsletter | Update Profile forms for subscriber data collection |
| Megaphone | Podcast hosting | RSS feeds; episode audio uploads |
| GitHub | Code + automation output | Issues used as delivery mechanism for analytics briefings |
| Anthropic API | AI-generated briefings | claude-sonnet for weekly analytics summaries |

---

## Workflow Areas

| Folder | What lives here |
|--------|----------------|
| `workflows/analytics/` | Weekly Chartbeat briefing pipeline |
| `workflows/seo/` | Metadata packages for articles, podcasts, videos |
| `workflows/podcast/` | Megaphone → WordPress publishing |
| `workflows/cms/` | Content publishing, asset handling, WordPress patterns |
| `workflows/newsletter/` | Virginia Homegrown welcome flow, subscriber data collection |
| `workflows/archive/` | Brightspot SOPs — read-only reference, do not update |

---

## Operational Guidelines

1. **Think First** — Always read the relevant workflow file before invoking any tools. Understand the full sequence before acting.
2. **Self-Healing** — If a tool fails, investigate the error, fix the script, retest it, and update the corresponding workflow document to prevent recurrence.
3. **Separation of Concerns** — API keys and secrets live in `.env`. Never hardcode credentials in tools or workflows.
4. **Communicate Proactively** — If a workflow is ambiguous or you encounter unexpected state, stop and ask for clarification before proceeding.
5. **Brightspot is legacy** — Do not build new Brightspot tooling. If a task touches Brightspot, check whether a WordPress equivalent should be built instead.

---

## Known Failure Modes

- **EXIF-laden JPGs** will fail on upload in some CMS contexts — strip metadata before upload
- **Brightspot API** is finicky with asset types — always validate content type before POST
- **Chartbeat historical API** returns data in UTC — account for timezone when labeling weekly reports
- **Megaphone RSS** — confirm audio file specs (bitrate, format) before sharing feeds externally

---

## Project Structure

```
/
├── workflows/       # Markdown SOPs — read these before running anything
│   ├── analytics/
│   ├── seo/
│   ├── podcast/
│   ├── cms/
│   ├── newsletter/
│   └── archive/     # Brightspot reference — do not modify
├── tools/           # Python scripts — deterministic execution only
│   ├── chartbeat/
│   ├── wordpress/
│   ├── mailchimp/
│   └── megaphone/
├── temp/            # Temporary file storage during task execution
└── .env             # Secrets and environment config (never commit this)
```

---

## Environment Variables

See `.env.example` for all required keys. At minimum you need:

```
ANTHROPIC_API_KEY=
CHARTBEAT_API_KEY=
CHARTBEAT_HOST=vpm.org
GITHUB_TOKEN=
GITHUB_REPO=mhdesigns98/vpm-tools
MAILCHIMP_API_KEY=
MAILCHIMP_SERVER_PREFIX=
MEGAPHONE_API_KEY=
```

---

## Notes

- Enable **bypass permissions** in Claude Code settings for fully automated tasks.
- To initialize a new project: `Initialize this project based on the claude.md file`
- When in doubt about WordPress migration status, ask Mike before building new CMS tooling.
