# Workflow: Podcast Episode Publishing

## Objective
Publish a new podcast episode from Megaphone to the VPM website CMS, including metadata, audio embed, and SEO package.

## Inputs
- Megaphone episode URL or ID
- Show name (e.g. RVA's Got Issues, VPM Daily Newscast)
- Episode title, description, publish date
- Audio file (if uploading directly)

## Tools
- `tools/megaphone/` — RSS feed parsing, episode metadata extraction (TODO)
- `tools/wordpress/` — Episode post creation via WP REST API (TODO)

## Steps
1. Pull episode metadata from Megaphone RSS feed
2. Confirm audio file specs (MP3, 128kbps minimum)
3. Generate SEO package (see `workflows/seo/seo-package.md`)
4. Create Podcast Episode post in CMS with:
   - Title, description, publish date
   - Megaphone embed or direct audio URL
   - Tags, categories, show association
5. Verify post preview before publishing

## Output
- Published episode post on vpm.org
- SEO fields populated

## Known Issues
- VPM Daily Newscast: verify uploaded file matches newscast audio before sharing RSS feed with NPR
- EXIF metadata on any associated images must be stripped before CMS upload

## WordPress Migration Note
- Brightspot had a `Podcast Episode` content type with specific fields
- WordPress equivalent TBD — confirm content type structure before building publish automation

## Shows
| Show | Host | Notes |
|------|------|-------|
| RVA's Got Issues | Rich Meagher | Richmond/Virginia politics; General Assembly Required series |
| VPM Daily Newscast | — | NPR RSS pilot — file specs matter |

## Last Updated
<!-- Update this line when you modify the workflow -->
