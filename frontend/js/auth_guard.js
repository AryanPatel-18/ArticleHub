export async function protectRoute() {
    const token = localStorage.getItem("auth_token");

    if (!token) {
        window.location.replace("../pages/Session_timeout.html");
        return false;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/validate-token", {
            headers: {
                Authorization: "Bearer " + token
            }
        });

        const data = await response.json();

        if (!response.ok || data.valid === false) {
            localStorage.clear();
            sessionStorage.clear();
            window.location.replace("../pages/Session_timeout.html");
            return false;
        }

        return true;

    } catch (err) {
        window.location.replace("../pages/Authentication.html");
        return false;
    }
}
