# Workflow: Weekly Analytics Briefing

## Objective
Pull the previous week's traffic data from Chartbeat, generate an AI-written summary via the Anthropic API, and post it as a GitHub Issue.

## Inputs
- Chartbeat API key (`CHARTBEAT_API_KEY`)
- Chartbeat host (`CHARTBEAT_HOST` = vpm.org)
- Anthropic API key (`ANTHROPIC_API_KEY`)
- GitHub token and repo (`GITHUB_TOKEN`, `GITHUB_REPO`)

## Tools
- `tools/chartbeat/insights.py` — pulls historical data, generates briefing, posts to GitHub Issues

## Steps
1. Run `insights.py`
2. Script determines the most recent completed week (Mon–Sun)
3. Pulls page-level traffic data from Chartbeat historical API
4. Sends data to Claude with a briefing prompt
5. Posts the result as a new GitHub Issue with label `analytics`

## Output
GitHub Issue titled: `Weekly traffic briefing — [week start date]`

## Edge Cases
- Chartbeat returns UTC — the script should label weeks in ET
- If the API returns no data, fail loudly rather than posting an empty briefing
- Duplicate issue check: if an issue for that week already exists, skip or append

## Schedule
Run via GitHub Actions every Monday morning (see `.github/workflows/weekly-insights.yml`)

## Last Updated
<!-- Update this line when you modify the workflow -->
