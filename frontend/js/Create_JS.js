import { protectRoute } from "./auth_guard.js";

let tags = [];
let autoSaveTimer;
let articleData = {
    title: '',
    content: '',
    tags: []
};

document.addEventListener("DOMContentLoaded", async () => {
    const isValid = await protectRoute();

    if (!isValid) return;
});

const contentArea = document.getElementById('article-content');
const wordCounter = document.getElementById('word-counter');

contentArea.addEventListener('input', function() {
    const text = this.innerText || this.textContent;
    const words = text.trim().split(/\s+/).filter(word => word.length > 0).length;
    const chars = text.length;
    wordCounter.textContent = `${words} words, ${chars} characters`;
    
    articleData.content = this.innerHTML;
    // autoSave();
});

// Title input
document.getElementById('article-title').addEventListener('input', function() {
    articleData.title = this.value;
});

// Format Text Functions
function formatText(command) {
    const selection = window.getSelection();
    if (!selection.toString()) {
        alert('Please select some text first.');
        return;
    }
    document.execCommand(command, false, null);
    document.getElementById('article-content').focus();
}

function insertHeading() {
    const selection = window.getSelection();
    if (!selection.toString()) {
        alert('Please select some text first.');
        return;
    }
    
    // Checking if already a heading by traversing up the parent chain
    let element = selection.anchorNode;
    let isHeading = false;
    
    while (element && element !== contentArea) {
        if (element.tagName === 'H2') {
            isHeading = true;
            break;
        }
        element = element.parentElement;
    }
    
    if (isHeading) {
        document.execCommand('formatBlock', false, 'p');
    } else {
        document.execCommand('formatBlock', false, 'h2');
    }
    document.getElementById('article-content').focus();
}

function insertList() {
    const selection = window.getSelection();
    if (!selection.toString()) {
        alert('Please select some text first.');
        return;
    }
    document.execCommand('insertUnorderedList', false, null);
    document.getElementById('article-content').focus();
}

function insertQuote() {
    const selection = window.getSelection();
    if (!selection.toString()) {
        alert('Please select some text first.');
        return;
    }
    
    // Check if already a blockquote by traversing up the parent chain
    let element = selection.anchorNode;
    let isQuote = false;
    
    while (element && element !== contentArea) {
        if (element.tagName === 'BLOCKQUOTE') {
            isQuote = true;
            break;
        }
        element = element.parentElement;
    }
    
    if (isQuote) {
        document.execCommand('formatBlock', false, 'p');
    } else {
        document.execCommand('formatBlock', false, 'blockquote');
    }
    document.getElementById('article-content').focus();
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
        document.getElementById('article-content').focus();
    }
}

// Tag System
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

// Converts the tag entered into a dismissible block format
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


// Load draft on page load
window.addEventListener('load', function() {
    const draft = localStorage.getItem('draft_article');
    if (draft) {
        const data = JSON.parse(draft);
        document.getElementById('article-title').value = data.title || '';
        document.getElementById('article-content').innerHTML = data.content || '';
        
        if (data.coverImage) {
            document.getElementById('cover-preview').src = data.coverImage;
            document.getElementById('cover-preview').classList.add('show');
        }
        
        tags = data.tags || [];
        renderTags();
        
        articleData = data;
        contentArea.dispatchEvent(new Event('input'));
    }
});

// Action Functions

const publishButton = document.getElementById("publish-article-btn")

// Main function that sends the payload to the backend to create the article, Here the article information is returned but is not used, and the user is sent back to the home page
async function publishArticle() {
    const title = document.getElementById('article-title').value.trim();
    const content = document.getElementById('article-content').innerHTML.trim();

    if (!title || !content) {
        alert('Please add a title and content before publishing.');
        return;
    }

    const token = localStorage.getItem("auth_token");

    publishButton.disabled = true;
    publishButton.innerHTML =
        `<span class="spinner-border spinner-border-sm" role="status"></span> Publishing...`;

    const payload = {
        title: title,
        content: content,
        tag_names: articleData.tags
    };

    try {
        const response = await fetch("http://localhost:8000/articles/", {
            method: "POST",
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

            publishButton.disabled = false;
            publishButton.innerText = "Publish Article";
            return;
        }

        window.location.href = "home.html";

    } catch (error) {
        console.error("Publish error:", error);
        alert("Server error while publishing article");

        publishButton.disabled = false;
        publishButton.innerText = "Publish Article";
    }
}


function saveDraft() {
    // autoSave();
    alert('Draft saved successfully!');
}

function discardArticle() {
    contentArea.text = ""
    document.getElementById("article-title").text = ""
}


window.formatText = formatText;
window.insertHeading = insertHeading;
window.insertList = insertList;
window.insertQuote = insertQuote;
window.insertLink = insertLink;
window.handleTagInput = handleTagInput;
window.publishArticle = publishArticle;
window.saveDraft = saveDraft;
window.discardArticle = discardArticle;