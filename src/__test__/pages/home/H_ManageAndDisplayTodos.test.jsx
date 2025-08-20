import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ToastContainer } from "react-toastify";

import HomePageManageAndDisplayTodos from "../../../pages/home/H_ManageAndDisplayTodos";

describe(HomePageManageAndDisplayTodos, async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    it("HomePageManageAndDisplayTodos displays all tasks that the user has", async () => {
        render(<HomePageManageAndDisplayTodos 
            tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
            accessToken={null}
            setReloadTasks={null}
        />);

        // Check that the main content is displayed correctly
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
})