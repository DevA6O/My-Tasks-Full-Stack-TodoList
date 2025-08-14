import React from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { expect, describe, it, beforeEach, afterEach } from "vitest";
import { setMockUseAuth } from "../../helper/mockUseAuth";
import checkFormValidation from "../../helper/formValidation";
import Home from "../../../pages/home";

let titleInput;
let descriptionInput;
let submitButton;


describe("Home - Add Task", async () => {
    beforeEach(async () => {
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<Home />);
        
        // Wait until the loading screen is removed
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Define values
        titleInput = await screen.findByTestId("title-input");
        descriptionInput = await screen.findByTestId("description-input");
        submitButton = await screen.findByTestId("submit-button");

        globalThis.fetch = vi.fn();
    });

    afterEach(async () => {
        await userEvent.clear(titleInput);
        await userEvent.clear(descriptionInput);

        cleanup();
    });


    it.each([
        ["", /title is required./i],
        ["x", /title must have at least 2 characters./i],
        ["x".repeat(141), /title cannot have more than 140 characters./i]
    ])("['%s']: Add task shows an error message '%s' for title input", async (titleValue, errorMsg) => {
        await checkFormValidation(titleInput, titleValue, submitButton, errorMsg);
    });



    it("Add task shows an error message for description input field", async () => {
        const descriptionValue = "x".repeat(321);
        const errorMsg = /description cannot have more than 320 characters./i

        await checkFormValidation(descriptionInput, descriptionValue, submitButton, errorMsg);
    });



    it("Add task is successful", async () => {
        const mockFetchResponse = {
            ok: true,
            status: 201,
            json: async () => ({})
        };
        fetch.mockResolvedValueOnce(mockFetchResponse);

        await userEvent.type(titleInput, "A title");
        await userEvent.click(submitButton);

        expect(screen.queryByTestId("add-task-error")).toBeNull();
        expect(titleInput.value).toBe("");
    });



    it("Add task failed", async () => {
        const mockErrorResponse = {
            ok: false,
            status: 400,
            json: async () => ({})
        };
        fetch.mockResolvedValueOnce(mockErrorResponse);

        await userEvent.type(titleInput, "A title");
        await userEvent.click(submitButton);

        expect(screen.queryByTestId("add-task-error")).toBeInTheDocument();
    });
})