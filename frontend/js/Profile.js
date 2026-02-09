// This js file loads all the information of the user from the backend, also allows the user to change the information and also change the password for the account
import { protectRoute } from "./auth_guard.js";

window.addEventListener("DOMContentLoaded", async () =>{
    const isValid = await protectRoute();

    if (!isValid) return;
    
    loadUserProfile();
});



// Edit section functionality
function editSection(section) {
    const viewMode = document.getElementById(`${section}-view-mode`);
    const editMode = document.getElementById(`${section}-edit-mode`);
    
    if (viewMode) viewMode.classList.add('hidden');
    if (editMode) editMode.classList.add('active');
}

function cancelEdit(section) {
    const viewMode = document.getElementById(`${section}-view-mode`);
    const editMode = document.getElementById(`${section}-edit-mode`);
    
    if (viewMode) viewMode.classList.remove('hidden');
    if (editMode) editMode.classList.remove('active');
}

// Saves the information from the form
function saveSection(section) {
    if (section === "personal-info" || section === "about" || section === "social") {
        updateUserProfile(section);
        return;
    }
    cancelEdit(section);
}

// Profile image change
document.getElementById('edit-image-btn').addEventListener('click', () => {
    alert('Profile picture upload functionality would be implemented here!');
});

// Logout functionality
function logout() {
    const modal = new bootstrap.Modal(document.getElementById("confirmLogoutModal"));
    modal.show();
}

// Main function that requests the data from the backend, the user id is passed through the auth token that is stored in the local storage
async function loadUserProfile() {
    const token = localStorage.getItem("auth_token");

    if (!token) {
        alert("Not authenticated. Please log in again.");
        window.location.href = "auth.html";
        return;
    }

    try {
        const response = await fetch("http://localhost:8000/users/me", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Failed to fetch profile");
        }

        const data = await response.json();

        // for populating the view mode
        document.getElementById("profile-username-display").textContent = data.user_name;
        document.getElementById("profile-user-handle").textContent = `@${data.user_name}`;

        document.getElementById("username-display-value").textContent = data.user_name;
        document.getElementById("email-display-value").textContent = data.user_email;

        if (data.birth_date) {
            const date = new Date(data.birth_date);
            const options = { year: "numeric", month: "long", day: "numeric" };
            document.getElementById("birthdate-display-value").textContent =
                date.toLocaleDateString("en-US", options);
        } else {
            document.getElementById("birthdate-display-value").textContent = "Not set";
        }

        document.getElementById("about-display-value").textContent = data.bio || "No bio provided";

        if (data.social_link) {
            document.getElementById("social-link-display").href = data.social_link;
            document.getElementById("social-url-display").textContent =
                data.social_link.replace("https://", "").replace("http://", "");
        } else {
            document.getElementById("social-url-display").textContent = "No link provided";
        }

        //For populating the edit mode
        document.getElementById("username-input").value = data.user_name;
        document.getElementById("email-input").value = data.user_email;
        document.getElementById("birthdate-input").value = data.birth_date || "";
        document.getElementById("about-input").value = data.bio || "";
        document.getElementById("social-input").value = data.social_link || "";

    } catch (error) {
        console.error("Profile load error:", error);
        alert("Could not load profile. Please login again.");
        window.location.href = "auth.html";
    }
}

// Creates the payload based on the information that the user updated, since any of the sections can be left as none in the payload as per the backend schema. In this way a single endpoint can be used to update all the information of the user except the password
function buildProfileUpdatePayload(section) {
    const payload = {};

    if (section === "personal-info") {
        payload.user_name = document.getElementById("username-input").value;
        payload.email = document.getElementById("email-input").value;
        payload.birth_date = document.getElementById("birthdate-input").value || null;
    }

    if (section === "about") {
        payload.bio = document.getElementById("about-input").value;
    }

    if (section === "social") {
        payload.social_link = document.getElementById("social-input").value;
    }

    return payload;
}


