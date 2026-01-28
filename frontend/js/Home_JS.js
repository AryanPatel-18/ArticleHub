import { protectRoute } from "./auth_guard.js";


function makePreview(text) {
    if (!text) return "";

    const sentences = text.split(/(?<=[.!?])\s+/);
    const preview = sentences.slice(0, 2).join(" ");

    return preview.length < text.length ? preview + "..." : preview;
}

async function loadArticles() {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
        console.error("No user_id in localStorage");
        return;
    }

    const loader = document.getElementById("article-loader");
    const cards = document.querySelectorAll(".article-card");

    // hide cards initially
    cards.forEach(card => {
        card.style.display = "none";
    });

    // show spinner
    loader.style.display = "block";

    try {
        const response = await fetch(`http://localhost:8000/recommendations/${userId}`);
        const articles = await response.json();

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

            // 🔴 IMPORTANT PART
            linkEl.href = `view_article.html?article_id=${article.article_id}`;
        });

        // show cards after data is loaded
        cards.forEach(card => {
            card.style.display = "block";
        });

    } catch (error) {
        console.error("Failed to load articles:", error);
    } finally {
        // hide spinner
        loader.style.display = "none";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    protectRoute();
    loadArticles();
});

