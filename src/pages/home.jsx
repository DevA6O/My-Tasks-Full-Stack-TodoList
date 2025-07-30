import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function Home() {
    const { accessToken, loading: authLoading } = useAuth();
    const [tasks, setTasks] = useState([]);
    const [username, setUsername] = useState("User");
    const [error, setError] = useState(null);
    const [isLoading, setLoading] = useState(true);

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
                    setError("Server error: Tasks could not be loaded.");
                }
            } catch (error) {
                setError(error);
            } finally{
                setLoading(false);
            }
        }

        loadTasks();
    }, [accessToken, authLoading]) 


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

                            <div className="flex mt-5 items-center gap-10">
                                <div className="flex flex-col gap-6 w-full max-w-md">
                                    <div className="flex flex-col">
                                    <label htmlFor="title" className="mb-1 font-medium">Title</label>
                                    <input
                                        id="title"
                                        type="text"
                                        className="px-4 py-2 border border-gray-300 rounded-md"
                                        placeholder="What would you like to do"
                                    />
                                    </div>

                                    <div className="flex flex-col">
                                    <label htmlFor="description" className="mb-1 font-medium">Description</label>
                                    <input
                                        id="description"
                                        type="text"
                                        className="px-4 py-2 border border-gray-300 rounded-md"
                                        placeholder="Add a short description"
                                    />
                                    </div>
                                </div>

                                <button
                                    className="bg-blue-600 text-white font-medium px-6 py-2 rounded-md hover:bg-blue-700 transition cursor-pointer"
                                >
                                    Add Task
                                </button>
                            </div>

                            <div className="mt-4 h-[5px] bg-gray-300 w-full mx-auto rounded"></div>
                        </div>

                        {/* Current tasks */}
                        <div className="flex flex-col m-20">
                            <h1 className="font-semibold text-2xl">Your Tasks</h1>

                            {error && <p className="text-red-500/80">{error}</p>}
                            {!isLoading && !error && tasks.length === 0 && 
                                <p className="font-sans">You don't have any to-dos to complete.</p>
                            }

                            {!error && Array.isArray(tasks) && tasks.length > 0 && (
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