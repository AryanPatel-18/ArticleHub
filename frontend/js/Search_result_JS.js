const API_BASE_URL = "http://127.0.0.1:8000";
const AUTH_TOKEN = localStorage.getItem("auth_token");

let allArticles = [];
let currentSort = "newest";

document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q");

    if (!query) {
        showError("No search query provided.");
        return;
    }

    fetchSearchResults(query);
});

async function fetchSearchResults(query) {
    if (!AUTH_TOKEN) {
        console.error("Auth token missing");
        return;
    }

    showLoading();

    try {
        const response = await fetch(
            `${API_BASE_URL}/search?q=${encodeURIComponent(query)}`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${AUTH_TOKEN}`,
                    "Content-Type": "application/json"
                }
            }
        );

        if (!response.ok) {
            throw new Error("Search request failed");
        }

        const data = await response.json();
        allArticles = data.results || [];

        hideLoading();
        sortArticles("newest");

    } catch (error) {
        console.error("Search failed:", error);
        showError("Failed to load search results.");
    }
}

/* ================= UI STATE ================= */

function showLoading() {
    document.getElementById("loading-state").style.display = "block";
    document.getElementById("articles-container").style.display = "none";
}

function hideLoading() {
    document.getElementById("loading-state").style.display = "none";
    document.getElementById("articles-container").style.display = "flex";
}

function showError(message) {
    hideLoading();
    const container = document.getElementById("articles-container");
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <h2 class="empty-state-title">Error</h2>
            <p class="empty-state-text">${message}</p>
        </div>
    `;
}

/* ================= SORTING ================= */

function sortArticles(sortType) {
    currentSort = sortType;

    document.querySelectorAll(".sort-btn").forEach(btn =>
        btn.classList.remove("active")
    );
    document.getElementById(`sort-${sortType}`).classList.add("active");

    if (sortType === "relevance") {
        // 🔥 Sort by backend-provided relevance score
        allArticles.sort((a, b) =>
            (b.score || 0) - (a.score || 0)
        );
    }
    else if (sortType === "newest") {
        allArticles.sort((a, b) =>
            new Date(b.created_at) - new Date(a.created_at)
        );
    }
    else if (sortType === "oldest") {
        allArticles.sort((a, b) =>
            new Date(a.created_at) - new Date(b.created_at)
        );
    }
    else if (sortType === "popular") {
        allArticles.sort((a, b) =>
            (b.likes || 0) - (a.likes || 0)
        );
    }

    renderArticles();
}


/* ================= RENDER ================= */

function renderArticles() {
    const container = document.getElementById("articles-container");

    if (!allArticles.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h2 class="empty-state-title">No results</h2>
                <p class="empty-state-text">No articles matched your search.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = allArticles.map(article => {
        // Create a short preview instead of dumping full content
        const preview = article.content
            ? escapeHtml(article.content.substring(0, 200)) + "..."
            : "";

        return `
            <a href="view_article.html?article_id=${article.article_id}" class="article-link">
                <div class="article-card p-3 mb-3">
                    <h3 class="article-title">${escapeHtml(article.title)}</h3>

                    <p class="article-excerpt">
                        ${preview}
                    </p>

                    <div class="article-meta">
                        <span>📅 ${formatDate(article.created_at)}</span>
                        <span> ❤️ ${article.likes || 0}</span>
                        <span> 🔍 ${article.score.toFixed(2)}</span>
                    </div>
                </div>
            </a>
        `;
    }).join("");
}


/* ================= HELPERS ================= */

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/[&<>"']/g, m => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[m]);
}
