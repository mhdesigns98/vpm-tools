# tools/wordpress

## Status
⚠️ TODO — WordPress migration in progress. Build these out once WP is live.

## Planned Scripts

### publish.py
Create or update posts via the WordPress REST API.

### upload_media.py
Upload images to the WordPress media library with EXIF stripping.

### get_post.py
Fetch post data by ID or slug for verification.

## Auth
WordPress REST API uses Application Passwords — not your login password.
Generate one at: WordPress Admin → Users → Profile → Application Passwords

**Requires in .env:**
```
WORDPRESS_API_URL=https://vpm.org/wp-json/wp/v2
WORDPRESS_USERNAME=
WORDPRESS_APP_PASSWORD=
```

## Notes
- See `workflows/cms/content-publishing.md` for the full SOP
- Always strip EXIF from images before upload
- WebP preferred; JPG at 80% quality acceptable
