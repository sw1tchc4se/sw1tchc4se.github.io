#!/usr/bin/env python3
"""Pre-render posts to static HTML for SEO + social sharing.

Run from the project root after adding/editing/removing posts:

    python3 tools/build.py

For every published (non-draft) post in content/posts/posts.json it writes a
fully static page at  post/<slug>/index.html  with the title, description,
Open Graph / Twitter tags, article metadata, JSON-LD and the rendered post
body all baked into the HTML. That means search crawlers and social
link-preview bots (which often don't run JavaScript) see the real content,
not an empty shell. Real visitors still get the interactive version: the
existing JS re-renders the article on top (table of contents, reactions, …).

It also regenerates sitemap.xml (clean post URLs) and feed.xml (RSS 2.0),
so this script supersedes tools/gen-sitemap.py.

Pure standard library, no dependencies — same as the rest of tools/.
"""
import hashlib
import html
import json
import os
import re
import shutil
from datetime import date, datetime, timezone
from email.utils import format_datetime

BASE = "https://sw1tchc4se.github.io/"
SITE_NAME = "sw1tchc4se"
SITE_DESC = "notes on security, tooling, and the occasional rabbit hole"
DEFAULT_IMAGE = BASE + "assets/avatar.png"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "posts")
POST_OUT = os.path.join(ROOT, "post")
TODAY = date.today().isoformat()
MARKER = "<!-- prerendered by tools/build.py -->"

# Local assets that need cache-busting when their contents change. ASSET_VER is
# a short hash of these files, set in main() and appended as ?v=… to every CSS/JS
# link so browsers always re-fetch after a change instead of serving a stale copy.
ASSET_FILES = ["css/style.css", "js/blog.js", "js/home.js", "js/posts.js", "js/post.js"]
ASSET_VER = "0"
# matches local css/js links in any page, with or without an existing ?v=…
ASSET_LINK_RE = re.compile(
    r'((?:href|src)="[^"]*?(?:css/style\.css|js/blog\.js|js/home\.js|js/posts\.js|js/post\.js))(\?v=[0-9a-f]+)?(")'
)


def asset_version():
    h = hashlib.sha1()
    for rel in ASSET_FILES:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:8]


def stamp_static_pages(version):
    """Rewrite ?v=… on the hand-written HTML pages (build.py regenerates the
    post pages itself, so they get the version baked straight into the template)."""
    pages = ["index.html", "404.html", "posts/index.html", "about/index.html", "post/index.html"]
    for rel in pages:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8").read()
        new = ASSET_LINK_RE.sub(rf"\1?v={version}\3", txt)
        if new != txt:
            open(path, "w", encoding="utf-8").write(new)
            print(f"  ~ stamped {rel}")


# --------------------------------------------------------------------------
# frontmatter (mirrors parseFrontmatter in js/blog.js)
# --------------------------------------------------------------------------
def parse_frontmatter(raw):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.DOTALL)
    if not m:
        return {}, raw
    data = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r"^(\w+)\s*:\s*(.*)$", line)
        if not mm:
            continue
        key, val = mm.group(1), mm.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            data[key] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
        elif val in ("true", "false"):
            data[key] = val == "true"
        else:
            data[key] = val.strip("\"'")
    return data, m.group(2)


# --------------------------------------------------------------------------
# tiny markdown -> HTML renderer (covers the documented post features)
# --------------------------------------------------------------------------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    text = esc(text)
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                  r'<img src="\2" alt="\1" loading="lazy" decoding="async">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)
    return text


def slugify(text):
    return re.sub(r"^-|-$", "", re.sub(r"[^\w]+", "-", re.sub(r"[*`~]", "", text).lower()))


LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
HR_RE = re.compile(r"^\s*([-*_])\s*(\1\s*){2,}$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def is_block_start(line):
    s = line.strip()
    return (s == "" or s.startswith("```") or HEAD_RE.match(line) or s.startswith(">")
            or LIST_RE.match(line) or HR_RE.match(line))


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def build_list(entries):
    out = []
    i, N = 0, len(entries)
    if N == 0:
        return ""
    tag = "ol" if entries[0][1] else "ul"
    out.append(f"<{tag}>")
    while i < N:
        indent, _ordered, text = entries[i]
        j = i + 1
        children = []
        while j < N and entries[j][0] > indent:
            children.append(entries[j])
            j += 1
        item = inline(text)
        if children:
            item += build_list(children)
        out.append(f"<li>{item}</li>")
        i = j
    out.append(f"</{tag}>")
    return "".join(out)


def render_markdown(md):
    lines = md.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]

        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{esc(chr(10).join(buf))}</code></pre>")
            continue

        if line.strip() == "":
            i += 1
            continue

        if HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        m = HEAD_RE.match(line)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            out.append(f'<h{lvl} id="{slugify(txt)}">{inline(txt)}</h{lvl}>')
            i += 1
            continue

        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{render_markdown(chr(10).join(buf))}</blockquote>")
            continue

        if "|" in line and i + 1 < n and "-" in lines[i + 1] and \
                re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            header = split_row(line)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in header)
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>")
            continue

        if LIST_RE.match(line):
            entries = []
            while i < n and LIST_RE.match(lines[i]):
                mm = LIST_RE.match(lines[i])
                entries.append((len(mm.group(1)), mm.group(2)[0].isdigit(), mm.group(3)))
                i += 1
            out.append(build_list(entries))
            continue

        buf = []
        while i < n and lines[i].strip() != "" and not is_block_start(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def format_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %-d, %Y")
    except ValueError:
        return iso


def reading_minutes(md):
    return max(1, round(len(md.split()) / 200))


def og_image(data):
    img = data.get("image")
    if not img:
        return DEFAULT_IMAGE
    return img if img.startswith("http") else BASE + img.lstrip("/")


def related(post, posts):
    scored = []
    for p in posts:
        if p["slug"] == post["slug"]:
            continue
        shared = len(set(p["tags"]) & set(post["tags"]))
        if shared:
            scored.append((shared, p["date"], p))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [p for _, _, p in scored[:3]]


# --------------------------------------------------------------------------
# page template
# --------------------------------------------------------------------------
def render_page(post, posts):
    slug = post["slug"]
    title = post["title"]
    excerpt = post["excerpt"] or title
    url = f"{BASE}post/{slug}/"
    full_title = f"{title} · {SITE_NAME}"
    image = og_image(post["data"])
    body_html = render_markdown(post["content"])

    tag_links = "".join(
        f'<a class="tag" href="../../posts/?tag={html.escape(t)}">{html.escape(t)}</a>'
        for t in post["tags"]
    )
    article_tags = "\n".join(
        f'  <meta property="article:tag" content="{html.escape(t)}" />' for t in post["tags"]
    )

    rel = related(post, posts)
    related_html = ""
    if rel:
        cards = "".join(
            f'<a class="card" href="../{p["slug"]}/">'
            f'<h3>{html.escape(p["title"])}</h3>'
            f'<div class="meta"><span><span data-icon="calendar"></span> {format_date(p["date"])}</span></div>'
            f'<p>{html.escape(p["excerpt"])}</p>'
            f'<div class="tags">{"".join(f"<span class=\"tag\">{html.escape(t)}</span>" for t in p["tags"])}</div>'
            "</a>"
            for p in rel
        )
        related_html = (
            '\n      <div class="divider"><span data-icon="petal"></span></div>'
            '\n      <section id="related-section">'
            '<h2 class="section-title"><span data-icon="sprout"></span> related reads</h2>'
            f'<div class="cards" id="related">{cards}</div></section>'
        )

    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": excerpt,
        "datePublished": post["date"],
        "dateModified": post["date"],
        "url": url,
        "mainEntityOfPage": url,
        "image": image,
        "keywords": ", ".join(post["tags"]),
        "author": {"@type": "Person", "name": SITE_NAME, "url": BASE + "about/"},
        "publisher": {"@type": "Person", "name": SITE_NAME},
    }
    ld_json = json.dumps(ld, ensure_ascii=False)

    e_title = html.escape(full_title)
    e_excerpt = html.escape(excerpt)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  {MARKER}
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e_title}</title>
  <meta name="description" content="{e_excerpt}" />
  <meta name="author" content="{SITE_NAME}" />
  <meta name="theme-color" content="#FCF3F6" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#241D29" media="(prefers-color-scheme: dark)" />
  <link rel="icon" href="/assets/avatar.svg" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="/assets/avatar.png" />
  <link rel="canonical" href="{url}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{SITE_NAME}" />
  <meta property="og:title" content="{e_title}" />
  <meta property="og:description" content="{e_excerpt}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{image}" />
  <meta property="article:published_time" content="{post['date']}" />
{article_tags}
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e_title}" />
  <meta name="twitter:description" content="{e_excerpt}" />
  <meta name="twitter:image" content="{image}" />
  <script type="application/ld+json">{ld_json}</script>
  <link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="../../feed.xml" />
  <script>
    (function () {{
      var s = localStorage.getItem("theme") ||
        (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      document.documentElement.setAttribute("data-theme", s);
    }})();
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Nunito:wght@400;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../css/style.css?v={ASSET_VER}" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css" />
  <script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
</head>
<body>
  <main class="container">
    <div id="article">
      <header class="post-header">
        <a class="back-link" href="../../posts/">← all posts</a>
        <h1>{html.escape(title)}</h1>
        <div class="post-meta">
          <span><span data-icon="calendar"></span> {format_date(post['date'])}</span>
          <span class="coffee"><span data-icon="coffee"></span> {reading_minutes(post['content'])} min</span>
        </div>
        <div class="tags">{tag_links}</div>
      </header>

      <div class="divider"><span data-icon="petal"></span></div>

      <div class="post-layout">
        <article class="prose" id="prose">{body_html}</article>
        <aside class="toc" id="toc" style="display:none">
          <h4><span data-icon="archive"></span> contents</h4>
          <ul id="toc-list"></ul>
        </aside>
      </div>

      <div id="reactions-mount"></div>{related_html}
    </div>
  </main>

  <script>
    window.__POST_SLUG__ = {json.dumps(slug)};
    window.__PRERENDERED__ = true;
  </script>
  <script defer src="../../js/blog.js?v={ASSET_VER}"></script>
  <script defer src="../../js/post.js?v={ASSET_VER}"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# sitemap + feed
# --------------------------------------------------------------------------
def url_entry(loc, lastmod):
    return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>"


def write_sitemap(posts):
    entries = [url_entry(BASE, TODAY), url_entry(BASE + "posts/", TODAY), url_entry(BASE + "about/", TODAY)]
    for p in posts:
        entries.append(url_entry(f"{BASE}post/{p['slug']}/", p["date"]))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(entries) + "\n</urlset>\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(xml)


def rfc822(iso):
    """RSS 2.0 requires RFC-822 dates, not bare ISO dates."""
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return format_datetime(dt)
    except ValueError:
        return iso


def write_feed(posts):
    items = []
    for p in sorted(posts, key=lambda x: x["date"], reverse=True):
        link = f"{BASE}post/{p['slug']}/"
        items.append(
            "    <item>\n"
            f"      <title>{html.escape(p['title'])}</title>\n"
            f"      <link>{link}</link>\n"
            f'      <guid isPermaLink="true">{link}</guid>\n'
            f"      <pubDate>{rfc822(p['date'])}</pubDate>\n"
            f"      <description>{html.escape(p['excerpt'])}</description>\n"
            "    </item>")
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0">\n  <channel>\n'
            f"    <title>{SITE_NAME}</title>\n    <link>{BASE}</link>\n"
            f"    <description>{SITE_DESC}</description>\n"
            + ("\n".join(items) + "\n" if items else "")
            + "  </channel>\n</rss>\n")
    open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8").write(feed)


