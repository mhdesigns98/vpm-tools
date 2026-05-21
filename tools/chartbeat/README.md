# tools/chartbeat

## What's here
Scripts for pulling analytics data from the Chartbeat API and generating insights.

## Scripts

### insights.py
Pulls the previous week's historical traffic data from Chartbeat, sends it to the Claude API for an AI-generated briefing, and posts the result as a GitHub Issue.

**To run manually:**
```bash
cd tools/chartbeat
python insights.py
```

**Requires in .env:**
```
CHARTBEAT_API_KEY=
CHARTBEAT_HOST=vpm.org
ANTHROPIC_API_KEY=
GITHUB_TOKEN=
GITHUB_REPO=
```

**Automated via:** `.github/workflows/weekly-insights.yml` (runs every Monday)

## Notes
- See `workflows/analytics/weekly-briefing.md` for the full SOP
- Chartbeat returns UTC — briefing labels weeks in ET
