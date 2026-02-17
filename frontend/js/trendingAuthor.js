// File renders all the articles for the author that was selected by the user
import { protectRoute } from "./auth_guard.js";

const baseURL = "http://127.0.0.1:8000";

let currentPage = Number(sessionStorage.getItem("author_current_page")) || 1;
let totalPages = 1;
let currentSort = sessionStorage.getItem("trending_sort") || "newest";
let authorId = null;
let articlesCache = [];

// DOM
const articlesContainer = document.getElementById("articles-container");
const loadingState = document.getElementById("loading-state");
const resultsCount = document.getElementById("results-count");
const pageIndicator = document.getElementById("page-indicator");
const prevBtn = document.getElementById("prev-page-btn");
const nextBtn = document.getElementById("next-page-btn");
const pageTitle = document.getElementById("page-title");


document.addEventListener("DOMContentLoaded", async () => {
    const isValid = await protectRoute();
    if (!isValid) return;

    const params = new URLSearchParams(window.location.search);

    authorId = params.get("author_id");

    const pageFromURL = params.get("page");
    if (pageFromURL) {
        currentPage = Number(pageFromURL);
        sessionStorage.setItem("author_current_page", currentPage);
    }

    const storedSort = sessionStorage.getItem("author_sort");
    if (storedSort) currentSort = storedSort;

    document.getElementById(`sort-${currentSort}`)?.classList.add("active");

    const backBtn = document.getElementById("back-btn");
    if (backBtn) {
        backBtn.addEventListener("click", () => {
            sessionStorage.removeItem("author_current_page");
            sessionStorage.removeItem("author_sort");
        });
    }


    fetchArticles();
});


// Main function that fetches all the articles from the backend
async function fetchArticles() {
    showLoading();

    try {
        const response = await fetch(
            `${baseURL}/articles/get/by-author?author_id=${authorId}&page=${currentPage}`
        );

        if (!response.ok) throw new Error("Fetch failed");

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

// Adding the data into their separate containers
function renderArticles(articles) {
    articlesContainer.innerHTML = "";

    if (!articles.length) {
        articlesContainer.innerHTML = "<p>No articles found.</p>";
        return;
    }

    articles.forEach(article => {
        const card = document.createElement("div");
        card.className = "article-card";

        const link = document.createElement("a");
        link.href = `view_article.html?article_id=${article.article_id}`;
        link.className = "read-more";
        link.textContent = "Read more →";

        link.addEventListener("click", () => {
            sessionStorage.setItem(
                "article_referrer",
                `trendingAuthor.html?author_id=${authorId}&page=${currentPage}`
            );
        });

        card.innerHTML = `
            <h3 class="article-title">${article.title}</h3>
            <p class="article-content">
                ${article.content.substring(0, 200)}...
            </p>
            <p class="article-meta">
                Created: ${new Date(article.created_at).toLocaleDateString()}
            </p>
        `;

        card.appendChild(link);
        articlesContainer.appendChild(card);
    });
}

// this decides the sorting types and updates the active buttons according to the current sorting type
function sortArticles(type) {
    currentSort = type;
    sessionStorage.setItem("author_sort", currentSort);

    document.querySelectorAll(".sort-btn").forEach(btn =>
        btn.classList.remove("active")
    );

    document.getElementById(`sort-${type}`).classList.add("active");

    applySorting();
}

// Actually sorts the functions based on the values
function applySorting() {
    let sorted = [...articlesCache];

    if (currentSort === "newest") {
        sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (currentSort === "oldest") {
        sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else {
        sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    renderArticles(sorted);
}

// Functions for pagination
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        sessionStorage.setItem("author_current_page", currentPage);
        fetchArticles();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        sessionStorage.setItem("author_current_page", currentPage);
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

// Loader functions
function showLoading() {
    loadingState.style.display = "block";
    articlesContainer.style.display = "none";
}

function hideLoading() {
    loadingState.style.display = "none";
    articlesContainer.style.display = "grid";
}


window.sortArticles = sortArticles;
window.nextPage = nextPage;
window.prevPage = prevPage;