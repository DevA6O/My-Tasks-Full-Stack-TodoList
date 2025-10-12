import React from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ToastContainer } from "react-toastify";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/HomePage";
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
            "Todo has been successfully added",
            {
                ok: true,
                status: 200,
                json: async () => ({})
            },
            "Creation successful: Todo was created successfully."
        ],

        [
            "Todo could not be added successfully",
            {
                ok: false,
                status: 400,
                json: async () => ({})
            },
            "Creation failed: An unexpected error has occurred. Please try again later."
        ]
    ])("%s", async (_, mockResponse, displayedMessage) => {
        // Mock API response
        fetch.mockResolvedValueOnce(mockResponse);

        render(
            <>
                <HomePageAddTodo 
                    accessToken={null}
                    onSuccess={vi.fn()}
                />

                <ToastContainer />
            </>   
        );

        // Get the input fields
        const titleInput = await screen.findByTestId("HomePageAddTodo-Title-Input");
        const descriptionInput = await screen.findByTestId("HomePageAddTodo-Description-Input");

        // Fill the input fields
        await userEvent.type(titleInput, "Title");
        await userEvent.type(descriptionInput, "Description");

        // Click on the submit button
        const submitButton = await screen.findByTestId("HomePageAddTodo-Submit-Button");
        await userEvent.click(submitButton);

        // Check whether the message is displayed correctly
        const message = await screen.findByText(displayedMessage);
        expect(message).toBeInTheDocument();
    });


    it("Authentication failed when adding a new todo", async () => {
        // Reset location to check the redirection
        delete window.location;
        window.location = { href: "" };

        // Mock API response
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 401,
            json: async () => ({})
        });

        render(
            <>
                <HomePageAddTodo 
                    accessToken={null}
                    onSuccess={vi.fn()}
                />

                <ToastContainer />
            </>   
        );

        // Get the input fields
        const titleInput = await screen.findByTestId("HomePageAddTodo-Title-Input");
        const descriptionInput = await screen.findByTestId("HomePageAddTodo-Description-Input");

        // Fill the input fields
        await userEvent.type(titleInput, "Title");
        await userEvent.type(descriptionInput, "Description");

        // Click on the submit button
        const submitButton = await screen.findByTestId("HomePageAddTodo-Submit-Button");
        await userEvent.click(submitButton);

        // Check whether the redirection worked
        expect(window.location.href).toBe("/login");
    });


    it.each([
        ["Title", "", "", "Title is required."],
        ["Title", "x", "", "Title must have at least 2 characters."],
        ["Title", "x".repeat(141), "", "Title cannot have more than 140 characters."],
        ["Description", "xxx", "x".repeat(321), "Description cannot have more than 320 characters."]
    ])
    (
        "Todo could not be created because a validation error occurred for the input '%s'.", 
        async (_, titleValue, descriptionValue, errorMsg) => {
            render(<HomePageAddTodo accessToken={null} onSuccess={null}/>);

            // Get the input fields and the submit button
            const titleInput = await screen.findByTestId("HomePageAddTodo-Title-Input");
            const descriptionInput = await screen.findByTestId("HomePageAddTodo-Description-Input");
            const submitButton = await screen.findByTestId("HomePageAddTodo-Submit-Button");

            // Check which field needs to be filled in
            if (titleValue !== "") {
                await userEvent.type(titleInput, titleValue);
            };
            if (descriptionValue !== "") {
                await userEvent.type(descriptionInput, descriptionValue);
            };
            
            // Click on the submit button
            await userEvent.click(submitButton);

            // Check whether the error message is displayed correctly
            const displayedErrorMessage = await screen.findByText(errorMsg);
            expect(displayedErrorMessage).toBeInTheDocument();
        }, 10000
    );
});