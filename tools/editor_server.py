#!/usr/bin/env python3
"""Local post editor for the blog.

Run:
    python3 tools/editor_server.py

It opens http://127.0.0.1:8800 in your browser: a form + Markdown editor with a
**live preview rendered by the real site renderer** (tools/build.py), so what you
see is exactly what gets published. Hitting *Save* writes
content/posts/<slug>.md, adds it to posts.json, and runs the build — then you
just commit & push.

Localhost-only, pure standard library.
"""
import json
import mimetypes
import os
import re
import sys
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # reuse the real renderer, front-matter parser and build pipeline

ROOT = build.ROOT
POSTS_DIR = build.POSTS_DIR
POSTS_JSON = os.path.join(POSTS_DIR, "posts.json")
HERE = os.path.dirname(os.path.abspath(__file__))
HOST, PORT = "127.0.0.1", 8800
SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def q(s):
    """Quote a scalar for the blog's simple front-matter parser."""
    s = " ".join(str(s).split()).replace('"', "'")
    return f'"{s}"'


def read_slugs():
    if os.path.exists(POSTS_JSON):
        return json.load(open(POSTS_JSON, encoding="utf-8"))
    return []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # keep the console quiet

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---- GET ----
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/editor", "/editor.html"):
            html = open(os.path.join(HERE, "editor.html"), "rb").read()
            return self._send(200, html, "text/html; charset=utf-8")
        if path == "/api/posts":
            return self._send(200, self._list_posts())
        if path.startswith("/api/post/"):
            return self._get_post(path[len("/api/post/"):])
        return self._serve_static(path)

    # ---- POST ----
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or "{}")
        except Exception:
            return self._send(400, {"error": "bad json"})
        if self.path == "/api/preview":
            return self._send(200, {"html": build.render_markdown(payload.get("markdown", ""))})
        if self.path == "/api/save":
            return self._save(payload)
        return self._send(404, {"error": "not found"})

    # ---- helpers ----
    def _serve_static(self, path):
        rel = path.lstrip("/")
        full = os.path.normpath(os.path.join(ROOT, rel))
        if os.path.isdir(full):
            full = os.path.join(full, "index.html")
        if not full.startswith(ROOT) or not os.path.isfile(full):
            return self._send(404, {"error": "not found"})
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype)

    def _list_posts(self):
        out = []
        for s in read_slugs():
            p = os.path.join(POSTS_DIR, f"{s}.md")
            meta = {"slug": s, "title": s, "draft": False, "date": ""}
            if os.path.exists(p):
                data, _ = build.parse_frontmatter(open(p, encoding="utf-8").read())
                meta.update(title=data.get("title", s), draft=bool(data.get("draft")),
                            date=data.get("date", ""))
            out.append(meta)
        return out

    def _get_post(self, slug):
        if not SAFE_SLUG.match(slug or ""):
            return self._send(400, {"error": "bad slug"})
        p = os.path.join(POSTS_DIR, f"{slug}.md")
        if not os.path.exists(p):
            return self._send(404, {"error": "not found"})
        data, content = build.parse_frontmatter(open(p, encoding="utf-8").read())
        return self._send(200, {"slug": slug, "data": data, "content": content})

    def _save(self, p):
        slug = (p.get("slug") or "").strip()
        if not SAFE_SLUG.match(slug):
            return self._send(400, {"error": "slug must be lowercase words joined by hyphens (e.g. htb-cicada)"})
        title = (p.get("title") or slug).strip()
        when = (str(p.get("date") or "") or date.today().isoformat())[:10]
        raw_tags = p.get("tags") or []
        tags = [str(t).strip().lstrip("#") for t in raw_tags if str(t).strip()]
        pinned = bool(p.get("pinned"))
        draft = bool(p.get("draft"))
        excerpt = (p.get("excerpt") or "").strip()
        body = (p.get("body") or "").rstrip() + "\n"

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
        out_path = os.path.join(POSTS_DIR, f"{slug}.md")
        existed = os.path.exists(out_path)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(fm + body)

        slugs = read_slugs()
        if slug not in slugs:
            slugs.append(slug)
            with open(POSTS_JSON, "w", encoding="utf-8") as f:
                json.dump(slugs, f, indent=2)
                f.write("\n")

        try:
            build.main()  # regenerate pages, sitemap, feed, posts-index, cache-bust
        except Exception as e:  # noqa: BLE001 - surface build errors to the editor
            return self._send(500, {"error": f"saved the file, but the build failed: {e}"})

        return self._send(200, {
            "ok": True,
            "updated": existed,
            "slug": slug,
            "url": f"/post/{slug}/",
            "file": f"content/posts/{slug}.md",
        })


def main():
    mimetypes.add_type("application/javascript", ".js")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"post editor running at {url}")
    print("write a post, hit Save (writes the .md + runs the build), then commit & push.")
    print("Ctrl-C to stop.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye!")
        server.shutdown()


if __name__ == "__main__":
    main()
