import React from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { toast } from "react-toastify";

// Default error message for unexpected errors
const DEFAULT_ERROR_MSG = "Registration failed: An unexpected error has occurred. Please try again later.";

const schema = yup.object().shape({
    username: yup
        .string()
        .required("Username is required.")
        .min(2, "Username must have at least 2 characters.")
        .max(16, "Username cannot have more than 16 characters."),
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


async function registerUserAPI(formData, setError) {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/register`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
    });
    const data = await response.json();

    // Handle the response based on the status code

    // If registration was successful
    if (response.ok && response.status === 201) {
        toast.success(
            "Registration successful! You will be redirected to the homepage shortly."
        );

        setTimeout(() => {
            window.location.href = "/";
        }, 3000);
    }

    // If the email is already registered
    else if (response.status == 409) {
        setError("email", {type: "server", message: data.detail});
    } 

    // Handle validation errors
    else if (response.status == 422) {
        const field = data.detail?.field;
        const message = data.detail?.message || DEFAULT_ERROR_MSG;
        setError(field, {type: "server", message: message});
    } 

    // Handle other errors
    else {
        toast.error(
            data.detail || 
            "Registration failed: An unknown page error occurred. You will be redirected shortly..."
        );

        setTimeout(() => {
            window.location.reload();
        }, 3000);
    };
};



export default function Register() {
    const {
        register,
        handleSubmit,
        setError,
        formState: { errors },
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onBlur"
    });

    const onSubmit = async (formData) => {
        try {
            await registerUserAPI(formData, setError);
        } catch (error) {
            toast.error(DEFAULT_ERROR_MSG);
            console.log(error);
        };
    };

    return (
        <div data-testid="Register" className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg">
                <h1 className="text-center text-2xl font-bold mb-6 text-gray-800">Create an Account</h1>

                <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
                    <div className="flex flex-col">
                        <label htmlFor="username" className="mb-1 text-sm font-medium text-gray-700">Username</label>
                        <input
                            type="text"
                            id="username"
                            data-testid="Register-Username-Input"
                            {...register("username")}
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.username && (
                            <span 
                                data-testid="Register-Username-Error"
                                className="text-red-500 text-sm mt-1">
                                    {errors.username.message}
                            </span>
                        )}
                    </div>

                    <div className="flex flex-col">
                        <label htmlFor="email" className="mb-1 text-sm font-medium text-gray-700">E-Mail Address</label>
                        <input
                            type="email"
                            id="email"
                            data-testid="Register-Email-Input"
                            {...register("email")}
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.email && (
                            <span 
                                data-testid="Register-Email-Error"
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
                            data-testid="Register-Password-Input"
                            {...register("password")}
                            className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        />
                        {errors.password && (
                            <span 
                                data-testid="Register-Password-Error"
                                className="text-red-500 text-sm mt-1">
                                    {errors.password.message}
                            </span>
                        )}
                    </div>

                    <button
                        type="submit"
                        data-testid="Register-Submit-Button"
                        className="mt-4 bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition-all duration-300 cursor-pointer"
                    >
                        Confirm
                    </button>

                    <p className="text-center text-gray-500 mt-3 text-sm">
                        I already have an account.&nbsp;
                        <a href="/login" className="text-blue-500 hover:text-blue-700 font-semibold underline">
                                Login
                        </a>
                        .
                    </p>
                </form>
            </div>
        </div>
    );
};