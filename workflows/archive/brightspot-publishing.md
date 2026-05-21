# Workflow: Brightspot Content Publishing [ARCHIVED]

## Status
⛔ ARCHIVED — Brightspot is being retired. Do not update this workflow.
This file is reference-only for historical context and WordPress migration planning.

## What Brightspot Was Used For
- Article, video, and podcast episode publishing
- SEO metadata (meta title, description) via built-in SEO module
- OG/social metadata
- Asset management (images, audio)
- Podcast Episode content type (custom fields: show, audio URL, transcript)
- Art & Culture ListThreePromo module (CSS customized)

## Known Brightspot Quirks (for WP migration reference)
- EXIF-laden JPGs caused silent upload failures — always strip before upload
- API was finicky with content types — required exact field matching
- SEO module had separate fields for meta vs OG — don't assume WordPress plugins handle this the same way
- Podcast Episode content type had show association, audio embed, and transcript fields

## Migration Checklist
- [ ] Map Brightspot content types → WordPress equivalents
- [ ] Confirm SEO plugin (Yoast or RankMath) field structure
- [ ] Validate Podcast Episode fields in WordPress
- [ ] Test image upload pipeline with EXIF stripping
- [ ] Archive or redirect legacy Brightspot URLs

## Last Updated
<!-- Archived — do not update -->
