import { protectRoute } from "./auth_guard.js";
// console.log("HOME SCRIPT EXECUTED", Date.now());


// Reducing the content length of the articles to include them in the containers ( To make preview )
function makePreview(text) {
    if (!text) return "";

    const sentences = text.split(/(?<=[.!?])\s+/);
    const preview = sentences.slice(0, 2).join(" ");

    return preview.length < text.length ? preview + "..." : preview;
}

// The page remembers the current page the user is on through the session storage
let currentPage = Number(sessionStorage.getItem("home_current_page")) || 1;
let totalPages = 1;

// generate or reuse session_id
let sessionId = sessionStorage.getItem("rec_session_id");
if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("rec_session_id", sessionId);
}

// This function is executed as soon as the page is loaded. This is responsible for requesting the recommended articles for the user based on the user vectors from the backend
let recommendationSessionId = sessionStorage.getItem("rec_session_id");

if (!recommendationSessionId) {
    recommendationSessionId = crypto.randomUUID();
    sessionStorage.setItem("rec_session_id", recommendationSessionId);
}
async function loadArticles() {
    const token = localStorage.getItem("auth_token");
    if (!token) return;

    const loader = document.getElementById("article-loader");
    const cards = document.querySelectorAll(".article-card");
    const prevBtn = document.getElementById("prev-page-btn");
    const nextBtn = document.getElementById("next-page-btn");
    const pageIndicator = document.getElementById("page-indicator");

    cards.forEach(card => (card.style.display = "none"));
    loader.style.display = "block";

    try {
        const response = await fetch(
            `http://localhost:8000/recommendations/?page=${currentPage}&page_size=5&session_id=${recommendationSessionId}`,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        if (!response.ok) throw new Error("Recommendation request failed");

        const data = await response.json();
        const articles = data.articles;
        totalPages = data.total_pages;

        articles.forEach((article, index) => {
            if (!cards[index]) return;

            const card = cards[index];
            const titleEl = card.querySelector(".article-title");
            const bodyEl = card.querySelector(".article-body");
            const metaEl = card.querySelector(".article-meta");
            const linkEl = card.closest(".article-link");

            titleEl.textContent = article.title;
            bodyEl.textContent = makePreview(article.content);
            metaEl.textContent = `By ${article.author_username}`;
            linkEl.href = `view_article.html?article_id=${article.article_id}`;

            linkEl.addEventListener("click", () => {
                sessionStorage.setItem("home_current_page", currentPage);
            });
        });

        cards.forEach(card => (card.style.display = "block"));

        pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage >= totalPages;

    } catch (error) {
        console.error(error);
    } finally {
        loader.style.display = "none";
    }
}


// Loading the trending tags from the backend and also creating the container to hold the trending tags and adding them in the trending tag section
async function loadTrendingTags() {
    const container = document.getElementById("trending-tags-container");
    container.innerHTML = "";

    try {
        const response = await fetch("http://localhost:8000/trending/tags");
        if (!response.ok) throw new Error("Failed to fetch trending tags");

        const tags = await response.json();

        tags.forEach(tag => {
            const a = document.createElement("a");
            a.className = "tag-btn text-decoration-none";
            a.textContent = tag.tag_name;
            a.href = `TrendingTag.html?tag_id=${tag.tag_id}`;
            container.appendChild(a);
        });
    } catch (error) {
        console.error(error);
    }
}

// Used to render the trending author tags. Backend returns the list of authors that is added into individual rectangles and loaded in the trending author section
async function loadTrendingAuthors() {
    const panel = document.getElementById("featured-writers-panel");

    try {
        const response = await fetch("http://localhost:8000/trending/authors");
        if (!response.ok) throw new Error("Failed to fetch trending authors");

        const authors = await response.json();

        const container = document.createElement("div");
        container.className = "d-flex flex-wrap gap-2 mt-2";

        authors.forEach(author => {
            const a = document.createElement("a");
            a.className = "tag-btn text-decoration-none";
            a.textContent = author.user_name;
            a.href = `trendingAuthor.html?author_id=${author.user_id}`;
            container.appendChild(a);
        });

        panel.appendChild(container);
    } catch (error) {
        console.error(error);
    }
}

// Adds all the event listeners once the page is loaded
document.addEventListener("DOMContentLoaded", async () => {
    const valid = await protectRoute();
    if (!valid) return;

    const prevButton = document.getElementById("prev-page-btn");
    const nextButton = document.getElementById("next-page-btn");
    const logoutButton = document.getElementById("dropdown-logout-desktop");
    const searchForm = document.getElementById("nav-search-form-desktop");


    // Both functions are responsible for changing the current page number in the session storage
    prevButton.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            sessionStorage.setItem("home_current_page", currentPage);
            loadArticles();
        }
    });

    nextButton.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            sessionStorage.setItem("home_current_page", currentPage);
            loadArticles();
        }
    });

    // Logs the user out
    logoutButton.addEventListener("click", () => {
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = "../pages/Authentication.html";
    });

    // Responsible the functioning of the search bar in the navbar section of the page
    searchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const query = document
            .getElementById("navbar-search-input-desktop")
            .value.trim();

        if (!query) return;

        window.location.href = `../pages/Search_article.html?q=${encodeURIComponent(query)}`;
    });

    loadTrendingTags();
    loadTrendingAuthors();
    loadArticles();
});