# --------------------------------------------------------------------------
def load_posts():
    slugs = json.load(open(os.path.join(POSTS_DIR, "posts.json"), encoding="utf-8"))
    posts = []
    for slug in slugs:
        path = os.path.join(POSTS_DIR, f"{slug}.md")
        if not os.path.exists(path):
            print(f"  ! skipping {slug}: {slug}.md not found")
            continue
        data, content = parse_frontmatter(open(path, encoding="utf-8").read())
        if data.get("draft"):
            continue
        posts.append({
            "slug": slug,
            "title": data.get("title", slug),
            "date": data.get("date", TODAY),
            "tags": data.get("tags", []),
            "pinned": bool(data.get("pinned")),
            "excerpt": data.get("excerpt", ""),
            "content": content,
            "data": data,
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def write_posts_index(posts):
    """A single metadata file so the home/posts pages make one request
    instead of fetching every .md to read its front-matter."""
    index = [
        {
            "slug": p["slug"],
            "title": p["title"],
            "date": p["date"],
            "tags": p["tags"],
            "pinned": p["pinned"],
            "excerpt": p["excerpt"],
        }
        for p in posts
    ]
    path = os.path.join(POSTS_DIR, "posts-index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def clean_stale(slugs):
    """Remove previously generated post dirs that are no longer published."""
    if not os.path.isdir(POST_OUT):
        return
    for name in os.listdir(POST_OUT):
        d = os.path.join(POST_OUT, name)
        idx = os.path.join(d, "index.html")
        if not os.path.isdir(d) or not os.path.exists(idx) or name in slugs:
            continue
        if MARKER in open(idx, encoding="utf-8").read():
            shutil.rmtree(d)
            print(f"  - removed stale post/{name}/")


def main():
    global ASSET_VER
    ASSET_VER = asset_version()
    posts = load_posts()
    slugs = {p["slug"] for p in posts}
    clean_stale(slugs)
    stamp_static_pages(ASSET_VER)
    for p in posts:
        out_dir = os.path.join(POST_OUT, p["slug"])
        os.makedirs(out_dir, exist_ok=True)
        open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(render_page(p, posts))
        print(f"  + post/{p['slug']}/index.html")
    write_sitemap(posts)
    write_feed(posts)
    write_posts_index(posts)
    print(f"done: {len(posts)} post page(s) + sitemap.xml + feed.xml + posts-index.json")


if __name__ == "__main__":
    main()
