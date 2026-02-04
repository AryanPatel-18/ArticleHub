const baseURL = "http://127.0.0.1:8000"; // adjust if deployed

let currentPage = 1;
let totalPages = 1;
let currentSort = "newest";
let authorId = null;
let articlesCache = [];

// DOM elements
const articlesContainer = document.getElementById("articles-container");
const loadingState = document.getElementById("loading-state");
const resultsCount = document.getElementById("results-count");
const pageIndicator = document.getElementById("page-indicator");
const prevBtn = document.getElementById("prev-page-btn");
const nextBtn = document.getElementById("next-page-btn");
const pageTitle = document.getElementById("page-title");

/* -----------------------------
   INIT
----------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    authorId = params.get("author_id");

    if (!authorId) {
        pageTitle.textContent = "Invalid Author";
        return;
    }

    pageTitle.textContent = `Author #${authorId}`;
    fetchArticles();
});

/* -----------------------------
   FETCH ARTICLES
----------------------------- */
async function fetchArticles() {
    showLoading();

    try {
        const response = await fetch(
            `${baseURL}/articles/get/by-author?author_id=${authorId}&page=${currentPage}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch articles by author");
        }

        const data = await response.json();

        pageTitle.textContent = data.author_name;
        articlesCache = data.articles;
        totalPages = data.total_pages;

        resultsCount.textContent = `${data.total_articles} articles found`;

        applySorting();
        updatePaginationUI(data.page, data.total_pages);

    } catch (err) {
        console.error(err);
        articlesContainer.innerHTML = "<p>Error loading articles.</p>";
    } finally {
        hideLoading();
    }
}

/* -----------------------------
   RENDER ARTICLES
----------------------------- */
function renderArticles(articles) {
    articlesContainer.innerHTML = "";

    if (!articles || articles.length === 0) {
        articlesContainer.innerHTML = "<p>No articles found.</p>";
        return;
    }

    articles.forEach(article => {
        const articleCard = document.createElement("div");
        articleCard.className = "article-card";

        articleCard.innerHTML = `
            <h3 class="article-title">${article.title}</h3>
            <p class="article-content">
                ${article.content.substring(0, 200)}...
            </p>
            <p class="article-meta">
                Created: ${new Date(article.created_at).toLocaleDateString()}
            </p>
            <a href="view_article.html?article_id=${article.article_id}" class="read-more">
                Read more →
            </a>
        `;

        articlesContainer.appendChild(articleCard);
    });
}

/* -----------------------------
   SORTING
----------------------------- */
function sortArticles(type) {
    currentSort = type;

    document.querySelectorAll(".sort-btn").forEach(btn =>
        btn.classList.remove("active")
    );
    document.getElementById(`sort-${type}`).classList.add("active");

    applySorting();
}

function applySorting() {
    let sorted = [...articlesCache];

    if (currentSort === "newest") {
        sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } 
    else if (currentSort === "oldest") {
        sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } 
    else if (currentSort === "popular") {
        // Backend does NOT return like_count yet
        // Fallback to newest
        sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    renderArticles(sorted);
}

/* -----------------------------
   PAGINATION
----------------------------- */
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        fetchArticles();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        fetchArticles();
    }
}

function updatePaginationUI(page, total) {
    pageIndicator.textContent = `Page ${page} of ${total}`;

    prevBtn.disabled = page <= 1;
    nextBtn.disabled = page >= total;

    document.getElementById("pagination-controls").style.display =
        total > 1 ? "flex" : "none";
}

/* -----------------------------
   LOADING STATE
----------------------------- */
function showLoading() {
    loadingState.style.display = "block";
    articlesContainer.style.display = "none";
}

function hideLoading() {
    loadingState.style.display = "none";
    articlesContainer.style.display = "grid";
}
