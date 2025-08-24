import test, { expect } from "@playwright/test";

// This file does not create any to-dos to check whether they are loaded correctly. 
// This is done separately by the responsible Add Todo test file.

test("Loading tasks was successful (without tasks)", async ({ page }) => {
    // Go to homepage
    await page.goto("/");

    // Check whether the username is displayed correctly
    const username = page.getByText("Welcome back, TestFrontendUser!");
    await expect(username).toBeVisible();

    // Check whether the no task message is displayed and loaded correctly
    const noTaskMessage = page.getByText("Nice work! Currently you have no tasks to solve!");
    await expect(noTaskMessage).toBeVisible();
});

// Rest is checked with unit tests...