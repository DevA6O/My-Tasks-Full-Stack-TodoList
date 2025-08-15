import React from "react";
import { cleanup, render, screen, waitFor, waitForElementToBeRemoved } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setMockUseAuth } from "../../helper/mockUseAuth";
import Home from "../../../pages/home";
import userEvent from "@testing-library/user-event";


describe("Home - Delete Task", async () => {
    beforeEach(() => {
        setMockUseAuth({accessToken: "fake-token", loading: false})
        globalThis.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    })

    it("Deletion is successful", async () => {
        // Mock API request for loadTasks
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: true}],
                username: "TestUser"
            })
        });

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Mock API request for delete todo
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({})
        })

        // Check whether the delete button is in the document
        const deleteButton = await screen.findByTestId("delete-btn-task-1");
        expect(deleteButton).toBeInTheDocument();

        // Mock API request for loadTasks again
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                username: "TestUser"
            })
        })

        // Delete the todo
        await userEvent.click(deleteButton);

        // Check whether API requests are called three times
        await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));

        // Check whether the deletion was successful
        await waitFor(() => {
            const deleteButtonAfter = screen.queryByTestId("delete-btn-task-1");
            expect(deleteButtonAfter).not.toBeInTheDocument();
        });

        // Check whether the username is displayed correctly, after deletion
        const welcomeMessage = await screen.findByText(/welcome back, testuser/i);
        expect(welcomeMessage).toBeInTheDocument();
    });



    it("Delete task failed because deletion was not successful", async () => {
        // Mock API request for loadTasks
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: true}],
                username: "TestUser"
            })
        });

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Mock API request for delete todo
        fetch.mockResolvedValueOnce({
            ok: false, // <- important for this test
            status: 400,
            json: async () => ({})
        });

        // Check whether the delete button is in the document
        const deleteButton = await screen.findByTestId("delete-btn-task-1");
        expect(deleteButton).toBeInTheDocument();

        // Delete the todo
        await userEvent.click(deleteButton);

        // Check whether the todo is still exists
        await waitFor(() => {
            const deleteButtonAfter = screen.queryByTestId("delete-btn-task-1");
            expect(deleteButtonAfter).toBeInTheDocument();
        });
    });
})