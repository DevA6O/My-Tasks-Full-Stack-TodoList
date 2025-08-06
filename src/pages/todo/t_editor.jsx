import { yupResolver } from "@hookform/resolvers/yup";
import React, { useState } from "react";
import { useForm } from "react-hook-form";


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
        throw new Error(errorData.detail || "Update failed: An unexpected server error occurred. Please try again later.")
    };
};


export default function EditorModal({ isOpen, onClose, children }) {
    if (!isOpen) return null;

    return (
        <>
            {/* Transparent blackground */}
            <div className="fixed inset-0 bg-black/80 z-40" onClick={onClose}></div>

            {/* Modal box */}
            <div className="fixed inset-0 flex items-center justify-center z-50">
                <div 
                    className="bg-white p-5 rounded shadow-md w-full max-w-md"
                    onClick={(e) => e.stopPropagation()}>
                    
                    {children}
                </div>
            </div>
        </>
    )
}

export function EditTaskForm({ task, validationSchema, accessToken, onSuccess }) {
    const {
        register: registerEditor,
        handleSubmit,
        setError,
        formState: { errors }
    } = useForm({
        resolver: yupResolver(validationSchema),
        mode: "onTouched",
        defaultValues: {
            title: task.title,
            description: task.description
        }
    })

    const onSubmit = async (formData) => {
        try {
            const data = {
                ...formData,
                todo_id: task.id
            }

            await updateTodo(data, accessToken);
            onSuccess();
        } catch (error) {
            setError("apiError", {type: "manual", message: "Update failed: An unexpected error occurred. Please try again later."});
            console.error(error); 
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <h2 className="text-2xl font-bold mb-4">Edit Task</h2>

            {/* Display error */}
            {errors.apiError && (
                <div className="flex justify-center w-full mb-4 p-5 border border-red-600 bg-red-200 rounded">
                    <p className="font-sans text-red-900 break-words text-center">{errors.apiError.message}</p>
                </div>
            )}

            {/* Title input */}
            <div className="mb-4">
                <label htmlFor="editTitle" className="block mb-1 font-medium">Title</label>
                <input
                    type="text"
                    id="editTitle"
                    {...registerEditor("title")}
                    className="w-full px-3 py-2 border rounded"/>

                {errors.title && (
                    <p className="font-sans text-red-500 max-w-[90vw] break-words">{errors.title.message}</p>
                )}
            </div>

            {/* Description input */}
            <div className="mb-4">
                <label htmlFor="editDescription" className="block mb-1 font-medium">Description</label>
                <input
                    type="text"
                    id="editDescription"
                    {...registerEditor("description")}
                    className="w-full px-3 py-2 border rounded"/>

                {errors.description && (
                    <p className="font-sans text-red-500 max-w-[90vw] break-words">{errors.description.message}</p>
                )}
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-3">
                <button 
                    type="button"
                    onClick={onSuccess}
                    className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400 cursor-pointer">
                    Cancel
                </button>
                <button 
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 cursor-pointer">
                    Save
                </button>
            </div>
        </form>
    );
}
