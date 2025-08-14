export default async function createTodoAPI(formData, accessToken) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(formData)
    });
    const data = await response.json();
    let errorMsg = data.detail;

    // If a validation error occurs
    if (!response.ok && response.status == 422) {
        errorMsg = data.detail?.message;
    };

    throw new Error(errorMsg || "Creation failed: An unexpected error occurred. Please try again later.");
};