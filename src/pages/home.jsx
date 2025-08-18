import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useForm } from "react-hook-form";
import * as yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";

import LoadingScreen from "../components/LoadingScreen";
import createTodoAPI from "./todo/t_creation";
import deleteTodoAPI from "./todo/t_deletion";
import completeTodoAPI from "./todo/t_completor";

import EditorModal from "./todo/t_editor";
import { EditTaskForm } from "./todo/t_editor";

import signoutUserAPI from "./t_signout";

const schema = yup.object().shape({
    title: yup
        .string()
        .required("Title is required.")
        .min(2, "Title must have at least 2 characters.")
        .max(140, "Title cannot have more than 140 characters."),
    description: yup
        .string()
        .max(320, "Description cannot have more than 320 characters.")
});


export default function Home() {
    const { accessToken, loading: authLoading } = useAuth();
    const [tasks, setTasks] = useState([]);
    const [username, setUsername] = useState("User");
    const [isLoading, setLoading] = useState(true);
    const [reloadTasks, setReloadTasks] = useState(false);
    const [editTask, setEditTask] = useState(null);

    const {
        register: registerHome,
        handleSubmit,
        setError,
        reset,
        formState: { errors },
    } = useForm({
        resolver: yupResolver(schema),
        mode: "onBlur"
    });

    const onSubmit = async (formData) => {
        try {
            await createTodoAPI(formData, accessToken); 
            setReloadTasks(true); // Reload the tasks
            reset(); // Reset form 
        } catch (error) {
            setError("addTask", {type: "manual", message: error.message});
            console.error(error);
        };
    };

    const deleteTodo = async (todoID) => {
        try {
            await deleteTodoAPI(todoID, accessToken);
            setReloadTasks(true); // Reload the tasks
        } catch (error) {
            setError("task", {type: "server", message: error.message, id: error.todoID});
            console.error(error);
        };
    };

    const completeTodo = async (todoID) => {
        try {
            await completeTodoAPI(todoID, accessToken);
            setReloadTasks(true); // Reload the tasks
        } catch (error) {
            setError("task", {type: "server", message: error.message, id: error.todoID});
            console.error(error);
        }
    }

    const signoutUser = async () => {
        try {
            await signoutUserAPI();
            window.location.href = "/";
        } catch (error) {
            setError("signout", {type: "server", message: error.message});
            console.log(error);
        };
    }


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
                    setError("loadedTasks", {type: "server", message: "Server error: Tasks could not be loaded."});
                };
            } catch (error) {
                setError("loadedTasks", {
                    type: "server", 
                    message: "An unexpected error occurred while loading all tasks. Please try again later."
                });
            } finally{
                setLoading(false);
                setReloadTasks(false);
            };
        };

        loadTasks();
    }, [accessToken, authLoading, reloadTasks]);



    return (
        <>
            {isLoading && <LoadingScreen />}

            {!isLoading && (
                <div>
                    {/* Desktop sidebar */}
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

                    {/* iPad and iPhone navbar */}
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

                    {/* Display signout error */}
                    {errors.signout && (
                        <div className="fixed top-5 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full px-4">
                            <div className="flex items-center justify-between gap-4 p-4 bg-red-100 border border-red-400 text-red-800 rounded shadow-md">
                                <p data-testid="signout-error" className="font-bold text-sm sm:text-base break-words text-center w-full">
                                    {errors.signout.message}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Main content */}
                    <main className="flex-1 pt-40 pl-5 sm:pl-10 md:pl-10 lg:pt-30 lg:ml-80">
                        {/* Welcome message */}
                        <div>
                            <h1 className="font-semibold text-2xl md:text-3xl">Welcome back, {username}!</h1>
                            <p className="md:text-lg">Ready to do a task or add a new one?</p>

                            {/* Line */}
                            <div className="w-11/12 p-1 bg-black/20 rounded"></div>
                        </div>

                        {/* Add new Task */}
                        <div className="flex-1 mt-10 max-w-100">
                            <h1 className="font-semibold text-xl">Add a New Task</h1>
                            <p className="text-lg">Here you can add a new task.</p>

                            <form className="flex flex-col" onSubmit={handleSubmit(onSubmit)}>
                                {/* Display an add task error */}
                                {errors.addTask && (
                                    <div className="flex justify-center w-full p-5 border border-red-600 bg-red-200 rounded">
                                        <p data-testid="add-task-error" className="font-sans text-red-900 break-words text-center">
                                            {errors.addTask.message}
                                        </p>
                                    </div>
                                )}

                                {/* Title input field */}
                                <div className="flex flex-col mt-5">
                                    <label htmlFor="title" className="text-lg">
                                        <span className="text-red-500">*</span> Title <span className="text-sm">(Required)</span>
                                    </label>

                                    <input 
                                        id="title"
                                        type="text"
                                        data-testid="title-input"
                                        {...registerHome("title")}
                                        className="p-2 w-3xs md:w-100 border-2 border-gray-400 rounded"
                                    />

                                    {/* Display error message */}
                                    {errors.title && (
                                        <p className="font-sans text-red-500 max-w-[90vw] break-words">{errors.title.message}</p>
                                    )}
                                </div>
                                
                                {/* Description input field */}
                                <div className="flex flex-col mt-5">
                                    <label htmlFor="description" className="text-lg">Description</label>

                                    <input 
                                        id="description"
                                        type="text"
                                        data-testid="description-input"
                                        {...registerHome("description")}
                                        className="p-2 w-3xs md:w-100 border-2 border-gray-400 rounded"
                                    />

                                    {/* Display error message */}
                                    {errors.description && (
                                        <p className="font-sans text-red-500 max-w-[90vw] break-words">{errors.description.message}</p>
                                    )}
                                </div>

                                {/* Add task button */}
                                <div className="mt-5 text-center flex md:justify-center">
                                    <button 
                                        type="submit"
                                        data-testid="submit-button"
                                        className="px-5 py-2 text-lg text-white bg-blue-600 rounded cursor-pointer hover:bg-blue-500 transition-all ease-in-out duration-400"
                                    >
                                        Add Task
                                    </button>
                                </div>
                            </form>
                        </div>

                        {/* Line */}
                        <div className="mt-5 w-11/12 p-1 bg-black/20 rounded"></div>
                        
                        {/* Show every task the user have */}
                        <div className="mt-10">
                            <h1 className="font-semibold text-xl">Your current Tasks</h1>
                            <p className="text-lg">Here you can see all the open tasks you have.</p>
                            
                            {/* Display task errors */}
                            <div className="mt-5">
                                {errors.loadedTasks && (<p className="text-red-500 font-bold">{errors.loadedTasks.message}</p>)}
                                {!isLoading && !errors.loadedTasks && tasks.length === 0 && (
                                    <p className="text-blue-800 font-sans font-semibold text-xl max-w-11/12">
                                        Nice work! Currently you have no tasks to solve!
                                    </p>
                                )}
                            </div>
                            
                            {/* Display all tasks if there are no errors */}
                            {!isLoading && !errors.loadedTasks && tasks.length > 0 && (
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5 max-w-[85%]">
                                    {tasks.map((task) => (
                                        <div 
                                            key={task.id} data-testid={`task-${task.id}`}
                                            className={`w-full max-w-2xl flex flex-col justify-between p-5 borderrounded shadow-lg
                                                ${task.completed ? 'bg-gray-100 text-gray-400 border-gray-300' : 'border-gray-400/40'}`}
                                        >   
                                            {/* Displays task errors when an error occurrs */}
                                            {errors.task && errors.task.id == task.id && (
                                                <div className="flex justify-center items-center text-center mb-5">
                                                    <div className="px-5 py-2 border rounded bg-red-200 text-red-800">
                                                        <h1 data-testid="error-task-msg">{errors.task.message}</h1>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="flex flex-col max-w-[85%] overflow-hidden">
                                                {/* Task title */}
                                                <h1 className={`font-semibold text-lg leading-snug break-words
                                                    ${task.completed ? 'text-gray-800/50' : 'text-gray-800'}`}
                                                    data-testid="task-title">
                                                    {task.title}
                                                </h1>

                                                {/* Task description */}
                                                <p data-testid="task-description" className="font-sans text-lg leading-snug break-words">
                                                    {task.description}
                                                </p>
                                            </div>
                                            

                                            {/* Action button */}
                                            <div className="flex justify-end gap-2 mt-5">
                                                {/* Complete button */}
                                                <button
                                                    onClick={() => completeTodo(task.id)}
                                                    disabled={task.completed}
                                                    data-testid={`complete-btn-task-${task.id}`}
                                                    className={`px-3 py-1 border border-gray-400/40 rounded-md font-semibold 
                                                        transition-all ease-in-out duration-300
                                                        ${task.completed 
                                                            ? 'cursor-not-allowed text-green-400/70 bg-gray-200' 
                                                            : 'cursor-pointer hover:bg-green-400 hover:text-white text-green-400'
                                                        }`}>
                                                    Completed
                                                </button>

                                                {/* Edit button */}
                                                <button
                                                    onClick={() => setEditTask(task)}
                                                    disabled={task.completed}
                                                    data-testid={`edit-btn-task-${task.id}`}
                                                    className={`px-3 py-1 border border-gray-400/40 rounded-md font-semibold 
                                                        transition-all ease-in-out duration-300
                                                        ${task.completed 
                                                            ? 'cursor-not-allowed text-blue-500/70 bg-gray-200'
                                                            : 'cursor-pointer text-blue-500 hover:bg-blue-500 hover:text-white'
                                                        }`}>
                                                    Edit
                                                </button>

                                                {/* Delete button */}
                                                <button 
                                                    onClick={() => deleteTodo(task.id)}
                                                    data-testid={`delete-btn-task-${task.id}`}
                                                    className={`px-3 py-1 border border-gray-400/40 rounded-md font-semibold 
                                                        cursor-pointer hover:bg-red-500 hover:text-white text-red-500 transition-all ease-in-out duration-500`}>
                                                    Delete
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </main>
                    
                    {/* Editor overlay */}
                    <EditorModal
                        isOpen={!!editTask}
                        onClose={() => setEditTask(null)}>
                        <EditTaskForm
                            task={editTask}
                            validationSchema={schema}
                            accessToken={accessToken}
                            onSuccess={() => {
                                setEditTask(null);
                                setReloadTasks(true);
                            }}>
                            
                        </EditTaskForm>
                    </EditorModal>
                </div>
            )}
        </>
    )
}