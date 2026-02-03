// API Configuration
const API_BASE_URL = 'http://localhost:3000/api'; // Replace with your actual API URL
const AUTH_TOKEN = localStorage.getItem('authToken'); // Assuming you store auth token in localStorage

// Get URL parameters
const urlParams = new URLSearchParams(window.location.search);
const pageType = urlParams.get('type') || 'all'; // 'all', 'search', 'bookmarks', 'tag'
const searchQuery = urlParams.get('query') || '';
const tagQuery = urlParams.get('tag') || '';

let allArticles = [];
let filteredArticles = [];
let currentSort = 'newest';
let currentPage = 1;
const articlesPerPage = 10;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    configurePageByType();
    fetchArticles();
});

// Configure page based on type
function configurePageByType() {
    const titleEl = document.getElementById('page-title');
    const subtitleEl = document.getElementById('page-subtitle');
    const backBtn = document.getElementById('back-btn');
    
    switch(pageType) {
        case 'search':
            titleEl.textContent = `Search Results`;
            subtitleEl.textContent = `Results for "${searchQuery}"`;
            break;
        case 'bookmarks':
            titleEl.textContent = 'Bookmarked Articles';
            subtitleEl.textContent = 'Your saved articles for later reading';
            break;
        case 'tag':
            titleEl.textContent = `Tag: ${tagQuery}`;
            subtitleEl.textContent = `Articles tagged with "${tagQuery}"`;
            break;
        case 'author':
            const authorName = urlParams.get('author') || 'Author';
            titleEl.textContent = `Articles by ${authorName}`;
            subtitleEl.textContent = `All articles written by ${authorName}`;
            break;
        default:
            titleEl.textContent = 'All Articles';
            subtitleEl.textContent = 'Browse all articles';
    }
}

// Fetch articles from API
async function fetchArticles() {
    try {
        showLoading();
        
        let apiEndpoint = '';
        let requestParams = {};
        
        // Determine API endpoint based on page type
        switch(pageType) {
            case 'search':
                apiEndpoint = `${API_BASE_URL}/articles/search`;
                requestParams = { query: searchQuery };
                break;
            case 'bookmarks':
                apiEndpoint = `${API_BASE_URL}/user/bookmarks`;
                break;
            case 'tag':
                apiEndpoint = `${API_BASE_URL}/articles/tag/${encodeURIComponent(tagQuery)}`;
                break;
            case 'author':
                const authorId = urlParams.get('authorId');
                apiEndpoint = `${API_BASE_URL}/articles/author/${authorId}`;
                break;
            default:
                apiEndpoint = `${API_BASE_URL}/articles`;
        }
        
        // Build query string for GET requests
        const queryString = Object.keys(requestParams).length > 0 
            ? '?' + new URLSearchParams(requestParams).toString() 
            : '';
        
        const response = await fetch(`${apiEndpoint}${queryString}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'auth.html';
                return;
            }
            throw new Error('Failed to fetch articles');
        }

        const data = await response.json();
        allArticles = data.articles || [];
        filteredArticles = [...allArticles];
        
        hideLoading();
        updateResultsCount();
        sortArticles('newest');
    } catch (error) {
        console.error('Error fetching articles:', error);
        hideLoading();
        showError('Failed to load articles. Please try again later.');
    }
}

// Show loading state
function showLoading() {
    document.getElementById('loading-state').style.display = 'block';
    document.getElementById('articles-container').style.display = 'none';
}

// Hide loading state
function hideLoading() {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('articles-container').style.display = 'flex';
}

// Update results count
function updateResultsCount() {
    const count = filteredArticles.length;
    const countEl = document.getElementById('results-count');
    countEl.textContent = `${count} article${count !== 1 ? 's' : ''} found`;
}

// Show error message
function showError(message) {
    hideLoading();
    const container = document.getElementById('articles-container');
    container.style.display = 'block';
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <h2 class="empty-state-title">Error</h2>
            <p class="empty-state-text">${message}</p>
            <button class="sort-btn" onclick="fetchArticles()">Retry</button>
        </div>
    `;
}

// Sort articles
function sortArticles(sortType) {
    currentSort = sortType;
    currentPage = 1;
    
    // Update active button
    document.querySelectorAll('.sort-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`sort-${sortType}`).classList.add('active');
    
    // Sort
    if (sortType === 'newest') {
        filteredArticles.sort((a, b) => new Date(b.date || b.createdAt) - new Date(a.date || a.createdAt));
    } else if (sortType === 'oldest') {
        filteredArticles.sort((a, b) => new Date(a.date || a.createdAt) - new Date(b.date || b.createdAt));
    } else if (sortType === 'popular') {
        filteredArticles.sort((a, b) => (b.likes || 0) - (a.likes || 0));
    }
    
    renderArticles();
}

// Render articles
function renderArticles() {
    const container = document.getElementById('articles-container');
    
    if (filteredArticles.length === 0) {
        container.style.display = 'block';
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h2 class="empty-state-title">No articles found</h2>
                <p class="empty-state-text">Try adjusting your search or browse all articles.</p>
            </div>
        `;
        document.getElementById('pagination-controls').style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    
    // Pagination
    const totalPages = Math.ceil(filteredArticles.length / articlesPerPage);
    const startIndex = (currentPage - 1) * articlesPerPage;
    const endIndex = startIndex + articlesPerPage;
    const articlesToShow = filteredArticles.slice(startIndex, endIndex);
    
    container.innerHTML = articlesToShow.map(article => `
        <a href="view_article.html?id=${article.id}" class="article-link">
            <div class="article-card">
                <div class="article-header">
                    <div style="flex: 1;">
                        <h3 class="article-title">${escapeHtml(article.title)}</h3>
                        <p class="article-author">By ${escapeHtml(article.author || article.authorName || 'Unknown')}</p>
                    </div>
                </div>
                
                <p class="article-excerpt">${escapeHtml(article.excerpt || '')}</p>
                
                <div class="article-meta">
                    <span class="meta-item">📅 ${formatDate(article.date || article.createdAt)}</span>
                    <span class="meta-item">👁️ ${article.views || 0} views</span>
                    <span class="meta-item">❤️ ${article.likes || 0} likes</span>
                </div>
                
                <div class="article-tags">
                    ${article.tags && article.tags.length > 0 ? 
                        article.tags.map(tag => `
                            <span class="tag-badge" onclick="event.preventDefault(); filterByTag('${escapeHtml(tag)}')">${escapeHtml(tag)}</span>
                        `).join('') 
                        : ''}
                </div>
            </div>
        </a>
    `).join('');
    
    // Update pagination
    if (totalPages > 1) {
        document.getElementById('pagination-controls').style.display = 'flex';
        document.getElementById('page-indicator').textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prev-page-btn').disabled = currentPage === 1;
        document.getElementById('next-page-btn').disabled = currentPage === totalPages;
    } else {
        document.getElementById('pagination-controls').style.display = 'none';
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

// Filter by tag
function filterByTag(tag) {
    window.location.href = `articles.html?type=tag&tag=${encodeURIComponent(tag)}`;
}

// Pagination
function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        renderArticles();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredArticles.length / articlesPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderArticles();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}