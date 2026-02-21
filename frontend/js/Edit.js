// This files handles the article edit form
import { protectRoute } from "./auth_guard.js";

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

// Get the article id from teh url
function getArticleIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id");
}

// loading the articles from the backend
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

        // Populate title
        titleInput.value = data.title;
        articleData.title = data.title;

        // Populate content (sanitize once)
        contentArea.innerHTML = DOMPurify.sanitize(data.content);
        articleData.content = data.content;

        // Normalize tags to object structure
        if (data.tags && Array.isArray(data.tags)) {
            tags = data.tags.map(t => ({
                tag_id: t.tag_id ?? null,
                tag_name: t.tag_name
            }));
        } else if (data.tag_names && Array.isArray(data.tag_names)) {
            tags = data.tag_names.map(name => ({
                tag_id: null,
                tag_name: name
            }));
        } else {
            tags = [];
        }

        articleData.tags = tags;

        renderTags();
        updateWordCounter();

    } catch (error) {
        console.error("Load error:", error);
        alert("Failed to load article.");
    }
}

// Used for creating dismissible boxes that contains all the tags
function renderTags() {
    const container = document.getElementById('tag-container');
    const input = document.getElementById('tag-input');

    container.innerHTML = '';

    tags.forEach(tag => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';

        const textNode = document.createTextNode(tag.tag_name);
        chip.appendChild(textNode);

        const removeBtn = document.createElement('span');
        removeBtn.className = 'tag-chip-remove';
        removeBtn.textContent = '×';

        removeBtn.addEventListener('click', () => {
            removeTag(tag.tag_id ?? tag.tag_name);
        });

        chip.appendChild(removeBtn);
        container.appendChild(chip);
    });

    container.appendChild(input);
}

// word counter
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

// all the formatting functions are defined below
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

// handling the tag input by detecting the enter key being pressed
function handleTagInput(event) {
    if (event.key === 'Enter') {
        event.preventDefault();

        const input = document.getElementById('tag-input');
        const tagName = input.value.trim();

        if (!tagName || tags.length >= 10) return;

        const exists = tags.some(
            t => t.tag_name.toLowerCase() === tagName.toLowerCase()
        );

        if (!exists) {
            tags.push({
                tag_id: null,
                tag_name: tagName
            });

            articleData.tags = tags;
            renderTags();
        }

        input.value = '';
    }
}

function removeTag(identifier) {
    tags = tags.filter(tag => {
        if (tag.tag_id !== null && tag.tag_id !== undefined) {
            return tag.tag_id !== identifier;
        }
        return tag.tag_name !== identifier;
    });

    articleData.tags = tags;
    renderTags();
}
// The main function that sends data to the backend using payload as well as passing the auth token in the header section
async function publishArticle() {
    const title = titleInput.value.trim();
    const content = contentArea.innerHTML.trim();

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

    //Disable buttons
    publishBtn.disabled = true;
    cancelBtn.disabled = true;

    //Spinner state
    const originalText = publishBtn.innerHTML;
    publishBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Updating...
    `;

    const payload = {
        title: title,
        content: content,
        tag_names: tags.map(t => t.tag_name)
    };

    console.log(payload)

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
            if (err.detail && Array.isArray(err.detail)) {
                err.detail.forEach(e => {
                    const field = e.loc[e.loc.length - 1];

                    if (field === "content") {
                        alert("Your article content is too short. Please write at least 50 characters.");
                    } else if (field === "title") {
                        alert("Your title is too short. Please write a longer title.");
                    } else {
                        alert(e.msg);
                    }
                });
            } else {
                alert("Failed to publish article.");
            }

            // 🔓 Re-enable buttons on failure
            publishBtn.disabled = false;
            cancelBtn.disabled = false;
            publishBtn.innerHTML = originalText;
            return;
        }

        const updatedArticle = await response.json();

        // Redirect after success
        window.location.href = `view_article.html?article_id=${updatedArticle.article_id}`;

    } catch (error) {
        console.error("Update error:", error);
        alert("Server error while updating article");

        // Re-enable buttons on error
        publishBtn.disabled = false;
        cancelBtn.disabled = false;
        publishBtn.innerHTML = originalText;
    }
}

// Discarding the article and moving to the home page
function discardArticle() {
    window.location.href = "Your_articles.html"
}

document.addEventListener("DOMContentLoaded", async () => {
    const isValid = await protectRoute();
    if (!isValid) return;

    loadArticle();
});


window.formatText = formatText;
window.insertHeading = insertHeading;
window.insertList = insertList;
window.insertQuote = insertQuote;
window.insertLink = insertLink;
window.handleTagInput = handleTagInput;
window.publishArticle = publishArticle;
window.discardArticle = discardArticle;
window.removeTag = removeTag;

