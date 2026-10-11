#!/usr/bin/env python3
"""Build the reviewed stream post without AI rewriting or runtime dependencies."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parent.parent
source = ROOT / 'posts/stream24x7.md'
lines = source.read_text().strip().splitlines()


def inline(text):
    value = html.escape(text)
    value = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
                   r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', value)


blocks, headings = [], []
i = 1
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith('```'):
        code = []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            code.append(lines[i])
            i += 1
        if i == len(lines):
            raise ValueError('Unclosed code block in source.')
        blocks.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            cells = [x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', x) for x in cells):
                rows.append(cells)
            i += 1
        header = '<tr>' + ''.join('<th scope="col">' + inline(x) + '</th>' for x in rows[0]) + '</tr>'
        body = ''.join('<tr>' + ''.join('<td>' + inline(x) + '</td>' for x in row) + '</tr>' for row in rows[1:])
        label = 'Профиль готового видео' if rows[0][0] == 'Параметр' else 'Расход трафика трансляций'
        blocks.append('<div class="table-scroll" tabindex="0" role="region" aria-label="' + label + '"><table><thead>' + header + '</thead><tbody>' + body + '</tbody></table></div>')
        continue
    if line.startswith('• '):
        items = []
        while i < len(lines) and lines[i].strip().startswith('• '):
            items.append('<li>' + inline(lines[i].strip()[2:]) + '</li>')
            i += 1
        blocks.append('<ul>' + ''.join(items) + '</ul>')
        continue
    if re.fullmatch(r'\*\*.+\*\*', line):
        title = line[2:-2]
        anchor = 'section-' + str(len(headings) + 1)
        headings.append((anchor, title))
        blocks.append(f'<h2 id="{anchor}">{html.escape(title)}</h2>')
        i += 1
        continue
    paragraph = [line]
    i += 1
    while i < len(lines) and lines[i].strip():
        paragraph.append(lines[i].strip())
        i += 1
    blocks.append('<p>' + inline(' '.join(paragraph)) + '</p>')

title = 'Как я организовал YouTube-трансляции 24/7 через свою панель'
excerpt = 'Готовим видео один раз, запускаем несколько независимых эфиров и считаем реальную скорость отдачи и месячный трафик. Всё про мою панель и подготовку видео.'
minutes = max(1, round(len(source.read_text().split()) / 180))
toc = ''.join(f'<li><a href="#{anchor}">{html.escape(text)}</a></li>' for anchor, text in headings)
page = f'''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title} · Блог</title>
  <meta name="description" content="{excerpt}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{excerpt}">
  <meta property="og:type" content="article">
  <meta property="og:image" content="https://sayonaraman.github.io/images/stream24x7.png">
  <link rel="canonical" href="https://sayonaraman.github.io/posts/stream24x7.html">
  <link rel="stylesheet" href="../css/style.css?v=20261012-1">
  <script src="https://telegram.org/js/telegram-web-app.js" defer></script>
  <script src="../js/telegram.js" defer></script>
</head>
<body>
  <div class="reading-progress" aria-hidden="true"></div>
  <div class="container">
    <a href="../index.html" class="back-link">← Назад к постам</a>
    <article class="post-content">
      <header class="post-header">
        <span class="topic-label">Автоматизация · YouTube</span>
        <h1>{title}</h1>
        <div class="post-meta"><time datetime="2026-10-12">12 октября 2026</time><span aria-hidden="true">·</span><span>{minutes} мин чтения</span></div>
      </header>
      <img class="article-cover" src="../images/stream24x7.png" width="1672" height="941" alt="Стримы 24/7: своя панель и несколько эфиров. Считай upload и трафик.">
      <details class="article-toc"><summary>В этой статье</summary><ol>{toc}</ol></details>
      <div class="post-content-body">{''.join(blocks)}</div>
      <div class="article-end"><span>Дочитал? Теперь можно считать свои эфиры.</span><a href="../index.html">Все статьи →</a></div>
    </article>
    <footer class="footer"><p>Сделано с ❤️ для вайбкодеров · 2026</p></footer>
  </div>
</body>
</html>'''
(ROOT / 'docs/posts/stream24x7.html').write_text(page)
path = ROOT / 'docs/posts/posts.json'
data = json.loads(path.read_text())
data['posts'] = [p for p in data['posts'] if p.get('url') != 'posts/stream24x7.html']
data['posts'].insert(0, {'title': 'Стримы 24/7: своя панель и несколько эфиров',
                       'excerpt': excerpt, 'date': '2026-10-12T00:00:00+03:00',
                       'url': 'posts/stream24x7.html', 'source_file': 'stream24x7.md',
                       'image': 'images/stream24x7.png', 'reading_time': minutes,
                       'category': 'Автоматизация', 'featured': True})
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(f'Built stream article: {len(blocks)} blocks, {len(headings)} sections, {minutes} min; existing articles preserved.')
