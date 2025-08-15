import React from "react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, afterEach, expect } from "vitest";
import { cleanup, render, screen, waitFor, waitForElementToBeRemoved } from "@testing-library/react";
import { setMockUseAuth } from "../../helper/mockUseAuth";
import Home from "../../../pages/home";


describe("Home - Edit Task", async () => {
    beforeEach(() => {
        setMockUseAuth({accessToken: "fake-token", loading: false})
        globalThis.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    })

    it("Edit task successful", async () => {
        const mockLoadTasksWithoutEdit = {
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: false}],
                username: "TestUser"
            })
        };

        const mockEditTask = {
            ok: true,
            status: 200,
            json: async () => ({})
        };

        const mockLoadTasksWithEdit = {
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "New title", description: "New description", completed: false}],
                username: "TestUser"
            })
        };

        fetch
            .mockImplementationOnce(() => Promise.resolve(mockLoadTasksWithoutEdit)) // 1. useEffect
            .mockImplementationOnce(() => Promise.resolve(mockEditTask))            // 2. Edit call
            .mockImplementationOnce(() => Promise.resolve(mockLoadTasksWithEdit));  // 3. useEffect reload

        // // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));

        // Click on edit button
        const editButton = await screen.findByTestId("edit-btn-task-1");
        expect(editButton).toBeEnabled();

        await userEvent.click(editButton);

        // Get input fields and submit button
        const editTitleInput = await screen.findByTestId("edit-title-task-1");
        expect(editTitleInput).toBeInTheDocument();

        const editDescriptionInput = await screen.findByTestId("edit-description-task-1");
        expect(editDescriptionInput).toBeInTheDocument();

        const submitButton = await screen.findByTestId("edit-submit-btn-task-1");
        expect(submitButton).toBeInTheDocument();

        // Enter the edit informations and click on the submit button
        await userEvent.clear(editTitleInput);
        await userEvent.type(editTitleInput, "New title", {delay: 1});

        await userEvent.clear(editDescriptionInput);
        await userEvent.type(editDescriptionInput, "New description", {delay: 1});

        await userEvent.click(submitButton);

        // Check whether API requests are called three times 
        await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));

        // Check whether the editing was successful
        await waitFor(() => {
            const editedTitle = screen.getByTestId("task-title");
            expect(editedTitle).toHaveTextContent("New title");

            const editedDescription = screen.getByTestId("task-description");
            expect(editedDescription).toHaveTextContent("New description");
        })
    });



    it("Edit task failed because editing was not successful", async () => {
        const mockLoadTasksWithoutEdit = {
            ok: true,
            status: 200,
            json: async () => ({
                todos: [{id: 1, title: "Title", description: "", completed: false}],
                username: "TestUser"
            })
        };

        const mockEditTask = {
            ok: false,
            status: 400,
            json: async () => ({})
        };

        fetch
            .mockImplementationOnce(() => Promise.resolve(mockLoadTasksWithoutEdit)) // 1. useEffect
            .mockImplementationOnce(() => Promise.resolve(mockEditTask))            // 2. Edit call

        // // Render home to trigger useEffect and wait for the loading screen to be removed
        render(<Home />)
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));
        
        // Click on edit button
        const editButton = await screen.findByTestId("edit-btn-task-1");
        expect(editButton).toBeEnabled();

        await userEvent.click(editButton);

        // Get input fields and submit button
        const editTitleInput = await screen.findByTestId("edit-title-task-1");
        expect(editTitleInput).toBeInTheDocument();

        const editDescriptionInput = await screen.findByTestId("edit-description-task-1");
        expect(editDescriptionInput).toBeInTheDocument();

        const submitButton = await screen.findByTestId("edit-submit-btn-task-1");
        expect(submitButton).toBeInTheDocument();

        // Enter the edit informations and click on the submit button
        await userEvent.type(editTitleInput, "New title", {delay: 1});
        await userEvent.type(editDescriptionInput, "New description", {delay: 1});
        await userEvent.click(submitButton);

        // Check whether API requests are called three times 
        await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));

        // Check whether the edit was not successful
        await waitFor(() => {
            const failedEditedTitle = screen.getByTestId("task-title");
            expect(failedEditedTitle).toHaveTextContent("Title");

            const failedEditedDescription = screen.getByTestId("task-description");
            expect(failedEditedDescription).toHaveTextContent("");
        })
    })
})