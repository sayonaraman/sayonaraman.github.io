// === Конфигурация === 
const POSTS_FILE = 'posts/posts.json';

// === Глобальные переменные ===
let allPosts = [];

// === Инициализация ===
document.addEventListener('DOMContentLoaded', async () => {
    await loadPosts();
    setupSearch();
});

// === Загрузка постов ===
async function loadPosts() {
    const loading = document.getElementById('loading');
    const postsGrid = document.getElementById('postsGrid');
    const emptyState = document.getElementById('emptyState');

    try {
        const response = await fetch(POSTS_FILE);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить посты');
        }

        const data = await response.json();
        allPosts = data.posts || [];

        loading.style.display = 'none';

        if (allPosts.length === 0) {
            emptyState.style.display = 'block';
            return;
        }

        renderPosts(allPosts);
    } catch (error) {
        console.error('Ошибка загрузки постов:', error);
        loading.innerHTML = '<p style="color: var(--text-secondary);">❌ Не удалось загрузить посты</p>';
    }
}

// === Рендер постов ===
function renderPosts(posts) {
    const postsGrid = document.getElementById('postsGrid');
    postsGrid.innerHTML = '';

    if (posts.length === 0) {
        document.getElementById('emptyState').style.display = 'block';
        return;
    }

    document.getElementById('emptyState').style.display = 'none';

    posts.forEach(post => {
        const card = createPostCard(post);
        postsGrid.appendChild(card);
    });
}

// === Создание карточки поста ===
function createPostCard(post) {
    const card = document.createElement('article');
    card.className = 'post-card';
    card.onclick = () => window.location.href = post.url;

    const readingTime = calculateReadingTime(post.excerpt);

    card.innerHTML = `
        <div class="post-meta">
            <span class="post-date">📅 ${formatDate(post.date)}</span>
            <span>•</span>
            <span class="post-reading-time">⏱️ ${readingTime} мин</span>
        </div>
        <h2 class="post-title">${post.title}</h2>
        <p class="post-excerpt">${post.excerpt}</p>
        <a href="${post.url}" class="post-link" onclick="event.stopPropagation()">
            Читать далее →
        </a>
    `;

    return card;
}

// === Поиск ===
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        
        if (query === '') {
            renderPosts(allPosts);
            return;
        }

        const filtered = allPosts.filter(post => 
            post.title.toLowerCase().includes(query) ||
            post.excerpt.toLowerCase().includes(query)
        );

        renderPosts(filtered);
    });
}

// === Утилиты ===
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('ru-RU', options);
}

function calculateReadingTime(text) {
    const wordsPerMinute = 200;
    const words = text.split(/\s+/).length;
    const minutes = Math.ceil(words / wordsPerMinute);
    return minutes;
}

