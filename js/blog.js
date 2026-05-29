const SITE = {
  name: "sw1tchc4se",
  tagline: "notes on security, tooling, and the occasional rabbit hole",
  status: "currently: learning something new",
};

const ROOT = (function () {
  const me = document.currentScript && document.currentScript.src;
  return me ? me.replace(/js\/blog\.js(\?.*)?$/, "") : "";
})();

const _ic = (paths) =>
  `<svg class="icon" viewBox="0 0 24 24" fill="var(--ic-fill)" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;

const _brand = (paths) =>
  `<svg class="icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${paths}</svg>`;

const ICON = {

  petal: _ic(`<path d="M12 2c2.5 3 4 5.5 4 8a4 4 0 0 1-8 0c0-2.5 1.5-5 4-8zm-7 7c3 .5 5.2 1.6 6.6 3a4 4 0 0 1-5.6 5.7C4.4 16 4.2 13.4 5 9zm14 0c.8 4.4.6 7-1 8.7a4 4 0 0 1-5.6-5.7C13.8 10.6 16 9.5 19 9zM12 14a4 4 0 0 1 3.4 6.2c-1.2 1.6-3.7 2.6-7.4 2.8.6-4.4 1.8-7 4-9z"/>`),
  pin: _ic(`<path d="M12 21s-6-5.686-6-10a6 6 0 1 1 12 0c0 4.314-6 10-6 10z"/><circle cx="12" cy="11" r="2.2"/>`),
  sprout: _ic(`<path d="M12 21v-7"/><path d="M12 14c0-3.5 2-6 6.5-6 0 4.5-2.5 6-6.5 6z"/><path d="M12 16c0-2.5-2-4.5-5.5-4.5 0 3.5 2 4.5 5.5 4.5z"/>`),
  archive: _ic(`<path d="M4 8a2 2 0 0 1 2-2h2.5l1.5 1.6H18a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/>`),
  tools: _ic(`<path d="M14.6 6.3a4 4 0 0 0-5.3 5.3L3.5 17.4 6.6 20.5l5.7-5.8a4 4 0 0 0 5.3-5.3l-2.6 2.6-2.1-2.1z"/>`),
  link: _ic(`<path d="M10 13a5 5 0 0 0 7 0l2.5-2.5a5 5 0 0 0-7-7L11 5"/><path d="M14 11a5 5 0 0 0-7 0l-2.5 2.5a5 5 0 0 0 7 7L13 19"/>`),
  calendar: _ic(`<rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M3 10h18M8 2.5v4M16 2.5v4"/>`),
  coffee: _ic(`<path d="M17 8h1.5a3 3 0 0 1 0 6H17"/><path d="M3.5 8h13.5v6a4 4 0 0 1-4 4H7.5a4 4 0 0 1-4-4z"/><path d="M7 2.5v2M11 2.5v2"/>`),
  leaf: _ic(`<path d="M5 19c-1-7 4-13 15-14 0 11-6 15-15 14z"/><path d="M9 15c2-2 4.5-3.5 8-4.5"/>`),
  flower: _ic(`<circle cx="12" cy="12" r="2.4"/><ellipse cx="12" cy="6" rx="2.6" ry="3.4"/><ellipse cx="12" cy="18" rx="2.6" ry="3.4"/><ellipse cx="6" cy="12" rx="3.4" ry="2.6"/><ellipse cx="18" cy="12" rx="3.4" ry="2.6"/>`),
  fire: _ic(`<path d="M12 3c2.8 3.2 5 5.6 5 9a5 5 0 0 1-10 0c0-1.7.7-3 1.8-4 .2 1.2 1 1.9 2.2 2-1-2.8 0-5 1-7z"/>`),
  idea: _ic(`<path d="M12 3a6 6 0 0 0-3.7 10.7c.5.4.7.9.7 1.5v.8h6v-.8c0-.6.2-1.1.7-1.5A6 6 0 0 0 12 3z"/><path d="M9.5 19h5M10.5 21.5h3"/>`),
  star: _ic(`<path d="M12 3.5l2.6 5.3 5.8.9-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.6 9.7l5.8-.9z"/>`),
  heart: _ic(`<path d="M12 20.5S4 16 4 9.8A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 8 2.8C20 16 12 20.5 12 20.5z"/>`),
  sparkles: _ic(`<path d="M12 4l1.5 4.2L18 9.5l-4.5 1.3L12 15l-1.5-4.2L6 9.5l4.5-1.3z"/><path d="M18.5 14l.7 1.9 1.9.7-1.9.7-.7 1.9-.7-1.9-1.9-.7 1.9-.7z"/>`),
  sun: _ic(`<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/>`),
  moon: _ic(`<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>`),
  mail: _ic(`<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>`),
  at: _ic(`<circle cx="12" cy="12" r="4"/><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.8 7.9"/>`),
  github: _brand(`<path d="M12 .5C5.4.5 0 5.9 0 12.5c0 5.3 3.4 9.8 8.2 11.4.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.3-1.8-1.3-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17.3 4.6 18.3 5 18.3 5c.7 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 24 12.5C24 5.9 18.6.5 12 .5z"/>`),
  twitter: _brand(`<path d="M24 4.6a9.9 9.9 0 0 1-2.8.8 4.9 4.9 0 0 0 2.2-2.7c-1 .6-2 1-3.1 1.2a4.9 4.9 0 0 0-8.4 4.5A13.9 13.9 0 0 1 1.7 3.2a4.9 4.9 0 0 0 1.5 6.6 4.9 4.9 0 0 1-2.2-.6v.1a4.9 4.9 0 0 0 4 4.8 4.9 4.9 0 0 1-2.2.1 4.9 4.9 0 0 0 4.6 3.4A9.9 9.9 0 0 1 0 19.5a13.9 13.9 0 0 0 7.6 2.2c9 0 14-7.5 14-14v-.6A10 10 0 0 0 24 4.6z"/>`),
};

