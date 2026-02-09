const baseURL = "http://127.0.0.1:8000"; // change if deployed

let currentPage = Number(sessionStorage.getItem("trending_current_page")) || 1;

let totalPages = 1;
let currentSort = sessionStorage.getItem("trending_sort") || "newest";
let tagId = null;
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

    tagId = params.get("tag_id");

    const pageFromURL = params.get("page");
    if (pageFromURL) {
        currentPage = Number(pageFromURL);
        sessionStorage.setItem("trending_current_page", currentPage);
    }

    const storedSort = sessionStorage.getItem("trending_sort");
    if (storedSort) currentSort = storedSort;

    document.getElementById(`sort-${currentSort}`)?.classList.add("active");

    const backBtn = document.getElementById("back-btn");
    if (backBtn) {
        backBtn.addEventListener("click", () => {
            sessionStorage.removeItem("trending_current_page");
            sessionStorage.removeItem("trending_sort");
        });
    }

    fetchArticles();
});



/* -----------------------------
   FETCH ARTICLES
----------------------------- */
async function fetchArticles() {
    showLoading();

    try {
        const response = await fetch(
            `${baseURL}/articles/get/by-tag?tag_id=${tagId}&page=${currentPage}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch articles");
        }

        const data = await response.json();

        pageTitle.textContent = data.tag_name;
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

    if (articles.length === 0) {
        articlesContainer.innerHTML = "<p>No articles found.</p>";
        return;
    }

    articles.forEach(article => {
        const articleCard = document.createElement("div");
        articleCard.className = "article-card";

        const link = document.createElement("a");
        link.href = `view_article.html?article_id=${article.article_id}`;
        link.className = "read-more";
        link.textContent = "Read more →";

        // 🔑 SAVE REFERRER
        link.addEventListener("click", () => {
            sessionStorage.setItem(
                "article_referrer",
                `TrendingTag.html?tag_id=${tagId}&page=${currentPage}`
            );
        });

        articleCard.innerHTML = `
            <h3 class="article-title">${article.title}</h3>
            <p class="article-content">
                ${article.content.substring(0, 200)}...
            </p>
            <p class="article-meta">
                Created: ${new Date(article.created_at).toLocaleDateString()}
            </p>
        `;

        articleCard.appendChild(link);
        articlesContainer.appendChild(articleCard);
    });
}


/* -----------------------------
   SORTING
----------------------------- */
function sortArticles(type) {
    currentSort = type;
    sessionStorage.setItem("trending_sort", currentSort);

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
    } else if (currentSort === "oldest") {
        sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (currentSort === "popular") {
        // backend does NOT return likes yet
        // fallback = newest
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
        sessionStorage.setItem("trending_current_page", currentPage);
        fetchArticles();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        sessionStorage.setItem("trending_current_page", currentPage);
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

function clearTrendingState() {
    sessionStorage.removeItem("trending_current_page");
}
