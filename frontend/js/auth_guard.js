// This file contains the function that is used to protect the routes that require authentication, it checks if the user has a valid token in the local storage and if not it redirects the user to the session timeout page. It also validates the token with the backend to ensure that it is still valid and if not it clears the local storage and redirects the user to the session timeout page. This function is called in all of the pages within the website, that is in case of this website the user would always need to login

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
