import React from "react";
import { vi, describe, it, beforeEach, expect, afterEach } from "vitest";
import { cleanup, render, screen, waitFor, waitForElementToBeRemoved } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { setMockUseAuth } from "../../helper/mockUseAuth";
import Home from "../../../pages/home";



describe("Home - Complete Task", async () => {
    beforeEach(() => {
        setMockUseAuth({accessToken: "fake-token", loading: false})
        globalThis.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    })

    it("Complete task successful", async () => {
        // Mock API response for loading tasks: returns one task that is not yet completed
        const mockLoadTasksCompletedFalse = {
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: false}],
                username: "TestUser",
            })
        };
        
        // Mock API response for completing a task: only the "ok" status matters here
        // since the client will reload the task list afterward
        const mockCompleteOk = {
            ok: true,
            status: 200,
            json: async () => ({})
        };

        // Mock API response for reloading tasks after a completion: 
        // returns the same task, but now marked as completed
        const mockLoadTasksCompletedTrue = {
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: true}],
                username: "TestUser",
            })
        };

        // Mock the API responses
        fetch
            .mockResolvedValueOnce(mockLoadTasksCompletedFalse)
            .mockResolvedValueOnce(mockCompleteOk)
            .mockResolvedValueOnce(mockLoadTasksCompletedTrue);

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check the state before starting the actual test
        const completeButton = await screen.findByTestId("complete-btn-task-1");
        const editButton = await screen.findByTestId("edit-btn-task-1");
        expect(completeButton).toBeEnabled();
        expect(editButton).toBeEnabled();

        // Complete the todo
        await userEvent.click(completeButton);

        // Check whether API requests are called three times
        await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));

        // Check the state after test
        await waitFor(() => {
            const completeButtonAfter = screen.getByTestId("complete-btn-task-1");
            const editButtonAfter = screen.getByTestId("edit-btn-task-1");
            expect(completeButtonAfter).toBeDisabled();
            expect(editButtonAfter).toBeDisabled();
        })
    });



    it("Complete task failed because completion was not successful", async () => {
        // Mock API request for loadTasks
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: false}],
                username: "TestUser"
            })
        });

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Mock API request for complete todo
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({})
        })

        // Complete todo finally
        const completeButton = await screen.findByTestId("complete-btn-task-1");
        expect(completeButton).toBeEnabled();

        await userEvent.click(completeButton);

        // Check whether API requests are called two times
        await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));

        // Check whether the completion was not successful
        const completeButtonAfter = await screen.findByTestId("complete-btn-task-1");
        expect(completeButtonAfter).toBeEnabled();

        const errorMsg = await screen.findByTestId("error-task-msg");
        expect(errorMsg).toBeInTheDocument();
    });
})