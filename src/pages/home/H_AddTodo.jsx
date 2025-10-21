import React from "react";
import { useForm } from "react-hook-form";
import * as yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";
import { toast } from "react-toastify";

const validationDisabled = import.meta.env.VITE_DISABLE_FRONTEND_VALIDATION;

export const schema = validationDisabled
    ? yup.object().shape({})
    : yup.object().shape({
        title: yup
            .string()
            .required("Title is required.")
            .min(2, "Title must have at least 2 characters.")
            .max(140, "Title cannot have more than 140 characters."),
        description: yup
            .string()
            .max(320, "Description cannot have more than 320 characters.")
    }
);

export async function createTodoAPI(formData, accessToken) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(formData)
    });
    const data = await response.json();

    if (!response.ok) {
        let errorMsg = data.detail;

        // If a validation error occurs
        if (!response.ok && response.status == 422) {
            errorMsg = data.detail?.message;
        };

        // Throw an error if the creation was unsuccessful
        const error = new Error(
            errorMsg || "Creation failed: An unexpected error has occurred. Please try again later."
        );
        error.status_code = response?.status;
        throw error;
    };

    return true;
};


export default function HomePageAddTodo({ accessToken, onSuccess }) {
    const {
        register: registerHome,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onBlur"
    });

    const onSubmit = async (formData) => {
        // Define a default error message for create
        const defaultErrorMsg = "Creation failed: An unexpected error has occurred. " +
        "Please try again later.";

        try {
            const success = await createTodoAPI(formData, accessToken);
            
            // Check whether the creation was successful
            if (success) {
                onSuccess(); // Reload the tasks
                reset(); // Reset form 

                toast.success("Creation successful: Todo was created successfully.");
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
        <div data-testid="HomePageAddTodo" className="flex-1 mt-10 max-w-100">
            <h1 className="font-semibold text-xl">Add a New Task</h1>
            <p className="text-lg">Here you can add a new task.</p>

            <form className="flex flex-col" onSubmit={handleSubmit(onSubmit)}>
                {/* Title input field */}
                <div className="flex flex-col mt-5">
                    <label htmlFor="title" className="text-lg">
                        <span className="text-red-500">*</span> Title <span className="text-sm">(Required)</span>
                    </label>

                    <input 
                        id="title"
                        type="text"
                        data-testid="HomePageAddTodo-Title-Input"
                        {...registerHome("title")}
                        className="p-2 w-3xs md:w-100 border-2 border-gray-400 rounded"
                    />

                    {/* Display error message */}
                    {errors.title && (
                        <p className="font-sans text-red-500 max-w-[90vw] break-words">{errors.title.message}</p>
                    )}
                </div>
                
                {/* Description input field */}
                <div className="flex flex-col mt-5">
                    <label htmlFor="description" className="text-lg">Description</label>

                    <input 
                        id="description"
                        type="text"
                        data-testid="HomePageAddTodo-Description-Input"
                        {...registerHome("description")}
                        className="p-2 w-3xs md:w-100 border-2 border-gray-400 rounded"
                    />

                    {/* Display error message */}
                    {errors.description && (
                        <p className="font-sans text-red-500 max-w-[90vw] break-words">{errors.description.message}</p>
                    )}
                </div>

                {/* Add task button */}
                <div className="mt-5 text-center flex md:justify-center">
                    <button 
                        type="submit"
                        data-testid="HomePageAddTodo-Submit-Button"
                        className="px-5 py-2 text-lg text-white bg-blue-600 rounded cursor-pointer hover:bg-blue-500 transition-all ease-in-out duration-400"
                    >
                        Add Task
                    </button>
                </div>
            </form>
        </div>
    )
}