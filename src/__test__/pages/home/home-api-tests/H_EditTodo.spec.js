import { fixtures as test } from "../../../apiFixtures";
import { expect } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config();

test("Todo successfully edited", async ({ page, createTodo }) => {
    // // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "My todo to be edited",
        description: "This todo will be edited in the test."
    });

    // Get the container with the created todo
    const container = page.getByText("My todo to be edited")
        .locator("..") // Parent div
        .locator(".."); // Task container

    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Open the edit form by clicking the edit button
    const editButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Edit-Button-For-${taskID}`
    );
    await editButton.click();

    // Edit the todo
    const editTitleInput = page.getByTestId(`EditTodo-Title-For-${taskID}`);
    const editDescriptionInput = page.getByTestId(`EditTodo-Description-For-${taskID}`);
    const editSubmitButton = page.getByTestId(`EditTodo-Submit-Button-For-${taskID}`);

    await editTitleInput.fill("Edited todo title");
    await editDescriptionInput.fill("Edited todo description.");
    await editSubmitButton.click();

    // Check the success message is displayed
    const successMessage = page.getByText("Update successful: Todo has been successfully updated.");
    await expect(successMessage).toBeVisible();

    // Check whether the edited todo is displayed correctly
    const editedTodoTitle = page.getByText("Edited todo title");
    const editedTodoDescription = page.getByText("Edited todo description.");

    await expect(editedTodoTitle).toBeVisible();
    await expect(editedTodoDescription).toBeVisible();
}, { timeout: 10000 });


test("Todo could not be edited successfully", async ({ page, createTodo, simulateAndMockPostRequestWithRealData }) => {
    // // Go to homepage
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "My todo to be edited",
        description: "The edit will fail."
    });
   
    // Mock api response
    const targetURL = `${process.env.VITE_API_URL}/todo/update`;

    await simulateAndMockPostRequestWithRealData({
        url: targetURL,
        headers: {
            "Content-Type": "application/json",
        },
        data: {
            title: "Todo could not be edited.",
            description: "",
            todo_id: "00000000-0000-0000-0000-000000000000"
        },
        accessToken: true,
        status: 400
    });

    // Get the container with the created todo
    const container = page.getByText("My todo to be edited")
        .locator("..") // Parent div
        .locator(".."); // Task container
    
    const taskTestID = await container.getAttribute("data-testid");
    const taskID = taskTestID?.split("task-")[1];

    // Open the edit form by clicking the edit button
    const editButton = page.getByTestId(
        `HomePageManageAndDisplayTodos-Edit-Button-For-${taskID}`
    );
    await editButton.click();

    // Try to edit the todo
    const editTitleInput = page.getByTestId(`EditTodo-Title-For-${taskID}`);
    const editDescriptionInput = page.getByTestId(`EditTodo-Description-For-${taskID}`);
    const editSubmitButton = page.getByTestId(`EditTodo-Submit-Button-For-${taskID}`);

    await editTitleInput.fill("My new edited title");
    await editDescriptionInput.fill("The edit will fail by clicking submit.");
    await editSubmitButton.click()

    // Check whether the edit was unsuccessful
    const errorMessage = page.getByText("Update failed: Todo could not be found.", { timeout: 2000 });
    await expect(errorMessage).toBeVisible();

    // Reload the page to see whether the todo has been changed
    await page.reload();

    // Check whether the created todo has not been changed
    const editedTodoTitle = page.getByText("My todo to be edited");
    const editedTodoDescription = page.getByText("The edit will fail.");

    await expect(editedTodoTitle).toBeVisible({ timeout: 2000 });
    await expect(editedTodoDescription).toBeVisible({ timeout: 2000 });
}, { timeout: 10000 });