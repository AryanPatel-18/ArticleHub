let article_Id;

let liked = false;
let saved = false;

let likeButton;
let saveButton;

document.addEventListener("DOMContentLoaded", () => {
    likeButton = document.getElementById("likeButton");
    saveButton = document.getElementById("saveButton");

    setBackNavigation();
    loadArticle();
    loadInteractionStatus();
});

async function loadArticle() {
    const loader = document.getElementById("article-loader");
    const container = document.getElementById("article-container");

    const params = new URLSearchParams(window.location.search);
    const articleId = params.get("article_id");
    article_Id = articleId;

    if (!articleId) {
        console.error("No article_id in URL");
        return;
    }

    loader.style.display = "block";
    container.style.display = "none";

    try {
        const response = await fetch(`http://localhost:8000/articles/${articleId}`);
        const article = await response.json();

        document.getElementById("article-title").textContent = article.title;

        document.getElementById("author-name").textContent = article.author_username;
        document.getElementById("author-initial").textContent =
            article.author_username.charAt(0).toUpperCase();

        const date = new Date(article.created_at);
        document.getElementById("article-date").textContent =
            date.toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric"
            });

        document.getElementById("article-content").textContent = article.content;

        const tagsList = document.getElementById("tags-list");
        tagsList.innerHTML = "";

        article.tags.forEach(tag => {
            const span = document.createElement("span");
            span.className = "tag-btn";
            span.textContent = tag;
            tagsList.appendChild(span);
        });

        loader.style.display = "none";
        container.style.display = "block";

        setTimeout(() => {
            logArticle(articleId, "view");
        }, 2000);

    } catch (error) {
        console.error("Failed to load article:", error);
        loader.style.display = "none";
    }
}

function logArticle(articleId, type) {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    fetch(`http://localhost:8000/interactions/?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            article_id: articleId,
            interaction_type: type
        })
    }).catch(() => {});
}

async function loadInteractionStatus() {
    const userId = localStorage.getItem("user_id");

    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get("article_id");

    if (!userId || !articleId) {
        console.error("Missing user_id or article_id");
        return;
    }

    try {
        const response = await fetch(
            `http://localhost:8000/interactions/status?user_id=${userId}&article_id=${articleId}`
        );

        if (!response.ok) return;

        const data = await response.json();

        liked = data.liked;
        saved = data.saved;

        if (liked) {
            likeButton.setAttribute("fill", "currentColor");
        } else {
            likeButton.setAttribute("fill", "none");
        }

        if (saved) {
            saveButton.setAttribute("fill", "currentColor");
        } else {
            saveButton.setAttribute("fill", "none");
        }

    } catch (error) {
        console.error("Error loading interaction status:", error);
    }
}

async function toggleInteraction(type) {
    const token = localStorage.getItem("auth_token");
    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get("article_id");

    if (!token || !articleId) {
        console.error("Missing auth token or article_id");
        return;
    }

    try {
        const response = await fetch(
            "http://localhost:8000/interactions/toggle",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    article_id: parseInt(articleId),
                    interaction_type: type
                })
            }
        );

        if (!response.ok) {
            console.error("Toggle interaction failed:", response.status);
            return;
        }

        const data = await response.json();

        if (data.interaction_type === "like") {
            likeButton.setAttribute(
                "fill",
                data.active ? "currentColor" : "none"
            );
        } else {
            saveButton.setAttribute(
                "fill",
                data.active ? "currentColor" : "none"
            );
        }

    } catch (error) {
        console.error("Error calling toggle endpoint:", error);
    }
}


function toggleLike() {
    toggleInteraction("like");
}

function toggleBookmark() {
    toggleInteraction("save");
}

function setBackNavigation() {
    const backBtn = document.getElementById("back-to-home-btn");
    const referrer = sessionStorage.getItem("article_referrer");

    if (!referrer) {
        backBtn.href = "home.html";
        backBtn.textContent = "← Back to Home";
        return;
    }

    backBtn.href = referrer;

    if (referrer.includes("TrendingTag")) {
        backBtn.textContent = "← Back to Trending Tag";
    }
    else if (referrer.includes("trendingAuthor")) {
        backBtn.textContent = "← Back to Author Articles";
    }
    else {
        backBtn.textContent = "← Back";
    }

    sessionStorage.removeItem("article_referrer");
}
