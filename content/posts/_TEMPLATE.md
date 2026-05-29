---
title: "Post Title Goes Here"
date: "2026-05-29"
tags: ["writeup", "htb"]
pinned: false
draft: true
excerpt: "One or two sentences shown on the post card and in search results."
---

This is regular paragraph text, just type normally. To start a **new paragraph**,
leave one blank line between blocks of text. Single line breaks are ignored, so
write as long or short lines as you like.

## This is a title, write it as `## Title`

Two hashes + a space makes a title (section heading). Every title automatically
shows up in the "contents" box on the side of the post.

### This is a subtitle, write it as `### Subtitle`

Three hashes makes a subtitle. These also appear in the contents box, indented
under the title above them.

## Text styles

- Bold text, write `**bold**` → **bold**
- Italic text, write `*italic*` → *italic*
- Bold + italic, write `***both***` → ***both***
- Inline code, wrap a word in backticks → `nmap`
- A link, write `[text](https://example.com)` → [text](https://example.com)
- Strikethrough, write `~~oops~~` → ~~oops~~

## Thoughts & comments

Start a line with `>` to make a blockquote. It renders in a soft, muted box with a
green bar down the side, perfect for an aside, a quote, or a "note to self":

> This is a thought. Use it whenever you want to step out of the main text and
> add a comment, a warning, or a quote from somewhere.

## Lists

A bullet list (start each line with `-`):

- first thing
- second thing
  - a sub-point (indent two spaces before the `-`)

A numbered list (start each line with `1.`, `2.`, …):

1. enumerate
2. exploit
3. profit

## Code samples

For a single highlighted code block, use three backticks followed by the language
name, then close with three backticks. This is what makes code look good on the page:

```python
def greet(name: str) -> str:
    # comments are highlighted too
    return f"hello, {name}!"

print(greet("world"))
```

Swap the language after the opening backticks to highlight anything, `bash`,
`js`, `rust`, `json`, `c`, `sql`, and more:

```bash
# a shell command
nmap -sC -sV -oN scan.txt 10.10.10.10
```

## A table (optional)

| Port | Service | Notes      |
| ---- | ------- | ---------- |
| 22   | ssh     | open       |
| 80   | http    | apache 2.4 |

## An image (optional)

Drop the image file in the `/assets` folder, then reference it with `../assets/`:

![description of the image](../assets/avatar.svg)

---

### How to publish this post

1. Copy this file to `content/posts/your-post-slug.md`
2. Edit the frontmatter at the top (title, date, tags, excerpt)
3. Set `draft: false`
4. Add `"your-post-slug"` to the list in `content/posts/posts.json`

(This template itself never appears on the site, it isn't listed in `posts.json`,
and `draft: true` would hide it anyway.)
