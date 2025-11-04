"""
Публикация всех MD постов из папки posts/ на GitHub Pages
"""
import os
import json
import re
from datetime import datetime
import markdown


class SitePublisher:
    """Публикация постов на сайт"""
    
    def __init__(self):
        self.posts_json = "docs/posts/posts.json"
        self.posts_dir = "docs/posts"
        self.template_file = "docs/post-template.html"
        self.source_dir = "posts"  # Папка с MD файлами
        
    def sanitize_filename(self, title):
        """Создает безопасное имя файла из заголовка"""
        filename = re.sub(r'[^\w\s-]', '', title)
        filename = re.sub(r'\s+', '-', filename)
        filename = filename.lower()
        filename = filename[:100]
        return filename
    
    def extract_title_from_md(self, md_content):
        """Извлекает заголовок из markdown файла"""
        lines = md_content.strip().split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Без названия"
    
    def extract_excerpt(self, md_content, max_length=200):
        """Извлекает первые строки как превью"""
        lines = md_content.strip().split('\n')
        content_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        
        excerpt = ' '.join(content_lines[:3]).strip()
        
        if len(excerpt) > max_length:
            excerpt = excerpt[:max_length] + '...'
        
        return excerpt
    
    def calculate_reading_time(self, text):
        """Рассчитывает время чтения"""
        words_per_minute = 200
        words = len(text.split())
        minutes = max(1, round(words / words_per_minute))
        return minutes
    
    def md_to_html(self, md_content):
        """Конвертирует markdown в HTML"""
        lines = md_content.strip().split('\n')
        content_without_title = '\n'.join([line for line in lines if not line.startswith('# ')])
        
        html = markdown.markdown(content_without_title, extensions=['extra', 'codehilite'])
        return html
    
    def load_posts_json(self):
        """Загружает список постов"""
        if not os.path.exists(self.posts_json):
            return {"posts": []}
        
        with open(self.posts_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_posts_json(self, data):
        """Сохраняет список постов"""
        with open(self.posts_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def is_post_published(self, md_filename):
        """Проверяет опубликован ли пост"""
        posts_data = self.load_posts_json()
        
        # Проверяем по исходному имени MD файла
        for post in posts_data['posts']:
            if post.get('source_file') == md_filename:
                return True
        
        return False
    
    def publish_post(self, md_file_path):
        """Публикует пост на сайт"""
        
        md_filename = os.path.basename(md_file_path)
        
        # Проверяем не опубликован ли уже
        if self.is_post_published(md_filename):
            print(f"⏭️  Пропускаем (уже опубликован): {md_filename}")
            return None
        
        # Читаем markdown файл
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Извлекаем данные
        title = self.extract_title_from_md(md_content)
        excerpt = self.extract_excerpt(md_content)
        reading_time = self.calculate_reading_time(md_content)
        date = datetime.now().isoformat()
        
        # Генерируем имя файла
        filename = self.sanitize_filename(title)
        html_filename = f"{filename}.html"
        html_path = os.path.join(self.posts_dir, html_filename)
        
        # Конвертируем markdown в HTML
        html_content = self.md_to_html(md_content)
        
        # Читаем шаблон
        with open(self.template_file, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Форматируем дату
        date_obj = datetime.fromisoformat(date)
        months_ru = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        formatted_date = f"{date_obj.day} {months_ru[date_obj.month]} {date_obj.year}"
        
        # Заменяем плейсхолдеры
        html_page = template.replace('{{TITLE}}', title)
        html_page = html_page.replace('{{EXCERPT}}', excerpt)
        html_page = html_page.replace('{{DATE}}', formatted_date)
        html_page = html_page.replace('{{READING_TIME}}', str(reading_time))
        html_page = html_page.replace('{{CONTENT}}', html_content)
        
        # Сохраняем HTML файл
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_page)
        
        # Обновляем posts.json
        posts_data = self.load_posts_json()
        
        post_entry = {
            "title": title,
            "excerpt": excerpt,
            "date": date,
            "url": f"posts/{html_filename}",
            "source_file": md_filename  # Запоминаем исходный файл
        }
        
        # Добавляем в начало списка (новые посты сверху)
        posts_data['posts'].insert(0, post_entry)
        
        self.save_posts_json(posts_data)
        
        print(f"✅ Опубликован: {title}")
        print(f"   Файл: posts/{html_filename}")
        
        return html_path
    
    def publish_all(self):
        """Публикует все новые посты из папки posts/"""
        
        if not os.path.exists(self.source_dir):
            print(f"❌ Папка {self.source_dir}/ не найдена!")
            return
        
        # Находим все MD файлы
        md_files = [f for f in os.listdir(self.source_dir) if f.endswith('.md')]
        
        if not md_files:
            print(f"📝 В папке {self.source_dir}/ нет MD файлов")
            return
        
        print(f"📂 Найдено MD файлов: {len(md_files)}\n")
        
        published_count = 0
        skipped_count = 0
        
        for md_file in md_files:
            md_path = os.path.join(self.source_dir, md_file)
            result = self.publish_post(md_path)
            
            if result:
                published_count += 1
            else:
                skipped_count += 1
        
        print(f"\n{'=' * 60}")
        print(f"✅ Опубликовано: {published_count}")
        print(f"⏭️  Пропущено (уже были): {skipped_count}")
        print(f"{'=' * 60}")
        
        if published_count > 0:
            print("\n💡 Не забудь залить на GitHub:")
            print("   git add .")
            print("   git commit -m \"Новые посты\"")
            print("   git push")


def main():
    """Основная функция"""
    import sys
    import io
    
    # Фикс для кодировки Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("  📢 Публикация постов на GitHub Pages")
    print("=" * 60)
    print()
    
    publisher = SitePublisher()
    publisher.publish_all()


if __name__ == "__main__":
    main()

