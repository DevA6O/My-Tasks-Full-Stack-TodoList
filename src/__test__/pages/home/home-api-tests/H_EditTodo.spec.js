import { fixtures as test } from "../../../apiFixtures";
import { expect } from "@playwright/test";

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
})