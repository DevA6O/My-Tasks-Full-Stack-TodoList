import { expect } from "@playwright/test";
import { fixtures as test } from "../../../apiFixtures.js";


test("Todo successfully added", async ({ page }) => {
    // Define a title and a description
    const title = "My todo";
    const description = "My description";

    // Go to the homepage
    await page.goto("/");

    // Create the todo
    const titleInput = page.getByTestId("HomePageAddTodo-Title-Input");
    const descriptionInput = page.getByTestId("HomePageAddTodo-Description-Input");
    const submitButton = page.getByTestId("HomePageAddTodo-Submit-Button");

    await titleInput.fill(title);
    await descriptionInput.fill(description);
    await submitButton.click();

    // Check whether the creation was successful
    const createdTodoTitle = page.getByText(title);
    const createdTodoDescription = page.getByText(description);

    await expect(createdTodoTitle).toBeVisible();
    await expect(createdTodoDescription).toBeVisible();
})


test("Todo could not be added successfully", async ({ page }) => {
    // Define a title and a description
    const title = "X";
    const description = "The todo could not be added successfully because the title is too short.";

    // Go to the homepage
    await page.goto("/");

    // Create the todo
    const titleInput = page.getByTestId("HomePageAddTodo-Title-Input");
    const descriptionInput = page.getByTestId("HomePageAddTodo-Description-Input");
    const submitButton = page.getByTestId("HomePageAddTodo-Submit-Button");

    await titleInput.fill(title);
    await descriptionInput.fill(description);
    await submitButton.click();

    // Check whether the error message is displayed correctly
    const errorMessage = page.getByText("Title should have at least 2 characters");
    await expect(errorMessage).toBeVisible();
});