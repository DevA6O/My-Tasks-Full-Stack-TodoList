import React from "react";
import { yupResolver } from "@hookform/resolvers/yup";
import { toast } from "react-toastify";
import { useForm } from "react-hook-form";
import Modal from "../../components/Modal";

async function updateTodo(data, accessToken) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/update`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const errorData = await response.json();

        const error = new Error(
            errorData.detail || "Update failed: An unexpected error occurred. Please try again later."
        );
        error.todoID = data?.todo_id;
        error.status_code = response?.status;
        throw error;
    };

    return true;
};


export default function HomePageEditorModal({ isOpen, onClose, children }) {
    return (
        <Modal isOpen={isOpen} onClose={onClose} classname="max-w-md">
            {children}
        </Modal>
    )
};

export function HomePageEditTaskForm({ task, validationSchema, accessToken, onSuccess }) {
    const {
        register: registerEditor,
        handleSubmit,
        formState: { errors }
    } = useForm({
        resolver: yupResolver(validationSchema),
        mode: "onTouched",
        defaultValues: {
            title: task.title,
            description: task.description
        }
    });

    const onSubmit = async (formData) => {
        // Define a default error message for update
        const defaultErrorMsg = "Update failed: An unexpected error has occurred. " +
        "Please try again later."

        try {
            // Define a data object to send this to the api
            const data = {
                ...formData,
                todo_id: task.id
            }
            
            // Try to update the todo
            const success = await updateTodo(data, accessToken);
            
            // Check whether the update was successful
            if (success) {
                onSuccess();
                toast.success("Update successful: Todo has been successfully updated.");
            } else {
                toast.error(defaultErrorMsg);
            };
        } catch (error) {
            // Check whether the user could not be authenticated
            if (error?.status_code == 401) {
                localStorage.setItem("authError", true);

                window.location.href = "/login"; return;
            };

            // If an unknown error has occurred
            toast.error(error?.message || defaultErrorMsg);
            console.error(error); 
        };
    };

    return (
        <form data-testid="HomePageEditTaskForm" onSubmit={handleSubmit(onSubmit)}>
            <h2 className="text-2xl font-bold mb-4">Edit Task</h2>
            {/* Title input */}
            <div className="mb-4">
                <label htmlFor="editTitle" className="block mb-1 font-medium">Title</label>
                <input
                    type="text"
                    id="editTitle"
                    data-testid={`EditTodo-Title-For-${task.id}`}
                    {...registerEditor("title")}
                    className="w-full px-3 py-2 border rounded"/>

                {errors.title && (
                    <p data-testid="EditTodo-Title-Error-Message"
                    className="font-sans text-red-500 max-w-[90vw] break-words">{errors.title.message}</p>
                )}
            </div>

            {/* Description input */}
            <div className="mb-4">
                <label htmlFor="editDescription" className="block mb-1 font-medium">Description</label>
                <input
                    type="text"
                    id="editDescription"
                    data-testid={`EditTodo-Description-For-${task.id}`}
                    {...registerEditor("description")}
                    className="w-full px-3 py-2 border rounded"/>

                {errors.description && (
                    <p data-testid="EditTodo-Description-Error-Message" 
                    className="font-sans text-red-500 max-w-[90vw] break-words">{errors.description.message}</p>
                )}
            </div>

            {/* Cancel and Submit button */}
            <div className="flex justify-end gap-3">
                <button 
                    type="button"
                    onClick={onSuccess}
                    data-testid={`EditTodo-Cancel-Button-For-${task.id}`}
                    className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400 cursor-pointer">
                    Cancel
                </button>
                <button 
                    type="submit"
                    data-testid={`EditTodo-Submit-Button-For-${task.id}`}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 cursor-pointer">
                    Save
                </button>
            </div>
        </form>
    );
}
