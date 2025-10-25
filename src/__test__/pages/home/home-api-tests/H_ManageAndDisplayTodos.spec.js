import { expect } from "@playwright/test";
import { fixtures as test } from "../../../apiFixtures";
import dotenv from "dotenv";

dotenv.config();


test("Todo marked as completed successfully", async ({ page, createTodo }) => {
    // Go to homepage
    await page.goto("/");

    // Create todo
    await createTodo({
        title: "My todo to be marked as completed",
        description: "The completion will be successful."
    });

    // Get the container
    const container = page.getByText("My todo to be marked as completed")
        .locator("..") // Parent div
        .locator(".."); // Task container

    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Click on the complete button
    const completeButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Complete-Button-For-${taskID}`
    );
    await completeButton.click();
    
    // Check whether the completion was successful
    const successMessage = page.getByText(
        "Completion successful: Todo has been marked as successfully completed."
    );
    await expect(successMessage).toBeVisible({ timeout: 5000 });

    // // Check whether the todo is actually marked as completed

    // Define the completed button again to avoid stale element handle error
    const updatedCompleteButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Complete-Button-For-${taskID}`
    );
    await expect(updatedCompleteButton).toBeDisabled();

    // Check in addition whether the edit button is also disabled
    const editButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Edit-Button-For-${taskID}`
    );
    await expect(editButton).toBeDisabled();
}, { timeout: 10000 });


test("Todo could not be marked as completed successfully", async (
    { page, createTodo, simulateAndMockPostRequestWithRealData }
) => {
    // Go to homepage
    await page.goto("/");

    // Create todo
    await createTodo({
        title: "Try to mark todo as completed",
        description: "The completion will fail."
    });

    // Mock api response
    const targetURL = `${process.env.VITE_API_URL}/todo/complete`;

    await simulateAndMockPostRequestWithRealData({
        url: targetURL,
        headers: {
            "Content-Type": "application/json"
        },
        data: {
            title: "My todo to be marked as completed",
            description: "",
            todo_id: "00000000-0000-0000-0000-000000000000"
        },
        accessToken: true,
        status: 400
    });

    // Get the container
    const container = page.getByText("Try to mark todo as completed")
        .locator("..") // Parent div
        .locator(".."); // Task container

    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Click on the complete button
    const completeButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Complete-Button-For-${taskID}`
    );
    await completeButton.click();

    // Check whether the completion was unsuccessful
    const errorMessage = page.getByText(
        "Completion failed: Todo could not be found."
    )
    await expect(errorMessage).toBeVisible({ timeout: 2000 });

    // Check whether the complete button is still enabled

    // Relaod the page to avoid stale element handle error
    await page.reload();

    const updatedCompleteButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Complete-Button-For-${taskID}`
    );
    await expect(updatedCompleteButton).toBeEnabled();

    // Check in addition whether the edit button is also still enabled
    const editButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Edit-Button-For-${taskID}`
    );
    await expect(editButton).toBeEnabled();
}, { timeout: 10000 });




test("Todo could be deleted successful", async ({ page, createTodo }) => {
    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Todo to be deleted",
        description: "The deletion will be successful."
    });

    // Get the test id
    const container = await page.getByText("Todo to be deleted")
        .locator("..") // Parent div
        .locator(".."); // Task container

    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Click on the delete button
    const deleteButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Delete-Button-For-${taskID}`
    );
    await deleteButton.click();

    // Check whether the deletion was successful
    const successMessage = page.getByText(
        "Deletion successful: Todo has been successfully deleted."
    );
    await expect(successMessage).toBeVisible({ timeout: 5000 });

    // Check whether the todo is acutally deleted

    // Reload the page to avoid stale element handle error
    await page.reload();

    const updatedDeleteButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Delete-Button-For-${taskID}`
    );
    await expect(updatedDeleteButton).toHaveCount(0);
}, { timeout: 10000 });


test("Todo could not be deleted successfully", async (
    { page, createTodo, simulateAndMockPostRequestWithRealData }
) => {
    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Todo could not be deleted",
        description: "The deletion will be fail."
    });

    // Mock api response
    const targetURL = `${process.env.VITE_API_URL}/todo/delete`;

    await simulateAndMockPostRequestWithRealData({
        url: targetURL,
        headers: {
            "Content-Type": "application/json"
        },
        data: {
            title: "Todo could not be deleted",
            description: "",
            todo_id: "00000000-0000-0000-0000-000000000000"
        },
        accessToken: true,
        status: 400
    });

    // Get the test id
    const container = await page.getByText("Todo could not be deleted")
        .locator("..") // Parent div
        .locator(".."); // Task container

    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Click on the delete button
    const deleteButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Delete-Button-For-${taskID}`
    );
    await deleteButton.click();

    // Check whether the deletion was unsuccessful
    const errorMessage = page.getByText(
        "Deletion failed: Todo could not be found."
    );
    await expect(errorMessage).toBeVisible({ timeout: 2000 });

    // Check whether the todo is acutally not deleted

    // Reload the page to avoid stale element handle error
    await page.reload();

    const updatedDeleteButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Delete-Button-For-${taskID}`
    );
    await expect(updatedDeleteButton).toHaveCount(1);
}, { timeout: 10000 });