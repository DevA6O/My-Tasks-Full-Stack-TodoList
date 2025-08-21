import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ToastContainer } from "react-toastify";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/homepage";
import HomePageManageAndDisplayTodos from "../../../pages/home/H_ManageAndDisplayTodos";


describe(HomePageManageAndDisplayTodos, async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    it("[HomePage - HomePageManageAndDisplayTodos] displays all tasks that the user has", async () => {
        // Mock API response for useEffect in HomePage
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                todos: [
                    {
                        id: 1,
                        title: "Todo",
                        description: "Unique description",
                        completed: false
                    }
                ],
                username: "TestUser"
            })
        });

        // Mock useAuth for HomePage and render HomePage
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<HomePage/>);

        // Check whether the main content of HomePageManageAndDisplayTodos is displayed correctly on the HomePage
        const mainContent = await screen.findByTestId("HomePageManageAndDisplayTodos-Display-Tasks");
        expect(mainContent).toBeInTheDocument();

        // Check that the task is displayed correctly
        const taskTitle = await screen.findByText("Todo");
        expect(taskTitle).toBeInTheDocument();

        const taskDescription = await screen.findByText("Unique description");
        expect(taskDescription).toBeInTheDocument();

        const completeButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Complete-Button-For-1");
        expect(completeButton).toBeInTheDocument();

        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        const deleteButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Delete-Button-For-1");
        expect(deleteButton).toBeInTheDocument();
    });


    it.each([
        [
            "Complete", "HomePageManageAndDisplayTodos-Complete-Button-For-1", 
            "Completion successful: Todo has been marked as successfully completed."
        ],

        [
            "Delete", "HomePageManageAndDisplayTodos-Delete-Button-For-1", 
            "Deletion successful: Todo has been successfully deleted."
        ]
    ])("HomePageManageAndDisplayTodos - %s a task successfully", async (type, testID, message) => {
        // Mock the setReloadTasks function
        const mockSetReloadTasks = vi.fn();

        // Mock API response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({})
        });

        // Render page and ToastContainer
        render(
            <>
                <HomePageManageAndDisplayTodos 
                    tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
                    accessToken={null}
                    setReloadTasks={mockSetReloadTasks}
                />

                <ToastContainer />
            </>
        );

        // Check and click on the button
        const button = await screen.findByTestId(testID);
        expect(button).toBeInTheDocument();

        await userEvent.click(button);

        // Check whether the action was successful
        expect(mockSetReloadTasks).toHaveBeenCalledWith(true);

        const successMessage = await screen.findByText(message);
        expect(successMessage).toBeInTheDocument();
    });


    it.each([
        [
            "Complete", "HomePageManageAndDisplayTodos-Complete-Button-For-1",
            "Completion failed: An unexpected error is occurred. Please try again later."
        ],

        [
            "Delete", "HomePageManageAndDisplayTodos-Delete-Button-For-1", 
            "Deletion failed: An unexpected error occurred. Please try again later."
        ]
    ])("HomePageManageAndDisplayTodos - Failed to '%s' a task", async (type, testID, message) => {
        // Mock the setReloadTasks function
        const mockSetReloadTasks = vi.fn();

        // Mock API response
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({})
        });

        // Render page and ToastContainer
        render(
            <>
                <HomePageManageAndDisplayTodos 
                    tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
                    accessToken={null}
                    setReloadTasks={mockSetReloadTasks}
                />

                <ToastContainer />
            </>
        );

        // Check and click on the button
        const button = await screen.findByTestId(testID);
        expect(button).toBeInTheDocument();

        await userEvent.click(button);

        // Check whether failed message is displayed correctly
        expect(mockSetReloadTasks).not.toHaveBeenCalled();

        const failedMessage = await screen.findByText(message);
        expect(failedMessage).toBeInTheDocument();
    });
})