const baseURL = "http://localhost:8000";

let tags = [];
let articleId = null;

// Word Counter
const contentArea = document.getElementById('article-content');
const wordCounter = document.getElementById('word-counter');
const titleInput = document.getElementById("article-title");

let articleData = {
    title: '',
    content: '',
    tags: []
};

/* -------------------------------
   READ ARTICLE ID FROM URL
-------------------------------- */
function getArticleIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
}

/* -------------------------------
   LOAD ARTICLE FROM BACKEND
-------------------------------- */
async function loadArticle() {
    articleId = getArticleIdFromURL();

    if (!articleId) {
        alert("No article ID provided.");
        return;
    }

    try {
        const response = await fetch(`${baseURL}/articles/${articleId}`);

        if (!response.ok) {
            throw new Error("Failed to fetch article");
        }

        const data = await response.json();

        // Populate title & content
        titleInput.value = data.title;
        contentArea.innerHTML = data.content;

        articleData.title = data.title;
        articleData.content = data.content;

        // ✅ Populate tags
        if (data.tag_names && Array.isArray(data.tag_names)) {
            tags = data.tag_names;
        } else if (data.tags && Array.isArray(data.tags)) {
            tags = data.tags;
        } else {
            tags = [];
        }

        renderTags();   // 🔥 this makes chips appear

        updateWordCounter();

    } catch (error) {
        console.error("Load error:", error);
        alert("Failed to load article.");
    }
}

function renderTags() {
    const container = document.getElementById('tag-container');
    const input = document.getElementById('tag-input');

    container.innerHTML = '';

    tags.forEach(tag => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.innerHTML = `
            ${tag}
            <span class="tag-chip-remove" onclick="removeTag('${tag}')">×</span>
        `;
        container.appendChild(chip);
    });

    container.appendChild(input);
}

/* -------------------------------
   WORD COUNTER
-------------------------------- */
function updateWordCounter() {
    const text = contentArea.innerText || contentArea.textContent;
    const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    const chars = text.length;
    wordCounter.textContent = `${words} words, ${chars} characters`;
}

contentArea.addEventListener('input', function() {
    articleData.content = this.innerHTML;
    updateWordCounter();
});

titleInput.addEventListener('input', function() {
    articleData.title = this.value;
});

/* -------------------------------
   FORMAT FUNCTIONS
-------------------------------- */
function formatText(command) {
    const selection = window.getSelection();
    if (!selection.toString()) {
        alert('Please select some text first.');
        return;
    }
    document.execCommand(command, false, null);
    contentArea.focus();
}

function insertHeading() {
    document.execCommand('formatBlock', false, 'h2');
    contentArea.focus();
}

function insertList() {
    document.execCommand('insertUnorderedList', false, null);
    contentArea.focus();
}

function insertQuote() {
    document.execCommand('formatBlock', false, 'blockquote');
    contentArea.focus();
}

function insertLink() {
    const selection = window.getSelection();
    if (!selection.toString()) {
        alert('Please select some text first.');
        return;
    }
    const url = prompt('Enter URL:');
    if (url) {
        document.execCommand('createLink', false, url);
        contentArea.focus();
    }
}

/* -------------------------------
   TAG SYSTEM (UI ONLY)
-------------------------------- */
function handleTagInput(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = document.getElementById('tag-input');
        const tag = input.value.trim();

        if (tag && !tags.includes(tag) && tags.length < 10) {
            tags.push(tag);
            renderTags();
            input.value = '';
            articleData.tags = tags;
        }
    }
}

function removeTag(tagToRemove) {
    tags = tags.filter(tag => tag !== tagToRemove);
    renderTags();
    articleData.tags = tags;
}

function renderTags() {
    const container = document.getElementById('tag-container');
    const input = document.getElementById('tag-input');

    container.innerHTML = '';

    tags.forEach(tag => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.innerHTML = `
            ${tag}
            <span class="tag-chip-remove" onclick="removeTag('${tag}')">×</span>
        `;
        container.appendChild(chip);
    });

    container.appendChild(input);
}

/* -------------------------------
   UPDATE ARTICLE (PUT)
-------------------------------- */
async function publishArticle() {
    const title = titleInput.value.trim();
    const content = contentArea.innerText.trim();

    if (!title || !content) {
        alert("Title and content are required.");
        return;
    }

    const token = localStorage.getItem("auth_token");
    if (!token) {
        alert("You are not authenticated.");
        return;
    }

    const publishBtn = document.getElementById("publish-article-btn");
    const cancelBtn = document.getElementById("discard-article-btn");

    // 🔒 Disable buttons
    publishBtn.disabled = true;
    cancelBtn.disabled = true;

    // 🔄 Spinner state
    const originalText = publishBtn.innerHTML;
    publishBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Updating...
    `;

    const payload = {
        title: title,
        content: content,
        tag_names: tags
    };

    try {
        const response = await fetch(`${baseURL}/articles/${articleId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Failed to update article");

            // 🔓 Re-enable buttons on failure
            publishBtn.disabled = false;
            cancelBtn.disabled = false;
            publishBtn.innerHTML = originalText;
            return;
        }

        const updatedArticle = await response.json();

        // ✅ Redirect after success
        window.location.href = `view_article.html?article_id=${updatedArticle.article_id}`;

    } catch (error) {
        console.error("Update error:", error);
        alert("Server error while updating article");

        // 🔓 Re-enable buttons on error
        publishBtn.disabled = false;
        cancelBtn.disabled = false;
        publishBtn.innerHTML = originalText;
    }
}

/* -------------------------------
   DISCARD
-------------------------------- */
function discardArticle() {
    window.location.href = "Your_articles.html"
}

/* -------------------------------
   INIT
-------------------------------- */
window.addEventListener("DOMContentLoaded", () => {
    loadArticle();
});