function icon(name, extraClass = "") {
  const svg = ICON[name] || "";
  return extraClass ? svg.replace('class="icon"', `class="icon ${extraClass}"`) : svg;
}

function injectIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => {
    if (el.dataset.iconDone) return;
    el.innerHTML = icon(el.dataset.icon, el.dataset.iconClass || "");
    el.dataset.iconDone = "1";
  });
}

function applyStoredTheme() {
  const saved = localStorage.getItem("theme");
  const theme = saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", theme);
}
function toggleTheme() {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  const btn = document.querySelector(".theme-toggle");
  if (btn) btn.innerHTML = icon(next === "dark" ? "sun" : "moon");
}
applyStoredTheme();

function buildChrome(active) {
  const header = document.createElement("header");
  header.className = "site-header";
  header.innerHTML = `
    <nav class="nav">
      <a class="brand" href="${ROOT}">${ICON.petal}${SITE.name}</a>
      <div class="nav-links">
        <a href="${ROOT}" data-nav="home">home</a>
        <a href="${ROOT}posts/" data-nav="posts">posts</a>
        <a href="${ROOT}about/" data-nav="about">about</a>
        <button class="theme-toggle" title="Toggle theme" aria-label="Toggle dark mode"></button>
      </div>
    </nav>`;
  document.body.prepend(header);

  const navActive = header.querySelector(`[data-nav="${active}"]`);
  if (navActive) navActive.classList.add("active");

  const toggle = header.querySelector(".theme-toggle");
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  toggle.innerHTML = icon(isDark ? "sun" : "moon");
  toggle.addEventListener("click", toggleTheme);

  const footer = document.createElement("footer");
  footer.className = "site-footer";
  footer.innerHTML = `
    ${icon("petal")}
    <p>made with care by <strong>${SITE.name}</strong> · static &amp; serverless</p>
    <p>© ${new Date().getFullYear()} · built with plain HTML, CSS &amp; JS</p>`;
  document.body.appendChild(footer);

  injectIcons();
}

function parseFrontmatter(raw) {
  const match = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);
  if (!match) return { data: {}, content: raw };
  const data = {};
  for (const line of match[1].split("\n")) {
    const m = line.match(/^(\w+)\s*:\s*(.*)$/);
    if (!m) continue;
    let [, key, val] = m;
    val = val.trim();
    if (val.startsWith("[") && val.endsWith("]")) {
      data[key] = val.slice(1, -1).split(",")
        .map((s) => s.trim().replace(/^["']|["']$/g, ""))
        .filter(Boolean);
    } else if (val === "true" || val === "false") {
      data[key] = val === "true";
    } else {
      data[key] = val.replace(/^["']|["']$/g, "");
    }
  }
  return { data, content: match[2] };
}

let _postsCache = null;

async function loadAllPosts() {
  if (_postsCache) return _postsCache;
  const manifest = await fetch(`${ROOT}content/posts/posts.json`).then((r) => r.json());
  const posts = await Promise.all(
    manifest.map(async (slug) => {
      const raw = await fetch(`${ROOT}content/posts/${slug}.md`).then((r) => r.text());
      const { data, content } = parseFrontmatter(raw);
      return {
        slug,
        title: data.title || slug,
        date: data.date || "",
        tags: data.tags || [],
        pinned: !!data.pinned,
        draft: !!data.draft,
        excerpt: data.excerpt || "",
        content,
      };
    })
  );
  _postsCache = posts
    .filter((p) => !p.draft)
    .sort((a, b) => new Date(b.date) - new Date(a.date));
  return _postsCache;
}

async function loadPost(slug) {
  const raw = await fetch(`${ROOT}content/posts/${slug}.md`).then((r) => {
    if (!r.ok) throw new Error("not found");
    return r.text();
  });
  const { data, content } = parseFrontmatter(raw);
  return {
    slug,
    title: data.title || slug,
    date: data.date || "",
    tags: data.tags || [],
    pinned: !!data.pinned,
    excerpt: data.excerpt || "",
    content,
  };
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  if (isNaN(d)) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function readingCoffees(markdown) {
  const words = markdown.trim().split(/\s+/).length;
  const minutes = Math.max(1, Math.round(words / 200));
  const cups = Math.max(1, Math.ceil(minutes / 4));
  return { minutes, cups };
}

function tagPills(tags, { link = false } = {}) {
  return tags
    .map((t) =>
      link
        ? `<a class="tag" href="${ROOT}posts/?tag=${encodeURIComponent(t)}">${t}</a>`
        : `<span class="tag">${t}</span>`
    )
    .join("");
}

function postCard(p, { pinned = false } = {}) {
  return `
    <a class="card ${pinned ? "pinned" : ""}" href="${ROOT}post/?post=${encodeURIComponent(p.slug)}">
      ${pinned ? `<span class="pin-badge">${icon("pin")} pinned</span>` : ""}
      <h3>${p.title}</h3>
      <div class="meta"><span>${icon("calendar")} ${formatDate(p.date)}</span></div>
      <p>${p.excerpt}</p>
      <div class="tags">${tagPills(p.tags)}</div>
    </a>`;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function setMeta(attr, key, content) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function setCanonical(href) {
  let el = document.head.querySelector('link[rel="canonical"]');
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", "canonical");
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}
