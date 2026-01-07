function showRegister() {
    document.getElementById("auth-login-form").classList.add("d-none");
    document.getElementById("auth-register-form").classList.remove("d-none");
}

function showLogin() {
    document.getElementById("auth-register-form").classList.add("d-none");
    document.getElementById("auth-login-form").classList.remove("d-none");
}

function reloadRegisterPage(){
    const passwordInput = document.getElementById("auth-register-password-input")
    const confirmPasswordInput = document.getElementById("auth-register-confirm-password-input")
    const emailInput = document.getElementById("auth-register-email-input")
    const usernameInput = document.getElementById("auth-register-username-input")

    const registerBtn = document.getElementById("auth-register-submit-btn");
    const registerSpinner = document.getElementById("register-btn-spinner");
    const registerBtnText = document.getElementById("register-btn-text");

    passwordInput.classList.remove("input-error")
    confirmPasswordInput.classList.remove("input-error")
    emailInput.classList.remove("input-error")
    usernameInput.classList.remove("input-error")
    document.getElementById("error-email").innerText  = null;
    document.getElementById("error-username").innerText = null;

    // Hide spinner and re-enable button
    registerBtn.disabled = false;
    registerBtnText.style.opacity = "1";
    registerSpinner.style.opacity = "0";

}

function loadSpinner(){
    const registerBtn = document.getElementById("auth-register-submit-btn");
    const registerSpinner = document.getElementById("register-btn-spinner");
    const registerBtnText = document.getElementById("register-btn-text");

    registerBtn.disabled = true;
    registerBtnText.style.opacity = "0.5";
    registerSpinner.style.opacity = "1";
}

// Select the registration form
const registerForm = document.getElementById("auth-register-form");
const loginForm = document.getElementById("auth-login-form")

// Attach submit event
registerForm.addEventListener("submit", async function (event) {
    event.preventDefault(); // prevent form reload
    reloadRegisterPage()

    // Collect input values
    const user_name = document.getElementById("auth-register-username-input").value.trim();
    const user_email = document.getElementById("auth-register-email-input").value.trim();
    const password = document.getElementById("auth-register-password-input").value;
    const confirm_password = document.getElementById("auth-register-confirm-password-input").value;
    const birth_date = document.getElementById("auth-register-birth-date-input").value;
    const about_author = document.getElementById("auth-register-about-author-input").value.trim();
    const social_link = document.getElementById("auth-register-social-link-input").value.trim();

    const passwordInput = document.getElementById("auth-register-password-input")
    const confirmPasswordInput = document.getElementById("auth-register-confirm-password-input")
    const emailInput = document.getElementById("auth-register-email-input")
    const usernameInput = document.getElementById("auth-register-username-input")

    // Create request payload
    const payload = {
        user_name,
        user_email,
        password,
        confirm_password,
        birth_date,
        about_author: about_author || null,
        social_link: social_link || null
    };

    if (payload.password !== payload.confirm_password) {
        passwordInput.classList.add("input-error");
        confirmPasswordInput.classList.add("input-error");
        document.getElementById("error-password").innerText = "Passwords do not match.";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        // Parse response
        const data = await response.json();

        if (!response.ok) {
            // Show errors based on backend response
            if (data.detail === "Username already exists") {
                usernameInput.classList.add("input-error");
                document.getElementById("error-username").innerText = data.detail;
            } else if (data.detail === "Email already exists") {
                emailInput.classList.add("input-error");
                document.getElementById("error-email").innerText = data.detail;
            } else {
                alert(data.detail || "Registration failed.");
            }
            return;
        }

        // Loading the spinner
        loadSpinner()
        
        // Switching to the home page
        setTimeout(() => {    
            window.location.href = "Home.html";
        }, 1000);

    } catch (error) {
        console.error("Error:", error);
        alert("Unable to connect to the server. Try again later.");
    }
});


loginForm.addEventListener("submit", async function(event){
    event.preventDefault();
    // Inputs
    const loginEmailInput = document.getElementById("auth-login-email-input");
    const loginPasswordInput = document.getElementById("auth-login-password-input");

    // Error message elements
    const emailError = document.getElementById("error-login-email");
    const passwordError = document.getElementById("error-login-password");

    // Button
    const loginButton = document.getElementById("auth-login-submit-btn");

    // Reset styles
    loginEmailInput.classList.remove("input-error");
    loginPasswordInput.classList.remove("input-error");
    emailError.innerText = "";
    passwordError.innerText = "";

    const email = loginEmailInput.value.trim();
    const password = loginPasswordInput.value;

    // Validate email
    if (!email) {
        loginEmailInput.classList.add("input-error");
        emailError.innerText = "Email is required.";
        return;
    }

    // Validate password
    if (!password) {
        loginPasswordInput.classList.add("input-error");
        passwordError.innerText = "Password is required.";
        return;
    }

    loginButton.disabled = true;
    loginButton.innerHTML = `
        <span class="spinner-border spinner-border-sm"></span> Logging in...
    `;

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_email: email, password : password })
        });

        const data = await response.json();

        if (!response.ok) {
            if (data.detail === "Invalid credentials") {
                loginPasswordInput.classList.add("input-error");
                passwordError.innerText = "Invalid email or password.";
            } else {
                alert(data.detail || "Login failed.");
            }

            loginButton.disabled = false;
            loginButton.innerHTML = "Login";
            return;
        }

        localStorage.setItem("auth_token", data.access_token);
        localStorage.setItem("user_id", data.user_id);

        window.location.href = "Home.html";

    } catch (error) {
        console.error("Error:", error);
        loginButton.disabled = false;
        loginButton.innerHTML = "Login";
    }

})