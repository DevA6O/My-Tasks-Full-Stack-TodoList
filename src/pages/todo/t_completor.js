export async function completeTodoAPI(todoID, accessToken) {
    response = await fetch(`${import.meta.env.VITE_API_URL}/todo/complete`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify({todo_id: todoID})
    });

    if (!response.ok) {
        data = await response.json();
        throw new Error(data.detail || "Completion failed: An unexpected error is occurred.");
    };
}