import { expect } from "@playwright/test";
import { fixtures as test } from "../../../apiFixtures.js";


test("Add todo was successful", async ({ page, createTodo }) => {
    // Define title and description
    const todoTitle = "Test creation todo"
    const todoDescription = "Test whether the creation was successful"

    // Create the tood
    await createTodo({
        title: todoTitle,
        description: todoDescription
    });

    // Double check
    const todoTitleElement = page.getByText(todoTitle, {timeout: 5000});
    await expect(todoTitleElement).toBeVisible();

    const todoDescriptionElement = page.getByText(todoDescription, {timeout: 5000});
    await expect(todoDescriptionElement).toBeVisible();
});

test("Add todo failed: Backend validation error", async ({ page }) => {
    // Define title and description
    const todoTitle = "X";
    const todoDescription = "This todo could not be created because the title is too short.";

    // Go to homepage
    await page.goto("/");

    // Fill the input fields
    await page.fill('input[name="title"]', todoTitle);
    await page.fill('input[name="description"]', todoDescription);
    
    // Get submit button and submit the informations
    const submitButton = page.getByTestId("HomePageAddTodo-Submit-Button");
    await expect(submitButton).toBeVisible();

    await submitButton.click();

    // Check whether the creation was not successful
    const errorMessage = page.getByText("Title should have at least 2 characters", {timeout: 5000});
    await expect(errorMessage).toBeVisible();
});