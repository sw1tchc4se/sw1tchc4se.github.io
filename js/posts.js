(async function () {
  buildChrome("posts");

  const listEl = document.getElementById("timeline");
  const searchEl = document.getElementById("search");
  const filterEl = document.getElementById("tag-filter");

  let posts;
  try {
    posts = await loadAllPosts();
  } catch (e) {
    listEl.innerHTML = `<p class="empty-state">Couldn't load posts. Serve the site over HTTP (see README).</p>`;
    return;
  }

  const allTags = [...new Set(posts.flatMap((p) => p.tags))].sort();

  const params = new URLSearchParams(location.search);
  const state = { query: "", tag: params.get("tag") || null };

  function renderFilters() {
    filterEl.innerHTML =
      `<span class="filter-label">filter:</span>` +
      allTags
        .map(
          (t) =>
            `<span class="tag ${state.tag === t ? "active" : ""}" data-tag="${t}">${t}</span>`
        )
        .join("");
    filterEl.querySelectorAll("[data-tag]").forEach((el) => {
      el.addEventListener("click", () => {
        state.tag = state.tag === el.dataset.tag ? null : el.dataset.tag;
        renderFilters();
        renderList();
      });
    });
  }

  function renderList() {
    const q = state.query.toLowerCase();
    const filtered = posts.filter((p) => {
      const matchesTag = !state.tag || p.tags.includes(state.tag);
      const haystack = (p.title + " " + p.excerpt + " " + p.tags.join(" ")).toLowerCase();
      const matchesQuery = !q || haystack.includes(q);
      return matchesTag && matchesQuery;
    });

    if (!filtered.length) {
      const msg = posts.length
        ? "No posts match that, try clearing the filters"
        : "No posts here yet, check back soon";
      listEl.innerHTML = `<p class="empty-state">${msg} ${icon("sprout")}</p>`;
      return;
    }

    listEl.innerHTML = filtered
      .map(
        (p) => `
        <div class="timeline-item">
          <a class="card" href="${ROOT}post/${encodeURIComponent(p.slug)}/">
            <h3>${p.title}</h3>
            <div class="meta"><span>${icon("calendar")} ${formatDate(p.date)}</span></div>
            <p>${p.excerpt}</p>
            <div class="tags">${tagPills(p.tags)}</div>
          </a>
        </div>`
      )
      .join("");
  }

  searchEl.addEventListener("input", (e) => {
    state.query = e.target.value;
    renderList();
  });

  renderFilters();
  renderList();
})();
