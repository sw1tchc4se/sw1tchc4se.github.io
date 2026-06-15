(async function () {
  buildChrome("");

  // Defined up here (not lower down) so the prerendered branch below can use
  // them — a `const` is in the temporal dead zone until its declaration runs.
  const COPY_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>';
  const CHECK_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';

  const slug = window.__POST_SLUG__ || new URLSearchParams(location.search).get("post");
  const article = document.getElementById("article");

  if (!slug) {
    location.replace(`${ROOT}posts/`);
    return;
  }

  // Pages written by tools/build.py already contain the rendered article, its
  // metadata and (when relevant) the related list. In that case we only need to
  // *enhance* the existing DOM — no re-parsing the markdown, no marked.js.
  if (window.__PRERENDERED__) {
    const prose = document.getElementById("prose");
    highlightCode(prose);
    addCopyButtons(prose);
    buildTOC();
    buildReactions();
    return;
  }

  // ---- fallback: no prerendered HTML, render the post on the client ----
  let post, allPosts;
  try {
    [post, allPosts] = await Promise.all([loadPost(slug), loadAllPosts()]);
  } catch (e) {
    article.innerHTML = `
      <div class="empty-state">
        <h2>Post not found</h2>
        <p>That post doesn't exist (or the site needs to be served over HTTP).</p>
        <a class="btn" href="${ROOT}posts/">← back to posts</a>
      </div>`;
    return;
  }

  document.title = `${post.title} · ${SITE.name}`;
  setMeta("name", "description", post.excerpt || post.title);
  setMeta("property", "og:title", `${post.title} · ${SITE.name}`);
  setMeta("property", "og:description", post.excerpt || post.title);
  const cleanUrl = `${ROOT}post/${slug}/`;
  setMeta("property", "og:url", cleanUrl);
  setCanonical(cleanUrl);

  const { minutes, cups } = readingCoffees(post.content);
  const bodyHtml = marked.parse(post.content);

  article.innerHTML = `
    <header class="post-header">
      <a class="back-link" href="${ROOT}posts/">← all posts</a>
      <h1>${escapeHtml(post.title)}</h1>
      <div class="post-meta">
        <span>${icon("calendar")} ${formatDate(post.date)}</span>
        <span class="coffee" title="~${minutes} min read">${icon("coffee").repeat(cups)} ${minutes} min</span>
      </div>
      <div class="tags">${tagPills(post.tags, { link: true })}</div>
    </header>

    <div class="divider">${icon("petal")}</div>

    <div class="post-layout">
      <article class="prose" id="prose">${bodyHtml}</article>
      <aside class="toc" id="toc" style="display:none">
        <h4>${icon("archive")} contents</h4>
        <ul id="toc-list"></ul>
      </aside>
    </div>

    <div id="reactions-mount"></div>

    <div class="divider">${icon("petal")}</div>

    <section id="related-section" style="display:none">
      <h2 class="section-title">${icon("sprout")} related reads</h2>
      <div class="cards" id="related"></div>
    </section>`;

  highlightCode(document.getElementById("prose"));
  addCopyButtons(document.getElementById("prose"));
  buildTOC();
  buildReactions();
  buildRelated();

  function buildRelated() {
    const related = allPosts
      .filter((p) => p.slug !== slug)
      .map((p) => ({ p, shared: p.tags.filter((t) => post.tags.includes(t)).length }))
      .filter((x) => x.shared > 0)
      .sort((a, b) => b.shared - a.shared || new Date(b.p.date) - new Date(a.p.date))
      .slice(0, 3)
      .map((x) => x.p);

    if (!related.length) return;
    document.getElementById("related-section").style.display = "";
    document.getElementById("related").innerHTML = related.map((p) => postCard(p)).join("");
  }

  // ---- shared enhancers (used by both paths) ----
  function highlightCode(root) {
    if (typeof hljs === "undefined") return;
    root.querySelectorAll("pre code").forEach((block) => hljs.highlightElement(block));
  }

  function addCopyButtons(root) {
    root.querySelectorAll("pre").forEach((pre) => {
      if (pre.parentElement.classList.contains("code-wrap")) return;
      const wrap = document.createElement("div");
      wrap.className = "code-wrap";
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy-btn";
      btn.innerHTML = COPY_SVG;
      btn.setAttribute("aria-label", "copy code to clipboard");
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText(pre.innerText).then(() => {
          btn.innerHTML = CHECK_SVG;
          btn.classList.add("copied");
          btn.setAttribute("aria-label", "copied");
          setTimeout(() => {
            btn.innerHTML = COPY_SVG;
            btn.classList.remove("copied");
            btn.setAttribute("aria-label", "copy code to clipboard");
          }, 1500);
        });
      });
      wrap.appendChild(btn);
    });
  }

  function buildTOC() {
    const prose = document.getElementById("prose");
    const headings = prose.querySelectorAll("h2, h3");
    if (!headings.length) return;
    const list = document.getElementById("toc-list");
    headings.forEach((h, i) => {
      const id = h.id || `h-${i}-${h.textContent.toLowerCase().replace(/[^\w]+/g, "-").replace(/^-|-$/g, "")}`;
      h.id = id;
      const li = document.createElement("li");
      if (h.tagName === "H3") li.className = "h3";
      li.innerHTML = `<a href="#${id}">${escapeHtml(h.textContent)}</a>`;
      list.appendChild(li);
    });
    document.getElementById("toc").style.display = "";

    const links = list.querySelectorAll("a");
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            links.forEach((l) => l.classList.remove("active"));
            const active = list.querySelector(`a[href="#${en.target.id}"]`);
            if (active) active.classList.add("active");
          }
        });
      },
      { rootMargin: "-10% 0px -80% 0px" }
    );
    headings.forEach((h) => obs.observe(h));
  }

  function buildReactions() {
    const reactions = ["leaf", "flower", "sparkles", "heart"];
    const key = `reactions:${slug}`;
    const store = JSON.parse(localStorage.getItem(key) || "{}");
    const mount = document.getElementById("reactions-mount");
    const bar = document.createElement("div");
    bar.className = "reactions";
    bar.innerHTML = reactions
      .map(
        (r) => `
        <button class="reaction ${store[r]?.mine ? "reacted" : ""}" data-emoji="${r}" aria-label="react with ${r}">
          ${icon(r)}<span class="count">${store[r]?.count || 0}</span>
        </button>`
      )
      .join("");
    mount.appendChild(bar);

    bar.querySelectorAll(".reaction").forEach((btn) => {
      btn.addEventListener("click", () => {
        const e = btn.dataset.emoji;
        const entry = store[e] || { count: 0, mine: false };
        if (entry.mine) {
          entry.count = Math.max(0, entry.count - 1);
          entry.mine = false;
          btn.classList.remove("reacted");
        } else {
          entry.count += 1;
          entry.mine = true;
          btn.classList.add("reacted", "bump");
          setTimeout(() => btn.classList.remove("bump"), 420);
        }
        store[e] = entry;
        localStorage.setItem(key, JSON.stringify(store));
        btn.querySelector(".count").textContent = entry.count;
      });
    });
  }
})();
