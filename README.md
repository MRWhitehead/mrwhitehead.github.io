# Michael Whitehead site migration scaffold

This repository is now prepared to host a Jekyll-based blog migration from WordPress while preserving SEO-friendly URL structure.

## What is included

- Jekyll config with permalink pattern `/:year/:month/:day/:slug/`
- Minimal dark theme styling for posts and blog index
- `blog.html` page that lists all posts by date
- WordPress import script at `tools/import_wordpress.py` that:
  - reads a WordPress WXR XML export
  - imports published posts into `_posts/`
  - preserves canonical permalink paths
  - carries tags into front matter
  - strips common WordPress presentational attributes/classes
  - rewrites `wp-content/uploads` media links to local `/images/...`
  - downloads media files into `/images/`

## Run the migration

1. Export your WordPress site content as XML (WXR) from WordPress admin.
2. Place the export file in this repo (example: `wordpress.xml`).
3. Run:

```bash
python tools/import_wordpress.py --xml wordpress.xml
```

4. Commit generated `_posts/*.md` and downloaded `images/*`.
5. Build/deploy via GitHub Pages.

## Notes

- This environment could not directly fetch `michaelwhitehead.net` over HTTP(S), so the migration script is set up and validated with a sample XML, but real post import requires your XML export file.
