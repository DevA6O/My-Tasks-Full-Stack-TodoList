export async function completeTodoAPI(todoID, accessToken) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/complete`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify({todo_id: todoID})
    });

    if (!response.ok) {
        const data = await response.json();

        const error = new Error(data.detail || "Completion failed: An unexpected error is occurred. Please try again later.");
        error.todoID = todoID;
        error.status_code = response?.status;
        throw error;
    };

    return true;
};

export async function deleteTodoAPI(todoID, accessToken) {
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
        const data = await response.json();

        const error = new Error(data.detail || "Deletion failed: An unexpected error occurred. Please try again later.");
        error.todoID = todoID;
        error.status_code = response?.status;
        throw error;
    };

    return true;
};