import React from "react";
import { set, useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { toast } from "react-toastify";

// Default error message for unexpected errors
const DEFAULT_ERROR_MSG = "Login failed: An unexpected error has occurred. Please try again later.";


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
});



async function loginUserAPI(formData, setError) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/login`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
    });
    const data = await response.json();
    
    // Handle the response based on the status code

    // If Login was successful
    if (response.ok && response.status === 200) {
        window.location.href = "/";
        toast.success("Login successful! Redirecting to the homepage...");
    }
    // Handle validation error occurred
    else if (response.status === 422) {
        const field = data.detail?.field;
        const message = data.detail?.message || DEFAULT_ERROR_MSG;
        setError(field, {type: "server", message: message});
    }
    // Handle other errors
    else {
        toast.error(data.detail || DEFAULT_ERROR_MSG);
    };
};



export default function Login() {
    const {
        register: login,
        handleSubmit,
        setError,
        formState: { errors }
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onBlur"
    });

    const onSubmit = async (formData) => {
        try {
            await loginUserAPI(formData, setError);

            setTimeout(() => {
                window.location.href = "/";
            }, 3000);
        } catch (error) {
            toast.error(DEFAULT_ERROR_MSG);
            console.error(error);
        };
    };

    return (
        <div data-testid="Login" className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
                <h1 className="text-center text-2xl font-bold mb-6 text-gray-800">Login to Your Account</h1>

                <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
                    <div className="flex flex-col">
                        <label htmlFor="email" className="mb-1 text-sm font-medium text-gray-700">E-Mail Address</label>
                        <input
                        type="email"
                        id="email"
                        data-testid="Login-Email-Input"
                        {...login("email")}
                        className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.email && (
                            <span
                                data-testid="Login-Email-Error"
                                className="text-red-500 text-sm mt-1">
                                    {errors.email.message}
                            </span>
                        )}
                    </div>

                    <div className="flex flex-col">
                        <label htmlFor="password" className="mb-1 text-sm font-medium text-gray-700">Password</label>
                        <input
                        type="password"
                        id="password"
                        data-testid="Login-Password-Input"
                        {...login("password")}
                        className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.password && (
                            <span
                                data-testid="Login-Password-Error"
                                className="text-red-500 text-sm mt-1">
                                    {errors.password.message}
                                </span>
                        )}
                    </div>

                    <button
                        type="submit"
                        data-testid="Login-Submit"
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
    );
};