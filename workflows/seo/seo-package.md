# Workflow: SEO Metadata Package

## Objective
Generate SEO-optimized meta titles, meta descriptions, and Open Graph tags for VPM content — articles, podcast episodes, and videos.

## Inputs
- Content type: `article` | `podcast` | `video`
- Headline / title
- Body text or summary
- Primary keyword (optional — infer from content if not provided)
- URL slug (optional)

## Tools
- Claude API (via prompt) — no standalone script yet, currently done manually in claude.ai

## Steps
1. Identify content type
2. Extract or confirm primary keyword
3. Generate meta title (50–60 chars, keyword near front)
4. Generate meta description (150–160 chars, includes CTA or hook)
5. Generate OG title and OG description (can differ slightly from meta)
6. Review for VPM voice — not clickbait, factual, public media tone

## Output
```
Meta Title: 
Meta Description: 
OG Title: 
OG Description: 
```

## Notes
- "Virginia's home for public media" — not "Virginia Public Media"
- Podcast episodes: include show name in meta title when space allows
- RVA's Got Issues: tag Richmond/Virginia politics angle when relevant
- Video: lean on the visual hook in the description

## WordPress Migration Note
- In Brightspot: meta fields were set manually in the SEO module
- In WordPress: confirm which SEO plugin (Yoast? RankMath?) before building automation

## Last Updated
<!-- Update this line when you modify the workflow -->
