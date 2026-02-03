import { protectRoute } from "./auth_guard.js";


function makePreview(text) {
    if (!text) return "";

    const sentences = text.split(/(?<=[.!?])\s+/);
    const preview = sentences.slice(0, 2).join(" ");

    return preview.length < text.length ? preview + "..." : preview;
}

let currentPage = 1;
let totalPages = 1;

// generate or reuse session_id for this page load
let sessionId = sessionStorage.getItem("rec_session_id");
if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem("rec_session_id", sessionId);
}

async function loadArticles() {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
        console.error("No user_id in localStorage");
        return;
    }

    const loader = document.getElementById("article-loader");
    const cards = document.querySelectorAll(".article-card");
    const prevBtn = document.getElementById("prev-page-btn");
    const nextBtn = document.getElementById("next-page-btn");
    const pageIndicator = document.getElementById("page-indicator");

    // hide cards initially
    cards.forEach(card => {
        card.style.display = "none";
    });

    // show spinner
    loader.style.display = "block";

    try {
        const response = await fetch(
            `http://localhost:8000/recommendations/?user_id=${userId}&session_id=${sessionStorage.getItem("rec_session_id")}&page=${currentPage}&page_size=5`
        );

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
        });

        // show cards after data is loaded
        cards.forEach(card => {
            card.style.display = "block";
        });

        // update page indicator
        pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;

        // disable prev on page 1
        prevBtn.disabled = currentPage === 1;

        // disable next on last page
        nextBtn.disabled = currentPage >= totalPages;

    } catch (error) {
        console.error("Failed to load articles:", error);
    } finally {
        // hide spinner
        loader.style.display = "none";
    }
}

const prevButton = document.getElementById("prev-page-btn");
const nextButton = document.getElementById("next-page-btn");

prevButton.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadArticles();
    }
});

nextButton.addEventListener("click", () => {
    if (currentPage < totalPages) {
        currentPage++;
        loadArticles();
    }
});


document.addEventListener("DOMContentLoaded", () => {
    protectRoute();
    loadArticles();
});

const logoutButton = document.getElementById("dropdown-logout-desktop")

logoutButton.addEventListener('click', () => {
    localStorage.clear()
    sessionStorage.clear()
    window.location.href = "../pages/Authentication.html";
})

// const logoutLink = document.getElementById("dropdown-logout-desktop")
// logoutLink.addEventListener('click',logout())