import React from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";

const schema = yup.object().shape({
    username: yup
        .string()
        .min(2, "Username must have at least 2 characters.")
        .max(16, "Username coudn't have more than 16 characters.")
        .required("Username is required."),
    email: yup
        .string()
        .matches(
            /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
            "Email must be a valid email address."
        )
        .required("Email is required."),
    password: yup
        .string()
        .min(8, "Password must have at least 8 characters.")
        .max(32, "Password cannot have more than 32 characters.")
        .required("Password is required.")
})

export default function Register() {
    const {
        register,
        handleSubmit,
        setError,
        formState: { errors },
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onTouched"
    });

    const onSubmit = async (formData) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/register`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });
            const data = await response.json();

            if (response.ok && response.status === 201) {
                window.location.href = "/"; // Reload html and the memory
            } else { // Display error message 
                const field = data.detail.field;
                
                if (field !== null) {
                    setError(field, {
                        type: "server",
                        "message": data.detail.message
                    });
                } else {
                    window.alert("Server error: Please try again later.");
                    window.location.reload();
                };
            };

        } catch (error) {
            console.error("Network error: ", error);
        }
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
                <h1 className="text-center text-2xl font-bold mb-6 text-gray-800">Create an Account</h1>

                <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
                    <div className="flex flex-col">
                        <label htmlFor="username" className="mb-1 text-sm font-medium text-gray-700">Username</label>
                        <input
                            type="text"
                            id="username"
                            {...register("username")}
                            required
                            maxLength={16}
                            minLength={2}
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.username && (
                            <span className="text-red-500 text-sm mt-1">{errors.username.message}</span>
                        )}
                    </div>

                    <div className="flex flex-col">
                        <label htmlFor="email" className="mb-1 text-sm font-medium text-gray-700">E-Mail Address</label>
                        <input
                            type="email"
                            id="email"
                            {...register("email")}
                            required
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.email && (
                            <span className="text-red-500 text-sm mt-1">{errors.email.message}</span>
                        )}
                    </div>

                    <div className="flex flex-col">
                        <label htmlFor="password" className="mb-1 text-sm font-medium text-gray-700">Password</label>
                        <input
                            type="password"
                            id="password"
                            {...register("password")}
                            required
                            minLength={8}
                            maxLength={32}
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.password && (
                            <span className="text-red-500 text-sm mt-1">{errors.password.message}</span>
                        )}
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
