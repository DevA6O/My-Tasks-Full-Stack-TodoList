import React, { useEffect, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import HomePageNavigation from "./H_Navigation";
import HomePageAddTodo from "./H_AddTodo";
import HomePageManageAndDisplayTodos from "./H_ManageAndDisplayTodos";


export default function HomePage() {
    const { accessToken, loading: authLoading } = useAuth();
    const [isLoading, setLoading] = useState(true);
    
    const [username, setUsername] = useState("User");
    const [tasks, setTasks] = useState([]);
    const [taskError, setTaskError] = useState("");

    const [reloadTasks, setReloadTasks] = useState(false);

    useEffect(() => {
        // Wait for the access token
        if (authLoading) return;
        
        // If the user isn't logged in
        if (!accessToken && !authLoading) {
            window.location.href = "/login";
            return;
        };

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
                };
            } catch (error) {
                setTaskError("An unexpected error occurred while loading all tasks. Please try again later.")
            } finally{
                setLoading(false);
                setReloadTasks(false);
            };
        };

        loadTasks();
    }, [accessToken, authLoading, reloadTasks]);

    return (
        <>
            {!isLoading && (
                <>
                    {/* Side- & Navbar */}
                    <HomePageNavigation />

                    <main data-testid="homepage-main-content" className="flex-1 pt-40 pl-5 sm:pl-10 md:pl-10 lg:pt-30 lg:ml-80">
                        <div>
                            <h1 className="font-semibold text-2xl md:text-3xl">Welcome back, {username}!</h1>
                            <p className="md:text-lg">Ready to do a task or add a new one?</p>

                            <div className="w-11/12 p-1 bg-black/20 rounded"></div>
                        </div>

                        <HomePageAddTodo 
                            accessToken={accessToken}
                            onSuccess={() => { setReloadTasks(true); }}
                        />

                        <div className="mt-5 w-11/12 p-1 bg-black/20 rounded"></div>

                        <div className="mt-10">
                            <h1 className="font-semibold text-xl">Your current Tasks</h1>
                            <p className="text-lg">Here you can see all the open tasks you have.</p>
                            
                            <div className="mt-5">
                                {taskError !== "" && (
                                    <p className="text-red-800 font-sans font-semibold text-xl max-w-11/12">
                                        {taskError}
                                    </p>
                                )}
                                {!isLoading && taskError == "" && tasks.length === 0 && (
                                    <p className="text-blue-800 font-sans font-semibold text-xl max-w-11/12">
                                        Nice work! Currently you have no tasks to solve!
                                    </p>
                                )}
                            </div>

                            {!isLoading && taskError == "" && tasks.length > 0 && (
                                <HomePageManageAndDisplayTodos 
                                    tasks={tasks} 
                                    accessToken={accessToken} 
                                    setReloadTasks={setReloadTasks} 
                                />
                            )}
                        </div>
                    </main>
                </>
            )} 
        </>
    )
}