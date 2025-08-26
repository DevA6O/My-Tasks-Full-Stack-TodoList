import { expect } from "@playwright/test";
import { fixtures as test } from "../../../apiFixtures";
import dotenv from "dotenv";

dotenv.config();


test("Completion was successful", async ({ page, createTodo }) => {
    // Create todo
    await createTodo({
        title: "Completion was successful",
        description: ""
    });

    // Get the container
    const container = page.getByText("Completion was successful")
        .locator("..") // Go to parent div (Description & Title)
        .locator(".."); // Go to task-container

    // Click on complete button
    await container
        .locator("button:has-text('Completed')") // find the button with text "Completed"
        .click(); // Click on the button
    
    // Check whether the completion was successful
    const successMessage = page.getByText("Completion successful: Todo has been marked as successfully completed.");
    await expect(successMessage).toBeVisible({timeout: 5000});

    // Check whether the todo is actually marked as completed
    const completeButton = container.locator("button:has-text('Completed')")
    await expect(completeButton).toBeDisabled();

    const editButton = container.locator("button:has-text('Edit')");
    await expect(editButton).toBeDisabled();
});


test("Completion failed due to mocking", async ({ page, createTodo, simulateAndMockPostRequestWithRealData }) => {
    // Mock api response
    await simulateAndMockPostRequestWithRealData({
        url: `${process.env.VITE_API_URL}/todo/complete`,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer a-string-secret-at-least-256-bits-long" // Fake access token
        },
        data: {todo_id: "999526e8-8f81-473c-8d62-b84207493ff8"}, // Fake todo_id
        status: 400
    })

    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Completion failed due to mocking",
        description: ""
    });

    await page.getByText("Completion failed due to mocking")
        .locator("..") // Go to parent div (Description & Title)
        .locator("..") // Go to task-container
        .locator("button:has-text('Completed')") // Find the completed button
        .click(); // Click on the button

    // Check whether the completion was not successful
    const errorMessage = page.getByText(
        "Completion failed: Todo could not be marked as completed for technical reasons. Please try again later.", 
        {timeout: 5000}
    );
    await expect(errorMessage).toBeVisible();
});




test("Deletion was successful", async ({ page, createTodo }) => {
    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Deletion was successful",
        description: ""
    });

    // Click on the delete button
    await page.getByText("Deletion was successful")
        .locator("..") // Go to parent div
        .locator("..") // Go to task container
        .locator("button:has-text('Delete')") // Find delete button
        .click(); 
    
    // Check whether the deletion was successful
    const successMessage = page.getByText("Deletion successful: Todo has been successfully deleted.", {timeout: 5000});
    await expect(successMessage).toBeVisible();
});


test("Deletion failed due to mocking", async ({ page, createTodo, simulateAndMockPostRequestWithRealData }) => {
    // Mock api response
    await simulateAndMockPostRequestWithRealData({
        url: `${process.env.VITE_API_URL}/todo/delete`,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer a-string-secret-at-least-256-bits-long" // Fake access token
        },
        data: {todo_id: "999526e8-8f81-473c-8d62-b84207493ff8"}, // Fake todo_id
        status: 400
    });

    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Deletion failed due to mocking",
        description: ""
    });

    // Click on the delete button
    await page.getByText("Deletion failed due to mocking")
        .locator("..") // Go to parent div
        .locator("..") // Go to task container
        .locator("button:has-text('Delete')") // Find delete button
        .click();
    
    // Check whether the deletion was not successful
    const errorMessage = page.getByText(
        "Deletion failed: Todo could not be deleted for technical reasons. Please try again later.", 
        {timeout: 5000}
    );
    await expect(errorMessage).toBeVisible();
})