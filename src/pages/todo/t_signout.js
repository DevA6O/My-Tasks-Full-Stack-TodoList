export default async function signoutUserAPI() {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/signout`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "credentials": "include"
        }
    })

    if (!response.ok) {
        const errorMsg = await response.json()
        throw new Error(errorMsg || "Signout failed: An unexpected error occurred.")
    }
}