import React from "react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { ToastContainer } from "react-toastify";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/homepage";
import HomePageManageAndDisplayTodos from "../../../pages/home/H_ManageAndDisplayTodos";


describe("[HomePageManageAndDisplayTodos | HomePageEditTaskForm]", async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    });

    it("[HomePage - HomePageManageAndDisplayTodos] displays the edit form overlay after clicking the 'Edit' button", async () => {
        // Mock API response for useEffect in HomePage
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                todos: [
                    {
                        id: 1,
                        title: "Todo",
                        description: "",
                        completed: false
                    }
                ],
                username: "TestUser"
            })
        });

        // Mock useAuth for HomePage and render HomePage
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<HomePage/>);

        // Check and click the edit button
        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        await userEvent.click(editButton);

        // Check that the overlay is displayed correctly
        const editorModal = await screen.findByTestId("HomePageEditorModal");
        expect(editorModal).toBeInTheDocument();

        const editorForm = await screen.findByTestId("HomePageEditTaskForm");
        expect(editorForm).toBeInTheDocument();
    });


    it("HomePageEditTaskForm - Cancel editing task", async () => {
        // Mock the setReloadTasks function
        const mockSetReloadTasks = vi.fn();

        render(
            <HomePageManageAndDisplayTodos 
                tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
                accessToken={null}
                setReloadTasks={mockSetReloadTasks}
            />  
        );

        // Check and click the edit button
        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        await userEvent.click(editButton);

        // Check and click the cancel button
        const cancelButton = await screen.findByTestId("EditTodo-Cancel-Button-For-1");
        expect(cancelButton).toBeInTheDocument();

        await userEvent.click(cancelButton);

        // Check whether the modal has been closed
        await waitFor(() => {
            const editorModal = screen.queryByTestId("HomePageEditorModal");
            expect(editorModal).not.toBeInTheDocument();

            const editorForm = screen.queryByTestId("HomePageEditTaskForm");
            expect(editorForm).not.toBeInTheDocument();
        });
    });


    it.each([
        [
            "Task successfully edited",
            {
                ok: true,
                status: 200,
                json: async () => ({})
            },
            "Update successful: Todo has been successfully updated."
        ],

        [
            "Task edit failed",
            {
                ok: false,
                status: 400,
                json: async () => ({})
            },
            "Update failed: An unexpected error occurred. Please try again later."
        ]
    ])("HomePageEditTaskForm - %s", async (funcDescription, mockResponse, expectedMessage) => {
        // Mock the setReloadTasks function
        const mockSetReloadTasks = vi.fn();

        // Mock API response
        fetch.mockResolvedValueOnce(mockResponse);

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

        // Check and click the edit button
        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        await userEvent.click(editButton);

        // Click on the submit button
        const submitButton = await screen.findByTestId("EditTodo-Submit-Button-For-1");
        expect(submitButton).toBeInTheDocument();

        await userEvent.click(submitButton);

        // Check whether the expected message could be found
        const successMessage = await screen.findByText(expectedMessage);
        expect(successMessage).toBeInTheDocument();
    });



    it.each([
        ["Title", "", "", "Title is required."],
        ["Title", "x", "", "Title must have at least 2 characters."],
        ["Title", "x".repeat(141), "", "Title cannot have more than 140 characters."],
        ["Description", "xxx", "x".repeat(321), "Description cannot have more than 320 characters."]
    ])("HomePageEditTaskForm - %s returns an validation error", async (type, title, description, errorMessage) => {
        render(
            <HomePageManageAndDisplayTodos 
                tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
                accessToken={null}
                setReloadTasks={null}
            />  
        );

        // Check and click the edit button
        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        await userEvent.click(editButton);

        // Check whether the input fields exists
        const editTitleInput = await screen.findByTestId("EditTodo-Title-For-1");
        expect(editTitleInput).toBeInTheDocument();

        const editDescriptionInput = await screen.findByTestId("EditTodo-Description-For-1");
        expect(editDescriptionInput).toBeInTheDocument();

        // Clear the input fields and enter new values
        await userEvent.clear(editTitleInput);
        await userEvent.clear(editDescriptionInput);

        if (title !== "") {
            await userEvent.type(editTitleInput, title);
        };
        if (description !== "") {
            await userEvent.type(editDescriptionInput, description);
        };

        // Submit the informations
        const submitButton = await screen.findByTestId("EditTodo-Submit-Button-For-1");
        expect(submitButton).toBeInTheDocument();

        await userEvent.click(submitButton);

        // Check the validation message is displayed correctly
        let errorMessageField;

        if (type == "Title") {
            errorMessageField = await screen.findByTestId("EditTodo-Title-Error-Message");
        } else if (type == "Description") {
            errorMessageField = await screen.findByTestId("EditTodo-Description-Error-Message");
        };

        expect(errorMessageField).toHaveTextContent(errorMessage);
    }, 10000);
});