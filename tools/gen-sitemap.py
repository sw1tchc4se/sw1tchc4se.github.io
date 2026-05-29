#!/usr/bin/env python3
"""Regenerate sitemap.xml from the post manifest.

Run from the project root after adding or removing posts:

    python3 tools/gen-sitemap.py

It lists the static pages plus one URL per published (non-draft) post,
so Google can discover each post individually.
"""
import json
import os
import re
from datetime import date

BASE = "https://sw1tchc4se.github.io/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "posts")
TODAY = date.today().isoformat()


def frontmatter(slug):
    """Return (date, is_draft) for a post slug, with safe defaults."""
    path = os.path.join(POSTS_DIR, f"{slug}.md")
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        return TODAY, False
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    block = m.group(1) if m else ""
    d = re.search(r'(?m)^date:\s*"?([0-9-]+)"?', block)
    draft = re.search(r"(?m)^draft:\s*true\b", block)
    return (d.group(1) if d else TODAY), bool(draft)


def url_entry(loc, lastmod):
    return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>"


def main():
    entries = [
        url_entry(BASE, TODAY),
        url_entry(BASE + "posts/", TODAY),
        url_entry(BASE + "about/", TODAY),
    ]

    manifest_path = os.path.join(POSTS_DIR, "posts.json")
    slugs = json.load(open(manifest_path, encoding="utf-8"))
    published = 0
    for slug in slugs:
        post_date, is_draft = frontmatter(slug)
        if is_draft:
            continue
        entries.append(url_entry(f"{BASE}post/?post={slug}", post_date))
        published += 1

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    print(f"sitemap.xml written: 3 static pages + {published} post(s)")


if __name__ == "__main__":
    main()
