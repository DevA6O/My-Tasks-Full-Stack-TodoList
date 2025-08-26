import { fixtures as test } from "../../../apiFixtures";
import { expect } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config();

test("Edit was successful", async ({ page, createTodo }) => {
    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Edit was successful",
        description: ""
    });

    // Get task id
    const container = page.getByText("Edit was successful")
        .locator("..") // Go to parent div
        .locator("..") // Go to task container
    
    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Click on the edit button
    await container.locator("button:has-text('Edit')").click();

    // Submit new todo description
    const editDescriptionInput = page.getByTestId(`EditTodo-Description-For-${taskID}`, {timeout: 5000});
    await expect(editDescriptionInput).toBeVisible();
    await editDescriptionInput.fill("Edited description");

    const editSubmitButton = page.getByTestId(`EditTodo-Submit-Button-For-${taskID}`, {timeout: 5000});
    await expect(editSubmitButton).toBeVisible();
    await editSubmitButton.click();

    // Check whether the edit was successful
    const successMessage = page.getByText("Update successful: Todo has been successfully updated.", {timeout: 5000});
    await expect(successMessage).toBeVisible();
});


test("Edit failed caused by api response mocking", async ({ page, createTodo, simulateAndMockPostRequestWithRealData }) => {
    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Edit failed caused by api response mocking",
        description: ""
    });

    // Mock api response
    await simulateAndMockPostRequestWithRealData({
        url: `${process.env.VITE_API_URL}/todo/update`,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer a-string-secret-at-least-256-bits-long" // Fake access token
        },
        data: {
            title: "Could not be edited.",
            description: "",
            todo_id: "999526e8-8f81-473c-8d62-b84207493ff8" // Fake todo_id
        }, 
        status: 400
    });

    // Get task id
    const container = page.getByText("Edit was successful")
        .locator("..") // Go to parent div
        .locator("..") // Go to task container
    
    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Click on the edit button
    await container.locator("button:has-text('Edit')").click();

    // Submit new todo description
    const editDescriptionInput = page.getByTestId(`EditTodo-Title-For-${taskID}`, {timeout: 5000});
    await expect(editDescriptionInput).toBeVisible();
    await editDescriptionInput.fill("Could not be edited.");

    const editSubmitButton = page.getByTestId(`EditTodo-Submit-Button-For-${taskID}`, {timeout: 5000});
    await expect(editSubmitButton).toBeVisible();
    await editSubmitButton.click(); 

    // Check whether the edit was not successful
    const errorMessage = page.getByText("Update failed: An unexpected error occurred. Please try again later.", {timeout: 5000});
    await expect(errorMessage).toBeVisible();
});