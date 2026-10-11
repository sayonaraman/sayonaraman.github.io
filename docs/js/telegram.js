(() => {
  'use strict';
  const tg = window.Telegram?.WebApp;
  const onArticle = location.pathname.includes('/posts/');
  const home = onArticle ? '../index.html' : 'index.html';
  const storage = {
    get(key, fallback) { try { return localStorage.getItem(key) || fallback; } catch { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* Ephemeral webview. */ } }
  };
  let fontSize = storage.get('blog-font-size', 'normal');
  function apply() {
    if (!['normal', 'large'].includes(fontSize)) fontSize = 'normal';
    document.documentElement.dataset.theme = 'dark';
    document.documentElement.dataset.fontSize = fontSize;
    if (tg?.initData) {
      const color = getComputedStyle(document.documentElement).getPropertyValue('--bg-primary').trim();
      tg.setHeaderColor(color);
      tg.setBackgroundColor(color);
      if (tg.isVersionAtLeast?.('7.10')) tg.setBottomBarColor(color);
    }
  }
  apply();
  if (tg?.initData) {
    tg.ready();
    tg.expand();
    if (onArticle) { tg.BackButton.show(); tg.BackButton.onClick(() => { location.href = home; }); }
    else tg.BackButton.hide();
  }
  const slug = new URLSearchParams(location.search).get('tgWebAppStartParam') || tg?.initDataUnsafe?.start_param;
  const routes = {stream24x7: 'posts/stream24x7.html'};
  if (!onArticle && Object.hasOwn(routes, slug)) { location.replace(routes[slug]); return; }

  if (onArticle) {
  const dialog = document.createElement('dialog');
  dialog.className = 'appearance-dialog';
  dialog.setAttribute('aria-labelledby', 'appearance-title');
  dialog.innerHTML = `<form method="dialog"><div class="appearance-heading"><h2 id="appearance-title">Размер текста</h2><button class="close-appearance" aria-label="Закрыть настройки текста">×</button></div><fieldset><legend>Текст статьи</legend><div class="font-options"><label><input type="radio" name="font" value="normal">Обычный</label><label><input type="radio" name="font" value="large">Крупнее</label></div></fieldset><p class="appearance-note">Настройки сохраняются на этом устройстве.</p><button class="appearance-done">Готово</button></form>`;
  document.body.append(dialog);
  const button = document.createElement('button');
  button.className = 'appearance-button';
  button.type = 'button';
  button.setAttribute('aria-label', 'Настроить размер текста');
  button.setAttribute('aria-haspopup', 'dialog');
  button.innerHTML = '<span aria-hidden="true">Aa</span><span>Размер текста</span>';
  const back = document.querySelector('.back-link');
  if (back) {
    const actions = document.createElement('div');
    actions.className = 'article-actions';
    back.before(actions);
    actions.append(back, button);
  }
  button.addEventListener('click', () => {
    dialog.querySelector(`input[name="font"][value="${fontSize}"]`).checked = true;
    dialog.showModal();
  });
  dialog.addEventListener('change', event => {
    if (event.target.name === 'font') { fontSize = event.target.value; storage.set('blog-font-size', fontSize); }
    apply();
  });
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      const r = dialog.getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
    }
  });
  }
  const progress = document.querySelector('.reading-progress');
  if (progress) {
    const update = () => {
      const total = document.documentElement.scrollHeight - innerHeight;
      progress.style.width = `${total > 0 ? Math.min(100, scrollY / total * 100) : 0}%`;
    };
    window.addEventListener('scroll', update, {passive: true});
    window.addEventListener('resize', update);
    update();
  }
})();
