import test, { expect } from "@playwright/test";

test("Login was successful", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Login with the login data from global setup
    await page.goto("/login");

    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Check whether the success message is displayed
    const successMessage = page.getByText("Login successful! Redirecting to the homepage...")
    await expect(successMessage).toBeVisible({timeout: 5000});

    // Wait for the redirection
    await expect(page).toHaveURL("/", {timeout: 5000});
});

test("Login failed: Invalid login credentials", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Login attempt fails due to invalid login details
    await page.goto("/login");

    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "password1234");
    await page.click('button[type="submit"]');

    // Check whether the message is displayed correctly
    const errorMessage = page.getByText("Invalid login credentials.");
    await expect(errorMessage).toBeVisible({timeout: 5000});
});

test("Login failed: Validation error from backend", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Login attempt fails due to validation
    await page.goto("/login");

    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "pwd"); // too short
    await page.click('button[type="submit"]');

    // Check whether the message is displayed correctly
    const errorMessage = page.getByTestId("Login-Password-Error");
    await expect(errorMessage).toBeVisible({timeout: 5000});
});