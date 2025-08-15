import React from "react";
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { setMockUseAuth } from "../../helper/mockUseAuth";
import Home from "../../../pages/home";



describe("Home - Load Tasks", async () => {
    beforeEach(() => {
        setMockUseAuth({accessToken: "fake-token", loading: false});
        globalThis.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    })

    it("Load tasks successful", async () => {
        const mockFetchResponse = {
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
        };
        fetch.mockResolvedValueOnce(mockFetchResponse);

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check whether task is displayed correctly
        const taskElement = await screen.findByTestId("task-1");
        expect(taskElement).toBeInTheDocument();

        // Check whether the username is displayed correctly
        const welcomeMessage = await screen.findByText(/welcome back, testuser/i);
        expect(welcomeMessage).toBeInTheDocument();
    });



    it("Load tasks failed because response is not ok", async () => {
        const mockErrorResponse = {
            ok: false,
            status: 400,
            json: async () => ({})
        };
        fetch.mockResolvedValueOnce(mockErrorResponse);

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check whether the error message is displayed correctly
        const errorMsg = await screen.findByText(/server error: tasks could not be loaded./i);
        expect(errorMsg).toBeInTheDocument();
    });



    it("Load tasks failed because a network error occurrs", async () => {
        fetch.mockRejectedValueOnce(new Error("Network error"));

        // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check whether the error message is displayed correctly
        const errorMsg = await screen.findByText(/an unexpected error occurred while loading all tasks. please try again later./i);
        expect(errorMsg).toBeInTheDocument();
    });
});