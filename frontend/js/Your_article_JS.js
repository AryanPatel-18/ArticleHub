import { protectRoute } from "./auth_guard.js";

const AUTH_TOKEN = localStorage.getItem("auth_token");

let articles = [];
let currentPage = 1;
const pageSize = 5;

document.addEventListener("DOMContentLoaded", async function () {
    const isValid = await protectRoute();
    if (!isValid) return;

    if (document.getElementById("interaction-graph")) {
        loadInteractionGraph();
    }

    if (document.getElementById("total-articles")) {
        loadArticleStats();
    }

    if (document.getElementById("articles-container")) {
        fetchUserArticles();
    }
});

async function fetchUserArticles(type = "newest", page = 1) {
    try {

        if (document.querySelector(".sort-btn")) {
            if (type === "newest") {
                setActiveSort("sort-newest");
            } else if (type === "oldest") {
                setActiveSort("sort-oldest");
            } else {
                setActiveSort("sort-popular");
            }
        }

        const response = await fetch(
            `http://localhost:8000/articles/user/me?sort=${type}&page=${page}&page_size=${pageSize}`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${AUTH_TOKEN}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Failed to fetch articles");
        }

        const data = await response.json();

        articles = data.articles || [];
        currentPage = data.page;

        renderArticles();
        updatePagination(data.total_pages);

    } catch (error) {
        console.error("Error fetching articles:", error);
        showError("Failed to load your articles.");
    }
}

function renderArticles() {
    const container = document.getElementById("articles-container");
    if (!container) return;

    if (articles.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h2>No articles yet</h2>
                <p>Create your first article.</p>
                <a href="Create.html" class="create-btn">Create Article</a>
            </div>
        `;
        return;
    }

    container.innerHTML = articles.map(article => `
        <div class="article-card card mb-3 p-3">
            <h3 class="card-title">${escapeHtml(article.title)}</h3>

            <p class="card-text">
                ${DOMPurify.sanitize(article.content.slice(0, 200))}...
            </p>

            <small class="text-meta">
                Created at: ${formatDate(article.created_at)}
            </small>

            <div class="mt-3 d-flex gap-2">
                <a href="view_article.html?article_id=${article.article_id}" 
                class="btn btn-sm btn-primary">
                    View
                </a>

                <a href="Edit.html?id=${article.article_id}" 
                class="btn btn-sm btn-warning">
                    Edit
                </a>

                <button class="btn btn-sm btn-danger"
                        onclick="deleteArticle(${article.article_id})">
                    Delete
                </button>
            </div>
        </div>
    `).join("");
}

function updatePagination(totalPages) {
    const pagination = document.getElementById("pagination-controls");
    if (!pagination) return;

    if (totalPages <= 1) {
        pagination.style.display = "none";
        return;
    }

    pagination.style.display = "flex";

    const indicator = document.getElementById("page-indicator");
    if (indicator) {
        indicator.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    const prevBtn = document.getElementById("prev-page-btn");
    const nextBtn = document.getElementById("next-page-btn");

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages;
}

function prevPage() {
    if (currentPage > 1) {
        fetchUserArticles("newest", currentPage - 1);
    }
}

function nextPage() {
    fetchUserArticles("newest", currentPage + 1);
}

function showError(message) {
    const container = document.getElementById("articles-container");
    if (container) {
        container.innerHTML = `<p>${message}</p>`;
    }
}

function escapeHtml(text) {
    return text.replace(/[&<>"']/g, m => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[m]);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

async function loadArticleStats() {
    try {
        const response = await fetch("http://localhost:8000/articles/stats/me", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${AUTH_TOKEN}`
            }
        });

        if (!response.ok) {
            throw new Error("Failed to fetch article stats");
        }

        const data = await response.json();

        const map = {
            "total-articles": data.total_articles,
            "published-count": data.published_articles,
            "total-views": data.total_views,
            "total-likes": data.total_likes,
            "total-saves": data.total_saves
        };

        Object.entries(map).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });

    } catch (error) {
        console.error("Error loading article stats:", error);
    }
}

function setActiveSort(buttonId) {
    document.querySelectorAll(".sort-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    const target = document.getElementById(buttonId);
    if (target) {
        target.classList.add("active");
    }
}

async function loadInteractionGraph() {
    try {
        const response = await fetch(
            "http://localhost:8000/analytics/my-articles/interactions-graph",
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${AUTH_TOKEN}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Failed to fetch interaction graph");
        }

        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);

        const img = document.getElementById("interaction-graph");
        if (img) img.src = imageUrl;

    } catch (error) {
        console.error("Error loading interaction graph:", error);

        const container = document.querySelector(".graph-container");
        if (container) {
            container.innerHTML = `<p class="graph-error">Unable to load graph.</p>`;
        }
    }
}

window.fetchUserArticles = fetchUserArticles;
window.prevPage = prevPage;
window.nextPage = nextPage;
// window.deleteArticle = deleteArticle;
