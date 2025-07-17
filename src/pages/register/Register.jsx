import React, { useState } from "react";

export default function Register() {
    // Define values
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: ""
    });

    // Updates the corresponding field in formData whenever an input changes
    const handleChange = (event) => {
        setFormData(prev => ({
            ...prev,
            [event.target.id]: event.target.value
        }));
    };

    // Handle the form submission and send data to the backend
    const handleSubmit = async (event) => {
        event.preventDefault(); // To not reload the page

        try {
            const response = await fetch("http://127.0.0.1:8000/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });
            const data = await response.json();

            if (response.ok && response.status === 201) {
                console.log("Register successfully")
            } else {
                console.error("Error: ", data.detail || "Unknown Error");
            };
        } catch (error) {
            console.error("Network error: ", error);
        };
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
                <h1 className="text-center text-2xl font-bold mb-6 text-gray-800">Create an Account</h1>

                <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
                    <div className="flex flex-col">
                        <label htmlFor="username" className="mb-1 text-sm font-medium text-gray-700">Username</label>
                        <input
                            type="text"
                            id="username"
                            value={formData.username}
                            onChange={handleChange}
                            required
                            maxLength={16}
                            minLength={2}
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                    </div>

                    <div className="flex flex-col">
                        <label htmlFor="email" className="mb-1 text-sm font-medium text-gray-700">E-Mail Address</label>
                        <input
                            type="email"
                            id="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                    </div>

                    <div className="flex flex-col">
                        <label htmlFor="password" className="mb-1 text-sm font-medium text-gray-700">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={formData.password}
                            onChange={handleChange}
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
                        Confirm
                    </button>
                </form>
            </div>
        </div>
    );
}
