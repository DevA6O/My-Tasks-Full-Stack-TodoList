import test, { expect } from "@playwright/test";

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
    await expect(page).toHaveURL("/", {timeout: 5000});

    // Wait for loading
    const loading = page.getByText("Loading...");
    await expect(loading).not.toBeVisible();

    // Check whether the username is displayed correctly
    const username = page.getByText("Welcome back, TestUserForTasks!", {timeout: 5000});
    await expect(username).toBeVisible();

    // Check whether the no task message is displayed and loaded correctly
    const noTaskMessage = page.getByText("Nice work! Currently you have no tasks to solve!", {timeout: 5000});
    await expect(noTaskMessage).toBeVisible();
});

// Rest is checked with unit tests...