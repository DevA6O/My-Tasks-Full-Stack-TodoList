import React from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";

const schema = yup.object().shape({
    email: yup
        .string()
        .required("Email is required.")
        .matches(
            /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
            "Email must be a valid email address."
        ),
    password: yup
        .string()
        .required("Password is required.")
        .min(8, "Password must have at least 8 characters.")
        .max(32, "Password cannot have more than 32 characters.")
        
})

export default function Login() {
    const [generalError, setGeneralError] = React.useState("");
    const DEFAULT_ERROR_MSG = "An unexpected error occurred. Please try again."

    const {
        register: login,
        handleSubmit,
        formState: { errors }
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onBlur"
    })

    const onSubmit = async (formData) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/login`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });
            const data = await response.json();
            
            if (response.ok && response.status === 200) {
                window.location.href = "/";
            } else {
                setGeneralError(
                    data.detail || DEFAULT_ERROR_MSG
                )
            };
        } catch (error) {
            setGeneralError(DEFAULT_ERROR_MSG);
            console.error(error);
        };
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
                <h1 className="text-center text-2xl font-bold mb-6 text-gray-800">Login to Your Account</h1>

                {generalError && (
                    <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm text-center">
                        {generalError}
                    </div>
                )}

                <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
                    <div className="flex flex-col">
                        <label htmlFor="email" className="mb-1 text-sm font-medium text-gray-700">E-Mail Address</label>
                        <input
                        type="email"
                        id="email"
                        {...login("email")}
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
                        {...login("password")}
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
                        Login
                    </button>
                    
                    <p className="text-center text-gray-500 mt-3 text-sm">
                        I don't have an account.&nbsp;
                        <a href="/register" className="text-blue-500 hover:text-blue-700 font-semibold underline">
                            Register
                        </a>
                        .
                    </p>
                </form>
            </div>
        </div>
    )
}