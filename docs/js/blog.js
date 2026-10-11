(() => {
  'use strict';
  const grid = document.getElementById('postsGrid');
  const search = document.getElementById('searchInput');
  const loading = document.getElementById('loading');
  const empty = document.getElementById('emptyState');
  const count = document.getElementById('postCount');
  let posts = [];
  const text = (tag, cls, value) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    el.textContent = value;
    return el;
  };
  function card(post) {
    const link = document.createElement('a');
    const safeURL = new URL(post.url, location.href);
    if (safeURL.origin !== location.origin || !safeURL.pathname.endsWith('.html')) throw new Error('Invalid article URL');
    link.href = safeURL.href;
    link.className = 'post-card' + (post.featured ? ' featured-card' : '');
    if (post.image) {
      const image = document.createElement('img');
      image.src = post.image;
      image.alt = 'Стримы 24/7: своя панель и несколько эфиров';
      image.className = 'post-card-cover';
      image.width = 1672; image.height = 941;
      image.fetchPriority = post.featured ? 'high' : 'auto';
      image.loading = post.featured ? 'eager' : 'lazy';
      link.append(image);
    }
    const body = document.createElement('div');
    body.className = 'post-card-body';
    if (post.featured) body.append(text('span', 'new-label', 'Новая статья'));
    const meta = document.createElement('div');
    meta.className = 'post-meta';
    const date = new Date(post.date);
    const dateEl = text('time', 'post-date', date.toLocaleDateString('ru-RU', {day:'numeric',month:'long',year:'numeric',timeZone:'Europe/Kyiv'}));
    dateEl.dateTime = post.date;
    meta.append(dateEl, text('span', '', '·'), text('span', 'post-reading-time', `${post.reading_time || 5} мин чтения`));
    body.append(meta, text('h2', 'post-title', post.title.replace(/\s*🚀\s*$/, '')),
      text('p', 'post-excerpt', post.excerpt), text('span', 'post-link', 'Читать статью →'));
    link.append(body);
    return link;
  }
  function render() {
    const query = search.value.trim().toLocaleLowerCase('ru-RU');
    const filtered = posts.filter(p => (p.title + ' ' + p.excerpt).toLocaleLowerCase('ru-RU').includes(query));
    grid.replaceChildren(...filtered.map(card));
    empty.hidden = filtered.length > 0;
    empty.style.display = filtered.length ? 'none' : 'block';
    empty.querySelector('p').textContent = query ? 'Ничего не нашлось. Попробуй другое слово.' : 'Здесь скоро появятся статьи.';
    const n = filtered.length;
    count.textContent = `${n} ${n === 1 ? 'статья' : n > 1 && n < 5 ? 'статьи' : 'статей'}`;
  }
  search.addEventListener('input', render);
  fetch('posts/posts.json').then(response => {
    if (!response.ok) throw new Error('Не удалось загрузить статьи');
    return response.json();
  }).then(data => { posts = data.posts || []; render(); loading.hidden = true; loading.style.display = 'none'; })
    .catch(() => {
      loading.replaceChildren(text('p', '', 'Не удалось загрузить статьи. Попробуй обновить страницу.'));
      const retry = text('button', 'appearance-button', 'Обновить');
      retry.type = 'button'; retry.addEventListener('click', () => location.reload());
      loading.append(retry);
    });
})();
