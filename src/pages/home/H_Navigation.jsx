import React, { useState } from "react";
import { toast } from "react-toastify";
import HomePageSettingsModal from "./H_Settings";

export async function signoutUserAPI() {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/signout`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        credentials: "include"
    });
    
    if (!response.ok) {
        const json = await response.json();

        const error = new Error(
            typeof json === "string"
                ? json
                : json?.detail || "Signout failed: An unexpected error occurred."
        );
        error.status_code = response?.status;
        throw error;
    };

    return true;
};


export default function HomePageNavigation() {
    const [settings, setSettings] = useState(null);

    const signoutUser = async () => {
        // Define a default error message for signout
        const signoutErrorMsg = "Signout failed: An unexpected error has occurred. " +
        "Please try again later."

        try {
            const success = await signoutUserAPI();

            // Check whether the signout was successful
            if (success) {
                window.location.href = "/";
            } else {
                toast.error(signoutErrorMsg);
            };
        } catch (error) {
            // Check whether the session is expired already
            if (error?.status_code == 401) {
                localStorage.setItem("authError", true);

                window.location.href = "/login"; return;
            };
            
            // If an unknown error occurs
            toast.error(error?.message || signoutErrorMsg);
            console.log(error);
        };
    };

    return (
        <>
            <div data-testid="HomePageNavigation">
                {/* Desktop - Sidebar */}
                <aside className="hidden lg:flex flex-col justify-between fixed top-0 left-0 h-screen items-center w-64 p-16 bg-gray-500/20 border-r-4 border-gray-300">
                    <h1 className="font-bold text-2xl">MyTasks</h1>

                    <div className="flex flex-col font-sans">
                        <button
                            onClick={() => setSettings(true)}
                            className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200"
                            >Settings</button>
                        <button 
                            data-testid="HomePageNavigation-Desktop-Submit-Button"
                            onClick={signoutUser}
                            className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200"
                            >Sign out</button>
                    </div>
                </aside>

                {/* iPhone & iPads - Navbar */}
                <nav className="lg:hidden fixed top-0 left-0 right-0 flex flex-col sm:flex-row justify-between p-6 sm:p-10 bg-gray-200 border-b-2">
                    <h1 className="font-bold text-2xl">MyTasks</h1>

                    <div className="flex gap-4 mt-4 sm:mt-0">
                        <button
                            onClick={() => setSettings(true)}
                            className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200"
                            >Settings</button>
                        <button 
                            data-testid="HomePageNavigation-Mobile-Submit-Button"
                            onClick={signoutUser}
                            className="cursor-pointer hover:text-blue-500 transition-all ease-in duration-200"
                            >Sign out</button>
                    </div>
                </nav>
            </div>

            <HomePageSettingsModal
                isOpen={!!settings}
                onClose={() => setSettings(null)}>
            </HomePageSettingsModal>
        </>
    )
}