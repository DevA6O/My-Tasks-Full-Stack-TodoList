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


test("Completion failed: Authentication - Invalid token", async ({ page, createTodo }) => {
    await page.route(`${process.env.VITE_API_URL}/todo/complete`, async route => {
        const response = await route.fetch({
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer Invalid-Token"
            },
            body: JSON.stringify({
                todo_id: "00000000-0000-0000-0000-000000000000"
            })
        })
        const realData = await response.json();

        // Return the failed api response
        await route.fulfill({
            status: 400,
            contentType: "application/json",
            body: JSON.stringify(realData)
        })
    })

    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Completion failed",
        description: ""
    });

    await page.getByText("Completion failed")
        .locator("..") // Go to parent div (Description & Title)
        .locator("..") // Go to task-container
        .locator("button:has-text('Completed')") // Find the completed button
        .click(); // Click on the button

    // Check whether the completion was not successful
    const errorMessage = page.getByText(
        "Authentication failed: An unknown error is occurred. Please try again later.", 
        {timeout: 2000}
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


test("Deletion failed: Authentication - Invalid token", async ({ page, createTodo }) => {
    await page.route(`${process.env.VITE_API_URL}/todo/delete`, async route => {
        // Do a real api request, which fails, because the data aren't correct
        const response = await route.fetch({
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer Invalid-Token"
            },
            body: JSON.stringify({
                todo_id: "00000000-0000-0000-0000-000000000000" // Invalid todo id
            })
        });
        const realData = await response.json();
        
        // Return the failed api response
        await route.fulfill({
            status: 400,
            contentType: "application/json",
            body: JSON.stringify(realData)
        });
    });

    // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Deletion failed",
        description: ""
    });

    // Click on the delete button
    await page.getByText("Deletion failed")
        .locator("..") // Go to parent div
        .locator("..") // Go to task container
        .locator("button:has-text('Delete')") // Find delete button
        .click(); 
    
    // Check whether the deletion was unsuccessful
    const errorMessage = page.getByText(
        "Authentication failed: An unknown error is occurred. Please try again later.", 
        {timeout: 2000}
    );
    await expect(errorMessage).toBeVisible();
})