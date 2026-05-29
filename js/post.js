(async function () {
  buildChrome("");

  const slug = new URLSearchParams(location.search).get("post");
  const article = document.getElementById("article");

  if (!slug) {
    location.replace(`${ROOT}posts/`);
    return;
  }

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
  setMeta("property", "og:url", location.href);
  setCanonical(location.href);

  const { minutes, cups } = readingCoffees(post.content);
  const bodyHtml = marked.parse(post.content);

  article.innerHTML = `
    <header class="post-header">
      <a class="back-link" href="${ROOT}posts/">← all posts</a>
      <h1>${post.title}</h1>
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

  document.querySelectorAll("#prose pre code").forEach((block) => hljs.highlightElement(block));

  buildTOC();
  buildReactions();
  buildRelated();

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
      li.innerHTML = `<a href="#${id}">${h.textContent}</a>`;
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
        <button class="reaction ${store[r]?.mine ? "reacted" : ""}" data-emoji="${r}">
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
})();
