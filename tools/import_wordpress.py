#!/usr/bin/env python3
"""Import a WordPress XML export into Jekyll posts with local media.

Usage:
  python tools/import_wordpress.py --xml wordpress.xml
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}


def sanitize_html(raw: str) -> str:
    cleaned = raw
    cleaned = re.sub(r"\sclass=(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\sstyle=(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\sdata-[\w-]+=(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\saria-[\w-]+=(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\sloading=(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"\sdecoding=(['\"]).*?\1", "", cleaned, flags=re.I | re.S)
    return cleaned.strip()


def download_media(url: str, images_dir: Path, downloaded: dict[str, str]) -> str:
    if url in downloaded:
        return downloaded[url]

    parsed = urllib.parse.urlparse(url)
    filename = Path(parsed.path).name
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", filename)
    target = images_dir / safe_name

    if not target.exists():
        with urllib.request.urlopen(url) as resp:  # nosec - migration script
            target.write_bytes(resp.read())

    local = f"/images/{safe_name}"
    downloaded[url] = local
    return local


def replace_media_paths(content: str, images_dir: Path, downloaded: dict[str, str]) -> str:
    pattern = re.compile(r"https?://[^\"'\s>]+/wp-content/uploads/[^\"'\s>]+", re.I)

    def repl(match: re.Match) -> str:
        url = html.unescape(match.group(0))
        try:
            return download_media(url, images_dir, downloaded)
        except Exception as exc:  # best effort migration
            print(f"warning: failed to download {url}: {exc}", file=sys.stderr)
            return url

    return pattern.sub(repl, content)


def jekyll_filename(date_str: str, slug: str) -> str:
    date = date_str.split(" ")[0]
    return f"{date}-{slug}.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", required=True, help="WordPress WXR XML export file")
    parser.add_argument("--posts-dir", default="_posts")
    parser.add_argument("--images-dir", default="images")
    args = parser.parse_args()

    posts_dir = Path(args.posts_dir)
    images_dir = Path(args.images_dir)
    posts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(args.xml)
    root = tree.getroot()

    downloaded: dict[str, str] = {}
    count = 0

    for item in root.findall("./channel/item"):
        post_type = item.findtext("wp:post_type", default="", namespaces=NS)
        status = item.findtext("wp:status", default="", namespaces=NS)
        if post_type != "post" or status != "publish":
            continue

        title = (item.findtext("title") or "Untitled").strip()
        slug = (item.findtext("wp:post_name", namespaces=NS) or "").strip()
        if not slug:
            link = item.findtext("link") or ""
            slug = Path(urllib.parse.urlparse(link).path.rstrip("/")).name or "untitled"

        date = (item.findtext("wp:post_date", namespaces=NS) or "1970-01-01 00:00:00").strip()
        link = (item.findtext("link") or "").strip()
        path = urllib.parse.urlparse(link).path or "/"
        if not path.endswith("/"):
            path += "/"

        tags = []
        for cat in item.findall("category"):
            domain = cat.attrib.get("domain", "")
            if domain == "post_tag" and cat.text:
                tags.append(cat.text.strip())

        body = item.findtext("content:encoded", default="", namespaces=NS)
        body = sanitize_html(body)
        body = replace_media_paths(body, images_dir, downloaded)

        safe_title = title.replace('"', '\\"')
        fm = [
            "---",
            f'title: "{safe_title}"',
            f"date: {date.replace(' ', 'T')}+00:00",
            f"slug: {slug}",
            f"permalink: {path}",
        ]
        if tags:
            fm.append("tags:")
            fm.extend([f"  - {t}" for t in tags])
        fm.append("---")

        output = "\n".join(fm) + "\n\n" + body + "\n"
        fname = posts_dir / jekyll_filename(date, slug)
        fname.write_text(output, encoding="utf-8")
        count += 1

    print(f"Imported {count} posts into {posts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
