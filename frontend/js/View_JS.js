// import { protectRoute } from "./auth_guard.js";


document.addEventListener("DOMContentLoaded", () => {
    loadArticle();
    loadInteractionStatus();
});

let article_Id;

async function loadArticle() {
    const loader = document.getElementById("article-loader");
    const container = document.getElementById("article-container");

    const params = new URLSearchParams(window.location.search);
    const articleId = params.get("article_id");
    article_Id = articleId

    if (!articleId) {
        console.error("No article_id in URL");
        return;
    }

    // show loader, hide content
    loader.style.display = "block";
    container.style.display = "none";

    try {
        const response = await fetch(`http://localhost:8000/articles/${articleId}`);
        const article = await response.json();

        // fill title
        document.getElementById("article-title").textContent = article.title;

        // fill author
        document.getElementById("author-name").textContent = article.author_username;
        document.getElementById("author-initial").textContent =
            article.author_username.charAt(0).toUpperCase();

        // fill date
        const date = new Date(article.created_at);
        document.getElementById("article-date").textContent =
            date.toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric"
            });

        // fill content
        document.getElementById("article-content").textContent = article.content;

        // fill tags
        const tagsList = document.getElementById("tags-list");
        tagsList.innerHTML = "";

        article.tags.forEach(tag => {
            const span = document.createElement("span");
            span.className = "tag";
            span.textContent = tag;
            tagsList.appendChild(span);
        });

        // hide loader, show content
        loader.style.display = "none";
        container.style.display = "block";

        setTimeout(() => {
            logArticle(articleId,"view")
        }, 2000);

    } catch (error) {
        console.error("Failed to load article:", error);
        loader.style.display = "none";
    }
}


function logArticle(articleId,type) {
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

let liked = false
let saved = false
const likeButton = document.getElementById("likeButton")
const saveButton = document.getElementById("saveButton")

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

        if (!response.ok) {
            console.error("Failed to fetch interaction status");
            return;
        }

        const data = await response.json();

        liked = data.liked;
        saved = data.saved;

        if(liked){
            likeButton.setAttribute("fill","currentColor")
        }else{
            likeButton.setAttribute('fill','none')
        }

        if(saved){
            saveButton.setAttribute("fill","currentColor")
        }else{
            saveButton.setAttribute('fill','none')
        }

    } catch (error) {
        console.error("Error loading interaction status:", error);
    }
}

async function toggleInteraction(type) {
    const userId = localStorage.getItem("user_id");
    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get("article_id");

    
    if (!userId || !articleId) {
        console.error("Missing user_id or article_id");
        return;
    }

    try {
        const response = await fetch(
            `http://localhost:8000/interactions/toggle?user_id=${userId}`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    article_id: parseInt(articleId),
                    interaction_type: type
                })
            }
        );

        if (!response.ok) {
            console.error("Toggle request failed");
            return;
        }

        const data = await response.json();
        // console.log(data)
        if(data.interaction_type == 'like'){
            if(data.active){
                likeButton.setAttribute("fill","currentColor")
            }else{
                likeButton.setAttribute("fill","none")
            }
        }else{
            if(data.active){
                saveButton.setAttribute("fill","currentColor")
            }else{
                saveButton.setAttribute("fill","none")
            }
        }

    } catch (error) {
        console.error("Error calling toggle endpoint:", error);
    }
}

function toggleLike(){
    toggleInteraction('like')
}

function toggleBookmark(){
    toggleInteraction('save')
}