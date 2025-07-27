import React from "react";

export default function Login() {
    return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
                <h1 className="text-center text-2xl font-bold mb-6 text-gray-800">Login to Your Account</h1>

                <form className="flex flex-col gap-4">
                <div className="flex flex-col">
                    <label htmlFor="email" className="mb-1 text-sm font-medium text-gray-700">E-Mail Address</label>
                    <input
                    type="email"
                    id="email"
                    required
                    className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    />
                </div>

                <div className="flex flex-col">
                    <label htmlFor="password" className="mb-1 text-sm font-medium text-gray-700">Password</label>
                    <input
                    type="password"
                    id="password"
                    required
                    minLength={8}
                    maxLength={32}
                    className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    />
                </div>

                <button
                    type="submit"
                    className="mt-4 bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition-all duration-300 cursor-pointer"
                >
                    Login
                </button>
                </form>
            </div>
        </div>
    )
}