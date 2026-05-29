(async function () {
  buildChrome("home");

  document.getElementById("hero-name").textContent = SITE.name;
  document.getElementById("hero-tagline").textContent = SITE.tagline;
  document.getElementById("hero-status").innerHTML =
    `<span class="status-dot"></span> ${SITE.status} ${icon("sparkles")}`;

  let posts;
  try {
    posts = await loadAllPosts();
  } catch (e) {
    document.getElementById("recent").innerHTML =
      `<p class="empty-state">Couldn't load posts. If you're viewing this locally, serve it with a tiny web server (see README).</p>`;
    return;
  }

  const pinned = posts.filter((p) => p.pinned);
  const recent = posts.slice(0, 5);

  if (pinned.length) {
    document.getElementById("pinned-section").style.display = "";
    document.getElementById("pinned").innerHTML = pinned
      .map((p) => postCard(p, { pinned: true }))
      .join("");
  }

  document.getElementById("recent").innerHTML =
    recent.map((p) => postCard(p)).join("") ||
    `<p class="empty-state">No posts yet, check back soon ${icon("sprout")}</p>`;
})();
