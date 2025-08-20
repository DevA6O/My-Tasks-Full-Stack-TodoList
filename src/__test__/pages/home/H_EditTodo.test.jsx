import React from "react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ToastContainer } from "react-toastify";

import HomePageManageAndDisplayTodos from "../../../pages/home/H_ManageAndDisplayTodos";


describe("HomePageManageAndDisplayTodos - Edit", async () => {

    it("HomePageManageAndDisplayTodos displays the edit form overlay after clicking the 'Edit' button", async () => {
        // Mock the setReloadTasks function
        const mockSetReloadTasks = vi.fn();

        render(
            <HomePageManageAndDisplayTodos 
                tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
                accessToken={null}
                setReloadTasks={mockSetReloadTasks}
            />  
        );

        // Check and click on the edit button
        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        await userEvent.click(editButton);

        // Check that the overlay is displayed correctly
        const editorModal = await screen.findByTestId("HomePageEditorModal");
        expect(editorModal).toBeInTheDocument();

        const editorForm = await screen.findByTestId("HomePageEditTaskForm");
        expect(editorForm).toBeInTheDocument();
    })
})