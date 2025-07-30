import React, { useActionState, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useForm } from "react-hook-form";
import * as yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";

const schema = yup.object().shape({
    title: yup
        .string()
        .min(2, "Title must have at least 2 characters.")
        .max(140, "Title cannot have more than 140 characters.")
        .required("Title is required."),
    description: yup
        .string()
        .max(320, "Description cannot have more than 320 characters.")
})


export default function Home() {
    const { accessToken, loading: authLoading } = useAuth();
    const [tasks, setTasks] = useState([]);
    const [username, setUsername] = useState("User");
    const [taskErrors, setTaskError] = useState(null);
    const [isLoading, setLoading] = useState(true);
    const [reloadTasks, setReloadTasks] = useState(false);

    const {
        register: registerHome,
        handleSubmit,
        setError,
        formState: { errors },
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onTouched"
    })

    const onSubmit = async (formData) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/create`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${accessToken}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                setReloadTasks(true);
            } else {
                const data = await response.json();

                setError("apiError", {type: "manual", message: data.detail.message})
            }
        } catch (error) {
            console.log(error)
            setError(error);
        };
    };

    useEffect(() => {
        if (!accessToken || authLoading) return;

        const loadTasks = async () => {
            try {
                const response = await fetch(`${import.meta.env.VITE_API_URL}/todo/get_all`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${accessToken}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();

                    setTasks(Array.isArray(data.todos) ? data.todos : []);
                    setUsername(data.username || "User");
                } else {
                    setTaskError("Server error: Tasks could not be loaded.");
                }
            } catch (error) {
                setTaskError(error);
            } finally{
                setLoading(false);
            }
        }

        loadTasks();
    }, [accessToken, authLoading, reloadTasks]) 


    return (
        <>
            {isLoading && <p className="text-gray-500">Loading...</p>}
            
            {!isLoading && (
                <div className="flex h-screen">
                    {/* Sidebar */}
                    <aside className="flex flex-col justify-between p-10 w-64">
                        <h1 className="text-2xl font-bold">Menu</h1>
                        <div className="flex flex-col gap-1">
                            <a href="/settings" className="w-full">Settings</a>
                            <a href="/sign-out" className="w-full">Sign out</a>
                        </div>
                    </aside>

                    <main className="flex-1">
                        {/* Welcome message */}
                        <div className="flex flex-col m-20">
                            <h1 className="text-3xl">Welcome back, {username}!</h1>
                            <p className="text-lg text-black/80">Ready to do a task or add a new one?</p>
                            <div className="mt-4 h-[5px] bg-gray-300 w-full mx-auto rounded"></div>
                        </div>

                        {/* Add task */}
                        <div className="flex flex-col m-20">
                            <h1 className="font-semibold text-2xl">New Task</h1>
                            <p className="text-black/80">Here you can add a new task</p>

                            <form className="flex mt-5 items-center gap-10" onSubmit={handleSubmit(onSubmit)}>
                                <div className="flex flex-col gap-6 w-full max-w-md">
                                    <div className="flex flex-col">
                                        <label htmlFor="title" className="mb-1 font-medium">Title</label>
                                        <input
                                            id="title"
                                            type="text"
                                            {...registerHome("title")}
                                            className="px-4 py-2 border border-gray-300 rounded-md"
                                            placeholder="What would you like to do"
                                        />

                                        {errors.title && (
                                            <p className="text-red-500 mt-2 font-sans">{errors.title.message}</p>
                                        )}
                                    </div>

                                    <div className="flex flex-col">
                                        <label htmlFor="description" className="mb-1 font-medium">Description</label>
                                        <input
                                            id="description"
                                            type="text"
                                            {...registerHome("description")}
                                            className="px-4 py-2 border border-gray-300 rounded-md"
                                            placeholder="Add a short description"
                                        />

                                        {errors.description && (
                                            <p className="text-red-500 mt-2 font-sans">{errors.description.message}</p>
                                        )}
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    className="bg-blue-600 text-white font-medium px-6 py-2 rounded-md hover:bg-blue-700 transition cursor-pointer"
                                >
                                    Add Task
                                </button>
                            </form>

                            {errors.apiError && (
                                <p className="text-red-500 mt-2 font-sans">{errors.apiError.message}</p>
                            )}

                            <div className="mt-4 h-[5px] bg-gray-300 w-full mx-auto rounded"></div>
                        </div>

                        {/* Current tasks */}
                        <div className="flex flex-col m-20">
                            <h1 className="font-semibold text-2xl">Your Tasks</h1>

                            {taskErrors && <p className="text-red-500/80">{taskErrors.toString()}</p>}
                            {!isLoading && !taskErrors && tasks.length === 0 && 
                                <p className="font-sans">You don't have any to-dos to complete.</p>
                            }

                            {!taskErrors && Array.isArray(tasks) && tasks.length > 0 && (
                                <div className="flex flex-col gap-4">
                                    {tasks.map((task) => (
                                    <div
                                        key={task.id}
                                        className="w-full max-w-2xl border border-gray-300 bg-gray-50 rounded-md px-4 py-3 flex justify-between items-center shadow-sm"
                                    >
                                        <div className="flex flex-col max-w-[85%] overflow-hidden">
                                            <h2 className="text-base font-semibold text-gray-800 leading-snug break-words">
                                                {task.title}
                                            </h2>
                                            <p className="text-sm text-gray-600 mt-1 leading-snug break-words">
                                                {task.description}
                                            </p>
                                        </div>

                                        <button
                                            className="text-red-600 hover:text-red-800 font-medium text-sm px-3 py-1 border border-red-300 rounded-md transition shrink-0 ml-4 cursor-pointer"
                                            >
                                            Delete
                                        </button>
                                    </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </main>
                </div>
            )}
        </>
    )
}