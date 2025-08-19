import React from "react";
import { cleanup, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/homepage";


describe(HomePage, async () => {
    beforeEach(async () => {
        setMockUseAuth({accessToken: "fake-token", loading: false});
        global.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    });


    it("HomePage shows elements correctly", async () => {
        // Render page and wait until the loading screen is removed
        render(<HomePage />);
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check that the loading screen has been removed correctly
        const loadingScreenElement = screen.queryByTestId("loading-text");
        expect(loadingScreenElement).not.toBeInTheDocument();

        // Check that the navigation is displayed correctly
        const homePageNavigation = await screen.findByTestId("HomePageNavigation");
        expect(homePageNavigation).toBeInTheDocument();
        
        // Check that the main content is displayed correctly
        const mainContent = await screen.findByTestId("homepage-main-content");
        expect(mainContent).toBeInTheDocument();

        // Check that the greeting is displayed correctly
        const welcomeMessage = await screen.findByText(/welcome back, user!/i);
        expect(welcomeMessage).toBeInTheDocument();
    });



    it("HomePage is loading tasks successful", async () => {
        // Mock api response from useEffect loadTasks
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

        // Render page and wait until the loading screen is removed
        render(<HomePage />);
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check that the username is displayed correctly
        const welcomeMessage = await screen.findByText(/welcome back, testuser!/i);
        expect(welcomeMessage).toBeInTheDocument();

        // Check that the todo is displayed correctly
        const todoElement = await screen.findByTestId("task-1");
        expect(todoElement).toBeInTheDocument();
    });



    it("HomePage displays an error because tasks could not be loaded successful", async () => {
        // Mock api response from useEffect loadTasks
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({})
        });

        // Render page and wait until the loading screen is removed
        render(<HomePage />);
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check that the error message is displayed correctly
        const taskErrorMessage = await screen.findByText("Server error: Tasks could not be loaded.");
        expect(taskErrorMessage).toBeInTheDocument();
    });
})