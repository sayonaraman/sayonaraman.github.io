(() => {
  'use strict';
  const tg = window.Telegram?.WebApp;
  const onArticle = location.pathname.includes('/posts/');
  const home = onArticle ? '../index.html' : 'index.html';
  const storage = {
    get(key, fallback) { try { return localStorage.getItem(key) || fallback; } catch { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* Ephemeral webview. */ } }
  };
  let theme = storage.get('blog-theme', 'yellow');
  let fontSize = storage.get('blog-font-size', 'normal');
  function apply() {
    if (!['yellow', 'light', 'dark'].includes(theme)) theme = 'yellow';
    if (!['normal', 'large'].includes(fontSize)) fontSize = 'normal';
    document.documentElement.dataset.theme = theme;
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

  const dialog = document.createElement('dialog');
  dialog.className = 'appearance-dialog';
  dialog.setAttribute('aria-labelledby', 'appearance-title');
  dialog.innerHTML = `<form method="dialog"><div class="appearance-heading"><h2 id="appearance-title">Оформление</h2><button class="close-appearance" aria-label="Закрыть оформление">×</button></div><fieldset><legend>Тема</legend><div class="theme-options"><label><input type="radio" name="theme" value="yellow"><span class="theme-swatch swatch-yellow"></span>Жёлтая</label><label><input type="radio" name="theme" value="light"><span class="theme-swatch swatch-light"></span>Светлая</label><label><input type="radio" name="theme" value="dark"><span class="theme-swatch swatch-dark"></span>Тёмная</label></div></fieldset><fieldset><legend>Текст статьи</legend><div class="font-options"><label><input type="radio" name="font" value="normal">Обычный</label><label><input type="radio" name="font" value="large">Крупнее</label></div></fieldset><p class="appearance-note">Настройки сохраняются на этом устройстве.</p><button class="appearance-done">Готово</button></form>`;
  document.body.append(dialog);
  const button = document.createElement('button');
  button.className = 'appearance-button';
  button.type = 'button';
  button.setAttribute('aria-label', 'Настроить оформление');
  button.setAttribute('aria-haspopup', 'dialog');
  button.innerHTML = '<span aria-hidden="true">◐</span><span>Оформление</span>';
  const header = document.querySelector('.header-content');
  const back = document.querySelector('.back-link');
  if (header) header.append(button);
  else if (back) {
    const actions = document.createElement('div');
    actions.className = 'article-actions';
    back.before(actions);
    actions.append(back, button);
  }
  button.addEventListener('click', () => {
    dialog.querySelector(`input[name="theme"][value="${theme}"]`).checked = true;
    dialog.querySelector(`input[name="font"][value="${fontSize}"]`).checked = true;
    dialog.showModal();
  });
  dialog.addEventListener('change', event => {
    if (event.target.name === 'theme') { theme = event.target.value; storage.set('blog-theme', theme); }
    if (event.target.name === 'font') { fontSize = event.target.value; storage.set('blog-font-size', fontSize); }
    apply();
  });
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      const r = dialog.getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
    }
  });
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
