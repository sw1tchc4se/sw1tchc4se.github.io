#!/usr/bin/env python3
"""Import an Obsidian note as a blog post.

Usage:
    python3 tools/import.py path/to/Note.md [--slug my-post] [--vault DIR]
                                            [--draft] [--force]

What it does:
  * normalises the front-matter to the fields this blog uses
    (title, date, tags, pinned, draft, excerpt) — including converting
    Obsidian's multi-line `tags:` list to the inline form the parser needs,
    and filling in title/date/excerpt when they're missing;
  * rewrites Obsidian image embeds  ![[pic.png]]  ->  ![alt](../assets/pic.png)
    and copies the image files into  assets/  (searched for under the note's
    folder and any --vault you pass);
  * turns wikilinks  [[Note]] / [[Note|alias]]  into plain text (there's no
    target page to link to);
  * strips Obsidian callout markers  > [!note] Title  down to a normal
    blockquote with a bold title;
  * writes  content/posts/<slug>.md  and adds "<slug>" to posts.json.

Afterwards run  python3 tools/build.py  to publish. Pure standard library.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "posts")
POSTS_JSON = os.path.join(POSTS_DIR, "posts.json")
ASSETS_DIR = os.path.join(ROOT, "assets")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp"}

WARNINGS = []
COPIED = []


def warn(msg):
    WARNINGS.append(msg)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def strip_md(t):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)        # images
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)    # links -> text
    t = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), t)
    t = re.sub(r"[*_`~]", "", t)                      # emphasis / code marks
    return t.strip()


def truncate(t, n=180):
    t = " ".join(t.split())
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def q(s):
    """Quote a scalar for the blog's simple front-matter parser."""
    s = " ".join(str(s).split()).replace('"', "'")
    return f'"{s}"'


# --------------------------------------------------------------------------
# front-matter (tiny YAML subset: scalars, inline [..] lists, block - lists)
# --------------------------------------------------------------------------
def split_frontmatter(raw):
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.DOTALL)
    if not m:
        return {}, raw.lstrip("﻿")
    return parse_yaml_block(m.group(1)), m.group(2)


def parse_yaml_block(block):
    data = {}
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([\w-]+)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        if val == "":
            items, j = [], i + 1
            while j < len(lines) and re.match(r"^\s*-\s+", lines[j]):
                items.append(re.sub(r"^\s*-\s+", "", lines[j]).strip().strip("\"'"))
                j += 1
            data[key] = items if items else ""
            i = j if items else i + 1
            continue
        if val.startswith("[") and val.endswith("]"):
            data[key] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
        elif val.lower() in ("true", "false"):
            data[key] = val.lower() == "true"
        else:
            data[key] = val.strip("\"'")
        i += 1
    return data


def first_heading(body):
    m = re.search(r"^#{1,2}\s+(.*)$", body, re.MULTILINE)
    return strip_md(m.group(1)) if m else ""


def first_paragraph(body):
    skip = ("#", ">", "-", "*", "+", "|", "!", "`")
    buf = []
    for line in body.split("\n"):
        s = line.strip()
        if not s:
            if buf:
                break
            continue
        if s.startswith(skip) or re.match(r"^\d+\.\s", s) or re.match(r"^\s*<", s):
            if buf:
                break
            continue
        buf.append(s)
    return truncate(strip_md(" ".join(buf))) if buf else ""


# --------------------------------------------------------------------------
# images
# --------------------------------------------------------------------------
def safe_asset_name(name):
    base, ext = os.path.splitext(os.path.basename(name))
    return (slugify(base) or "image") + ext.lower()


def find_image(name, search_dirs):
    for d in search_dirs:
        if not d or not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            if name in files:
                return os.path.join(root, name)
    return None


def copy_image(raw_target, search_dirs):
    """Copy an image into assets/ and return its new ../assets/<name> path."""
    base = os.path.basename(raw_target.replace("%20", " ").split("#")[0]).strip()
    asset = safe_asset_name(base)
    src = find_image(base, search_dirs)
    if src:
        os.makedirs(ASSETS_DIR, exist_ok=True)
        shutil.copy2(src, os.path.join(ASSETS_DIR, asset))
        COPIED.append(asset)
    else:
        warn(f"image not found: '{base}' — put the file at assets/{asset} manually")
    return f"../assets/{asset}", os.path.splitext(base)[0]


