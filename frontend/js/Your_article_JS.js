const AUTH_TOKEN = localStorage.getItem("auth_token");

let articles = [];
let currentPage = 1;
const pageSize = 5;

document.addEventListener("DOMContentLoaded", function () {
    loadArticleStats();
    fetchUserArticles();
});

async function fetchUserArticles(type="newest",page = 1) {
    try {

        if(type == "newest"){
            setActiveSort("sort-newest")
        }else if(type == "oldest"){
            setActiveSort("sort-oldest")
        }else{
            setActiveSort("sort-popular")
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
                ${escapeHtml(article.content.slice(0, 200))}...
            </p>

            <small class="text-muted">
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

    if (totalPages <= 1) {
        pagination.style.display = "none";
        return;
    }

    pagination.style.display = "flex";
    document.getElementById("page-indicator").textContent =
        `Page ${currentPage} of ${totalPages}`;

    document.getElementById("prev-page-btn").disabled = currentPage === 1;
    document.getElementById("next-page-btn").disabled = currentPage === totalPages;
}

function prevPage() {
    if (currentPage > 1) {
        fetchUserArticles("newest",currentPage - 1);
    }
}

function nextPage() {
    fetchUserArticles("newest",currentPage + 1);
}

function showError(message) {
    const container = document.getElementById("articles-container");
    container.innerHTML = `<p>${message}</p>`;
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

        document.getElementById("total-articles").textContent = data.total_articles;
        document.getElementById("published-count").textContent = data.published_articles;
        document.getElementById("total-views").textContent = data.total_views;
        document.getElementById("total-likes").textContent = data.total_likes;
        document.getElementById("total-saves").textContent = data.total_saves;

    } catch (error) {
        console.error("Error loading article stats:", error);
    }
}

function setActiveSort(buttonId) {
    // remove "active" from all sort buttons
    document.querySelectorAll(".sort-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    // add "active" to the clicked one
    document.getElementById(buttonId).classList.add("active");
}

async function deleteArticle(articleId) {
    const confirmed = await showDeleteConfirm();
    if (!confirmed) return;

    try {
        const response = await fetch(
            `http://localhost:8000/articles/delete/${articleId}`,
            {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${AUTH_TOKEN}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Failed to delete article");
        }

        const data = await response.json();
        // alert(data.message || "Article deleted");
        showDeleteToast("Article Deleted")
        // reload articles after deletion
        fetchUserArticles();
        loadArticleStats();

    } catch (error) {
        console.error("Error deleting article:", error);
        alert("Failed to delete article. Please try again.");
    }
}

function showDeleteToast(message) {
    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");
    toast.className = "toast-message";
    toast.textContent = message;

    container.appendChild(toast);

    // remove after 2 seconds
    setTimeout(() => {
        toast.remove();
    }, 2000);
}

function showDeleteConfirm() {
    return new Promise((resolve) => {
        const overlay = document.getElementById("confirm-overlay");
        const yesBtn = document.getElementById("confirm-yes");
        const noBtn = document.getElementById("confirm-no");

        overlay.classList.remove("hidden");

        function cleanup(result) {
            overlay.classList.add("hidden");
            yesBtn.removeEventListener("click", yesHandler);
            noBtn.removeEventListener("click", noHandler);
            resolve(result);
        }

        function yesHandler() {
            cleanup(true);
        }

        function noHandler() {
            cleanup(false);
        }

        yesBtn.addEventListener("click", yesHandler);
        noBtn.addEventListener("click", noHandler);
    });
}
