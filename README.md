# sw1tchc4se.github.io

my blog where i blog → https://sw1tchc4se.github.io/

## writing a post

Three ways, pick whatever's comfy:

**Visual editor (easiest)** — a localhost editor with a live preview rendered
by the real site renderer, so what you see is what gets published. Save writes
the `.md`, updates `posts.json`, and runs the build for you:

```bash
python3 tools/editor_server.py     # opens http://127.0.0.1:8800
# write → Save & build → then:
git add -A && git commit -m "new post" && git push
```

It can also load & edit existing posts, mark drafts, and download/copy the raw
`.md`.

**From Obsidian** — run the importer; it normalises the front-matter, copies
embedded images into `assets/`, converts `[[wikilinks]]` to text, strips
`> [!callout]` markers, and adds the post to `posts.json`:

```bash
python3 tools/import.py "path/to/Note.md" --vault path/to/vault
python3 tools/build.py          # pre-render + sitemap/feed + cache-bust
git add -A && git commit -m "new post" && git push
```

Use `--draft` to import hidden, `--slug my-post` to set the URL.

**By hand** — copy `content/posts/_TEMPLATE.md` to
`content/posts/<slug>.md`, edit the front-matter (`draft: false`), add
`"<slug>"` to `content/posts/posts.json`, then run `tools/build.py` and push.

Always run `tools/build.py` before committing — it regenerates the static
post pages and bumps the asset cache-busting hash.