def convert_body(body, search_dirs):
    # 1) Obsidian embeds: ![[file.ext|opts]]
    def embed(m):
        target = m.group(1).split("|")[0].strip()
        ext = os.path.splitext(target)[1].lower()
        if ext in IMAGE_EXTS:
            path, alt = copy_image(target, search_dirs)
            return f"![{alt}]({path})"
        warn(f"transclusion ![[{m.group(1)}]] can't be embedded — left as plain text")
        return os.path.basename(target.split("|")[0])

    body = re.sub(r"!\[\[([^\]]+)\]\]", embed, body)

    # 2) local markdown images ![alt](relative/path) -> copy into assets/
    def md_img(m):
        alt, path = m.group(1), m.group(2).strip()
        if path.startswith(("http://", "https://", "../assets/", "/assets/", "data:")):
            return m.group(0)
        new_path, fallback_alt = copy_image(path, search_dirs)
        return f"![{alt or fallback_alt}]({new_path})"

    body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", md_img, body)

    # 3) wikilinks [[Note]] / [[Note|alias]] / [[Note#sec]] -> text
    def wiki(m):
        inner = m.group(1)
        if "|" in inner:
            return inner.split("|", 1)[1].strip()
        return inner.split("#", 1)[0].strip()

    if re.search(r"(?<!\!)\[\[[^\]]+\]\]", body):
        warn("wikilinks [[...]] were converted to plain text (no page to link to)")
    body = re.sub(r"(?<!\!)\[\[([^\]]+)\]\]", wiki, body)

    # 4) Obsidian callouts: > [!type]+- Title  -> > **Title**
    out = []
    for line in body.split("\n"):
        cm = re.match(r"^(\s*>+)\s*\[!(\w+)\][+-]?\s*(.*)$", line)
        if cm:
            label = cm.group(3).strip() or cm.group(2).capitalize()
            out.append(f"{cm.group(1)} **{label}**")
        else:
            out.append(line)
    return "\n".join(out).strip() + "\n"


# --------------------------------------------------------------------------
# posts.json
# --------------------------------------------------------------------------
def add_to_posts_json(slug):
    slugs = []
    if os.path.exists(POSTS_JSON):
        slugs = json.load(open(POSTS_JSON, encoding="utf-8"))
    if slug in slugs:
        return False
    slugs.append(slug)
    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(slugs, f, indent=2)
        f.write("\n")
    return True


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Import an Obsidian note as a blog post.")
    ap.add_argument("note", help="path to the Obsidian .md note")
    ap.add_argument("--slug", help="output slug (default: from title/filename)")
    ap.add_argument("--vault", help="extra folder to search for embedded images")
    ap.add_argument("--draft", action="store_true", help="import as a draft (hidden)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing post")
    args = ap.parse_args()

    if not os.path.isfile(args.note):
        sys.exit(f"error: no such file: {args.note}")

    raw = open(args.note, encoding="utf-8").read()
    data, body = split_frontmatter(raw)

    title = data.get("title") or first_heading(body) or \
        os.path.splitext(os.path.basename(args.note))[0]
    slug = args.slug or slugify(title)
    if not slug:
        sys.exit("error: could not derive a slug; pass --slug")

    out_path = os.path.join(POSTS_DIR, f"{slug}.md")
    if os.path.exists(out_path) and not args.force:
        sys.exit(f"error: {out_path} already exists (use --force to overwrite)")

    search_dirs = [os.path.dirname(os.path.abspath(args.note)), args.vault]
    body = convert_body(body, search_dirs)

    when = str(data.get("date") or data.get("created") or date.today().isoformat())[:10]
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip().lstrip("#") for t in re.split(r"[,\s]+", tags) if t.strip()]
    else:
        tags = [str(t).lstrip("#") for t in tags]
    pinned = bool(data.get("pinned", False))
    draft = True if args.draft else bool(data.get("draft", False))
    excerpt = data.get("excerpt") or data.get("description") or first_paragraph(body)

    fm = (
        "---\n"
        f"title: {q(title)}\n"
        f"date: {q(when)}\n"
        f"tags: [{', '.join(q(t) for t in tags)}]\n"
        f"pinned: {str(pinned).lower()}\n"
        f"draft: {str(draft).lower()}\n"
        f"excerpt: {q(excerpt)}\n"
        "---\n\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(fm + body)

    added = add_to_posts_json(slug)

    # ---- summary ----
    print(f"✓ wrote content/posts/{slug}.md")
    print(f"  title:   {title}")
    print(f"  date:    {when}")
    print(f"  tags:    {tags or '(none)'}")
    print(f"  draft:   {draft}")
    print(f"  posts.json: {'added' if added else 'already listed'}")
    if COPIED:
        print(f"  images copied to assets/: {', '.join(COPIED)}")
    if WARNINGS:
        print("\n  ⚠ check these:")
        for w in WARNINGS:
            print(f"    - {w}")
    if not excerpt:
        print("    - excerpt is empty; add one to the front-matter for nicer cards/SEO")
    print("\nnext: python3 tools/build.py   (then commit & push)")


if __name__ == "__main__":
    main()
