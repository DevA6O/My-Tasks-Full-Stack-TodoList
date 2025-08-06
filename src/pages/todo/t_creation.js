export default async function createTodoAPI(formData, accessToken) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(formData)
    });

    if (!response.ok) {
        const data = await response.json();

        throw new Error(data.detail || "Creation failed: An unexpected error occurred. Please try again later.");
    };
};