# Workflow: Content Publishing (WordPress)

## Objective
Publish or update content on vpm.org via the WordPress REST API.

## Status
⚠️ STUB — WordPress migration in progress. Fill this in once WP is live.

## Inputs
- Content type: article | video | page | podcast episode
- Title, body, publish date
- Featured image (EXIF-stripped JPG or WebP)
- SEO metadata (see `workflows/seo/seo-package.md`)
- Author, categories, tags

## Tools
- `tools/wordpress/` — WP REST API wrapper (TODO)

## Steps
1. Prepare content and assets
2. Strip EXIF from all images before upload
3. POST to WP REST API endpoint
4. Confirm post ID and URL returned
5. Verify live URL before closing task

## Environment Variables Needed
```
WORDPRESS_API_URL=https://vpm.org/wp-json/wp/v2
WORDPRESS_USERNAME=
WORDPRESS_APP_PASSWORD=
```

## Notes
- Use Application Passwords (not your login password) for API auth
- Images: WebP preferred, JPG acceptable at 80% quality, max 1920px
- Never use `file://` paths — always upload via API or media library

## Last Updated
<!-- Update this line when you modify the workflow -->
