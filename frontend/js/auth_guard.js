export async function protectRoute() {
    const token = localStorage.getItem("auth_token");

    // If no token → redirect
    if (!token) {
        window.location.href = "../pages/Authentication.html";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/validate-token", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        const data = await response.json();

        if (!response.ok || data.valid === false) {
            // Token invalid or expired
            localStorage.removeItem("auth_token");
            localStorage.removeItem("user_id");
            window.location.href = "../pages/Authentication.html";
            alert("Please Login")
            return;
        }

        // Valid token
        return true;

    } catch (err) {
        console.error("Token validation error:", err);
        window.location.href = "../pages/Auth.html";
    }
}
