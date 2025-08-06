export default async function deleteTodoAPI(todoID, accessToken) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/delete`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify({
            todo_id: todoID
        })
    });

    if (!response.ok) {
        data = await response.json();

        throw new Error(data.detail || "Deletion failed: An unexpected error occurred. Please try again later.");
    };
};