// The main function that updates the user information by sending the payload to the endpoint in the backend
async function updateUserProfile(section) {
    const token = localStorage.getItem("auth_token");
    if (!token) {
        alert("Not authenticated");
        window.location.href = "auth.html";
        return;
    }

    const payload = buildProfileUpdatePayload(section);

    try {
        const response = await fetch("http://localhost:8000/users/me", {
            method: "PUT",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error("Profile update failed");
        }

        const data = await response.json();

        // update the view mode
        document.getElementById("profile-username-display").textContent = data.user_name;
        document.getElementById("profile-user-handle").textContent = `@${data.user_name}`;

        document.getElementById("username-display-value").textContent = data.user_name;
        document.getElementById("email-display-value").textContent = data.user_email;

        if (data.birth_date) {
            const date = new Date(data.birth_date);
            const options = { year: "numeric", month: "long", day: "numeric" };
            document.getElementById("birthdate-display-value").textContent =
                date.toLocaleDateString("en-US", options);
        }

        document.getElementById("about-display-value").textContent = data.bio || "No bio provided";

        if (data.social_link) {
            document.getElementById("social-link-display").href = data.social_link;
            document.getElementById("social-url-display").textContent =
                data.social_link.replace("https://", "").replace("http://", "");
        } else {
            document.getElementById("social-url-display").textContent = "No link provided";
        }

        // updating the edit mode
        document.getElementById("username-input").value = data.user_name;
        document.getElementById("email-input").value = data.user_email;
        document.getElementById("birthdate-input").value = data.birth_date || "";
        document.getElementById("about-input").value = data.bio || "";
        document.getElementById("social-input").value = data.social_link || "";

        cancelEdit(section);

    } catch (err) {
        console.error("Update error:", err);
        alert("Failed to update profile");
    }
}

let pendingPasswordPayload = null;

// The function that checks that both the new password and the confirm password are the same as also prompts the user to confirm wether they want to change the password or not
function handlePasswordChange() {
    const oldPassword = document.getElementById("current-password-input").value;
    const newPassword = document.getElementById("new-password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;

    if (!oldPassword || !newPassword || !confirmPassword) {
        alert("Please fill in all password fields.");
        return;
    }

    if (newPassword !== confirmPassword) {
        alert("New password and confirm password do not match.");
        return;
    }

    pendingPasswordPayload = {
        old_password: oldPassword,
        new_password: newPassword,
        confirm_new_password: confirmPassword
    };

    const modal = new bootstrap.Modal(document.getElementById("confirmPasswordModal"));
    modal.show();
}

// The function that actually sends the new password to the backend for updating through the payload. Also sends the auth token for verification of the old password. In case the backend returns false that is the old password was not valid then the user would be prompted with an alert modal that would say invalid password
async function updatePassword() {
    const token = localStorage.getItem("auth_token");
    if (!token) {
        alert("Not authenticated");
        window.location.href = "auth.html";
        return;
    }

    try {
        const response = await fetch("http://localhost:8000/users/me/password", {
            method: "PUT",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(pendingPasswordPayload)
        });
        
        const data = await response.json();
        if (!response.ok) {
            const message = data.detail || "Password change failed";
            showPasswordErrorToast(message);
            return;
        }
        showPasswordSuccessToast();

        // Clear inputs
        document.getElementById("current-password-input").value = "";
        document.getElementById("new-password-input").value = "";
        document.getElementById("confirm-password-input").value = "";

        cancelEdit("password");

    } catch (err) {
        console.error("Password update error:", err);
        alert("This is running");
    }
}

// All the modals are in the below functions
document.getElementById("confirm-password-change-btn")
    .addEventListener("click", () => {
        const modalEl = document.getElementById("confirmPasswordModal");
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        updatePassword();
});

document.getElementById("confirm-logout-btn")
    .addEventListener("click", () => {
        const modalE2 = document.getElementById("confirmLogoutModal");
        const modal1 = bootstrap.Modal.getInstance(modalE2);
        modal1.hide();
        localStorage.clear()
        window.location.href = "Authentication.html"
});


function showPasswordSuccessToast() {
    const toastEl = document.getElementById("passwordSuccessToast");
    const toast = new bootstrap.Toast(toastEl, {
        delay: 1500   // 1.5 seconds
    });
    toast.show();
}

function showPasswordErrorToast(message) {
    const toastEl = document.getElementById("passwordErrorToast");
    document.getElementById("password-error-message").textContent = message;

    const toast = new bootstrap.Toast(toastEl, {
        delay: 2000
    });
    toast.show();
}
