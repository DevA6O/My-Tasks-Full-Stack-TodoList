import React, { useState } from "react"
import { toast } from "react-toastify";

import HomePageEditorModal from "./H_EditTodo";
import { HomePageEditTaskForm } from "./H_EditTodo";
import { schema } from "./H_AddTodo";
import { deleteTodoAPI, completeTodoAPI } from "./H_ManageTodos";


export default function HomePageManageAndDisplayTodos({ tasks, accessToken, setReloadTasks }) {
    const [editTask, setEditTask] = useState(null);

    const completeTodo = async (todoID) => {
        try {
            await completeTodoAPI(todoID, accessToken);
            setReloadTasks(true);
            toast.success("Completion successful: Todo has been marked as successfully completed.");
        } catch (error) {
            toast.error(error.message);
            console.error(error);
        };
    };

    const deleteTodo = async (todoID) => {
        try {
            await deleteTodoAPI(todoID, accessToken);
            setReloadTasks(true);
            toast.success("Deletion successful: Todo has been successfully deleted.");
        } catch (error) {
            toast.error(error.message);
            console.error(error);
        };
    };

    return (
        <>
            <div data-testid="HomePageManageAndDisplayTodos-Display-Tasks" 
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5 max-w-[85%]">
                {tasks.map((task) => (
                    <div 
                        key={task.id} data-testid={`task-${task.id}`}
                        className={`w-full max-w-2xl flex flex-col justify-between p-5 borderrounded shadow-lg
                            ${task.completed ? 'bg-gray-100 text-gray-400 border-gray-300' : 'border-gray-400/40'}`}
                    >   
                        <div className="flex flex-col max-w-[85%] overflow-hidden">
                            {/* Task title */}
                            <h1 className={`font-semibold text-lg leading-snug break-words ${task.completed ? 'text-gray-800/50' : 'text-gray-800'}`}>
                                {task.title}
                            </h1>

                            {/* Task description */}
                            <p className="font-sans text-lg leading-snug break-words">
                                {task.description}
                            </p>
                        </div>
                        

                        {/* Action button */}
                        <div className="flex justify-end gap-2 mt-5">
                            {/* Complete button */}
                            <button
                                onClick={() => completeTodo(task.id)}
                                disabled={task.completed}
                                data-testid={`HomePageManageAndDisplayTodos-Complete-Button-For-${task.id}`}
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
                                data-testid={`HomePageManageAndDisplayTodos-Edit-Button-For-${task.id}`}
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
                                data-testid={`HomePageManageAndDisplayTodos-Delete-Button-For-${task.id}`}
                                className={`px-3 py-1 border border-gray-400/40 rounded-md font-semibold 
                                    cursor-pointer hover:bg-red-500 hover:text-white text-red-500 transition-all ease-in-out duration-500`}>
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Editor overlay */}
            <HomePageEditorModal
                isOpen={!!editTask}
                onClose={() => setEditTask(null)}>
                <HomePageEditTaskForm
                    task={editTask}
                    validationSchema={schema}
                    accessToken={accessToken}
                    onSuccess={() => {
                        setEditTask(null);
                        setReloadTasks(true);
                    }}
                    >
                    
                </HomePageEditTaskForm>
            </HomePageEditorModal>
        </>
    )
}