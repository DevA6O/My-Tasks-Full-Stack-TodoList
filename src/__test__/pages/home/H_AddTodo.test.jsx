import React from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ToastContainer } from "react-toastify";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/homepage";
import HomePageAddTodo from "../../../pages/home/H_AddTodo";


describe(HomePageAddTodo, async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    })

    it("HomePageAddTodo loads correctly in HomePage", async () => {
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<HomePage />);
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Check whether HomePageAddTodo is loading correctly
        const homePageAddTodoContent = await screen.findByTestId("HomePageAddTodo");
        expect(homePageAddTodoContent).toBeInTheDocument();
    });


    it.each([
        [
            "HomePageAddTodo successfully adds the task",
            {
                ok: true,
                status: 200,
                json: async () => ({})
            },
            "Creation successful: Todo was created successfully."
        ],

        [
            "HomePageAddTodo was unable to add a task",
            {
                ok: false,
                status: 400,
                json: async () => ({})
            },
            "Creation failed: An unexpected error occurred. Please try again later."
        ]
    ])("%s", async (funcDescription, mockResponse, displayedMessage) => {
        // Mock onSuccess
        const mockOnSuccess = vi.fn();

        // Mock API response
        fetch.mockResolvedValueOnce(mockResponse);

        render(
            <>
                <HomePageAddTodo 
                    accessToken={null}
                    onSuccess={mockOnSuccess}
                />

                <ToastContainer />
            </>   
        );

        // Check whether the input fields are present
        const titleInput = await screen.findByTestId("HomePageAddTodo-Title-Input");
        expect(titleInput).toBeInTheDocument();

        const descriptionInput = await screen.findByTestId("HomePageAddTodo-Description-Input");
        expect(descriptionInput).toBeInTheDocument();

        const submitButton = await screen.findByTestId("HomePageAddTodo-Submit-Button");
        expect(submitButton).toBeInTheDocument();

        // Enter the information and submit it
        await userEvent.type(titleInput, "Title");
        await userEvent.type(descriptionInput, "Description");
        await userEvent.click(submitButton);

        // Check whether the message is displayed correctly
        const message = await screen.findByText(displayedMessage);
        expect(message).toBeInTheDocument();
    });
});