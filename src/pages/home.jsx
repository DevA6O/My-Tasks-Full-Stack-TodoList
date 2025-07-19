import React, { useState, useEffect, use } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Home() {
    const { isAuth, accessToken } = useAuth();
    const navigate = useNavigate();

    if (!isAuth) {
        return (
            <div className="h-screen flex flex-col justify-center items-center bg-gray-100 px-4 text-center">
                <h1 className="text-4xl sm:text-5xl font-bold text-gray-800 mb-4">
                    MyTasks - The Best Todo List
                </h1>
                <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-xl">
                    Organize your day, manage your tasks, and boost your productivity with ease.
                    No distractions. Just simplicity.
                </p>

                <div className="flex flex-col sm:flex-row gap-4">
                    <button
                        onClick={() => navigate("/tasks")}
                        className="px-6 py-3 bg-gray-800 text-white rounded-lg shadow hover:bg-gray-700 transition cursor-pointer"
                    >
                        Continue as Guest
                    </button>
                    <button
                        onClick={() => navigate("/login")}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-500 transition cursor-pointer"
                    >
                        Login
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="max-w-2xl mx-auto mt-10">
            <h1 className="text-3xl font-bold mb-4">Welcome!</h1>
        </div>
    );
}