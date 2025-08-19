import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePageManageAndDisplayTodos from "../../../pages/home/H_ManageAndDisplayTodos";

describe(HomePageManageAndDisplayTodos, async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    it("HomePageManageAndDisplayTodos displays all tasks that the user has", async () => {
        render(<HomePageManageAndDisplayTodos 
            tasks={[{id: 1, title: "Todo", description: "Unique description", completed: false}]}
            accessToken={null}
            setReloadTasks={null}
        />);

        // Check that the main content is displayed correctly
        const mainContent = await screen.findByTestId("HomePageManageAndDisplayTodos-Display-Tasks");
        expect(mainContent).toBeInTheDocument();

        // Check that the task is displayed correctly
        const taskTitle = await screen.findByText("Todo");
        expect(taskTitle).toBeInTheDocument();

        const taskDescription = await screen.findByText("Unique description");
        expect(taskDescription).toBeInTheDocument();

        const completeButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Complete-Button-For-1");
        expect(completeButton).toBeInTheDocument();

        const editButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Edit-Button-For-1");
        expect(editButton).toBeInTheDocument();

        const deleteButton = await screen.findByTestId("HomePageManageAndDisplayTodos-Delete-Button-For-1");
        expect(deleteButton).toBeInTheDocument();
    });
})