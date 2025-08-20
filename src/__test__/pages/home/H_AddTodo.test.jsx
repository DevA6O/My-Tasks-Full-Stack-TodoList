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

    it("HomePageAddTodo successfully adds the task", async () => {
        // Mock onSuccess
        const mockOnSuccess = vi.fn();

        // Mock API response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({})
        });

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

        // Add new todo
        await userEvent.type(titleInput, "Title");
        await userEvent.type(descriptionInput, "Description");
        await userEvent.click(submitButton);

        // Check whether the success message is displayed correctly
        const successMessage = await screen.findByText("Creation successful: Todo was created successfully.");
        expect(successMessage).toBeInTheDocument();
    });
});