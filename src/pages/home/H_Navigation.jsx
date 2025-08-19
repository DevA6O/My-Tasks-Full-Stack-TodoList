import React from "react";
import { toast } from "react-toastify";

export async function signoutUserAPI() {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/signout`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        credentials: "include"
    });
    
    if (!response.ok) {
        const errorMsg = await response.json();
        throw new Error(errorMsg || "Signout failed: An unexpected error occurred.");
    };
};


export default function HomePageNavigation() {
    const signoutUser = async () => {
        try {
            await signoutUserAPI();
            window.location.href = "/";
        } catch (error) {
            toast.error(error.message);
            console.log(error);
        };
    };

    return (
        <>
            {/* Desktop - Sidebar */}
            <aside className="hidden lg:flex flex-col justify-between fixed top-0 left-0 h-screen items-center w-64 p-16 bg-gray-500/20 border-r-4 border-gray-300">
                <h1 className="font-bold text-2xl">MyTasks</h1>

                <div className="flex flex-col font-sans">
                    <button className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200">Settings</button>
                    <button 
                        onClick={signoutUser}
                        className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200"
                        >Sign out</button>
                </div>
            </aside>

            {/* iPhone & iPads - Navbar */}
            <nav className="lg:hidden fixed top-0 left-0 right-0 flex flex-col sm:flex-row justify-between p-6 sm:p-10 bg-gray-200 border-b-2">
                <h1 className="font-bold text-2xl">MyTasks</h1>

                <div className="flex gap-4 mt-4 sm:mt-0">
                    <button className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200">Settings</button>
                    <button 
                        onClick={signoutUser}
                        className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200"
                        >Sign out</button>
                </div>
            </nav>
        </>
        
    )
}