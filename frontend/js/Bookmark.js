// This file is responsible for the rendering of saved articles of the user
import { protectRoute } from "./auth_guard.js";

// default variables
const API_BASE_URL = "http://127.0.0.1:8000";
let currentPage = 1;
let totalPages = 1;
let currentSort = "newest";
let articlesCache = [];

// Load on page start
document.addEventListener("DOMContentLoaded", async () => {
    const isValid = await protectRoute();

    if (!isValid) return;

    fetchBookmarkedArticles();
});

// The main function that fetches the saved articles from the backend, here it would send the auth token through the header which would be used to get the user id
async function fetchBookmarkedArticles() {
    showLoading(true);

    try {
        const token = localStorage.getItem("auth_token");

        const response = await fetch(
            `${API_BASE_URL}/articles/get/saved?page=${currentPage}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Failed to load bookmarks");
        }

        const data = await response.json();

        articlesCache = data.articles;
        totalPages = data.total_pages;

        document.getElementById("results-count").textContent =
            `Showing ${data.articles.length} of ${data.total_results} saved articles`;

        applySorting();
        updatePaginationUI();

    } catch (error) {
        console.error("Error:", error);
        alert("Could not load bookmarked articles.");
        // window.location.href = "Home.html"
    } finally {
        showLoading(false);
    }
}

// After the request has been sent this function is responsible for adding the data into the container that are created in the html file
function renderArticles(articles) {
    const container = document.getElementById("articles-container");
    container.innerHTML = "";

    if (articles.length === 0) {
        container.innerHTML = "<p>No saved articles found.</p>";
        return;
    }

    articles.forEach(article => {
        const articleDiv = document.createElement("div");
        articleDiv.className = "article-card";

        articleDiv.innerHTML = `
            <a href="view_article.html?article_id=${article.article_id}" class="article-link">
                <h2 class="article-title">${article.title}</h2>
                <p class="article-meta">
                    By ${article.author_username} • ${formatDate(article.created_at)} • ❤️ ${article.likes}
                </p>
                <p class="article-preview">
                    ${article.content.substring(0, 200)}...
                </p>
            </a>
        `;

        container.appendChild(articleDiv);
    });

    container.style.display = "block";
}


// This file changes the sort variable and also updates the active button from the button list in the sort container
function sortArticles(type) {
    currentSort = type;

    document.querySelectorAll(".sort-btn").forEach(btn => {
        btn.classList.remove("active");
    });
    document.getElementById(`sort-${type}`).classList.add("active");

    applySorting();
}

// Actually responsible sorting the articles based on the type
function applySorting() {
    let sorted = [...articlesCache];

    if (currentSort === "newest") {
        sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (currentSort === "oldest") {
        sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (currentSort === "popular") {
        sorted.sort((a, b) => b.likes - a.likes);
    }

    renderArticles(sorted);
}


// Both functions are responsible for the functioning of the next and prev button
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        fetchBookmarkedArticles();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        fetchBookmarkedArticles();
    }
}

// Updating the prev and the next buttons as well as the page number at the bottom of the page after changing the page
function updatePaginationUI() {
    document.getElementById("page-indicator").textContent =
        `Page ${currentPage} of ${totalPages}`;

    document.getElementById("prev-page-btn").disabled = currentPage === 1;
    document.getElementById("next-page-btn").disabled = currentPage === totalPages;

    document.getElementById("pagination-controls").style.display =
        totalPages > 1 ? "flex" : "none";
}


function showLoading(isLoading) {
    document.getElementById("loading-state").style.display =
        isLoading ? "flex" : "none";

    document.getElementById("articles-container").style.display =
        isLoading ? "none" : "block";
}

function formatDate(dateString) {
    const d = new Date(dateString);
    return d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric"
    });
}
