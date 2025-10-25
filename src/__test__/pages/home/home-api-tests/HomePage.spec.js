import { fixtures as test } from "../../../apiFixtures";
import { expect } from "@playwright/test";


test("Loading tasks was successful (with tasks)", async ({ page, createTodo }) => {
    // Go to homepgae
    await page.goto("/");

    // Create a todo
    await createTodo({
        title: "Loading tasks was successful - with tasks",
        description: ""
    });

    // Check whether tasks are displayed correctly
    const task = page.getByText("Loading tasks was successful - with tasks");
    await expect(task).toBeVisible({ timeout: 5000 });
}, { timeout: 10000 })


test("Loading tasks was successful (without tasks)", async ({ page, context }) => {
    // Clear cookies
    await context.clearCookies();

    // Register new
    await page.goto("/register");

    await page.fill('input[name="username"]', "TestUserForTasks");
    await page.fill('input[name="email"]', "test.frontend.tasks@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Wait for redirection
    await expect(page).toHaveURL("/", { timeout: 5000 });

    // Wait for loading
    const loading = page.getByText("Loading...");
    await expect(loading).not.toBeVisible();

    // Check whether the username is displayed correctly
    const username = page.getByText("Welcome back, TestUserForTasks!");
    await expect(username).toBeVisible({ timeout: 5000 });

    // Check whether the no task message is displayed and loaded correctly
    const noTaskMessage = page.getByText("Nice work! Currently you have no tasks to solve!");
    await expect(noTaskMessage).toBeVisible({ timeout: 5000 });
}, { timeout: 10000 });