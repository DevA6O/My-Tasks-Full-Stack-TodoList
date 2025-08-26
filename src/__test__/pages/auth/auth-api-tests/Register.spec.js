import { test, expect } from "@playwright/test";

test("Registration was successful", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Register a new test user
    await page.goto("/register");

    await page.fill('input[name="username"]', "TestUser");
    await page.fill('input[name="email"]', "test.frontend2@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Wait for the redirection
    await expect(page).toHaveURL("/", {timeout: 5000});
});

test("Registration failed: Email already exists", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Trying to create an account, but the email address is already registered
    await page.goto("/register");

    await page.fill('input[name="username"]', "TestUser");
    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Check whether the message is displayed correctly
    const errorMessage = page.getByTestId("Register-Email-Error");
    await expect(errorMessage).toBeVisible({timeout: 5000});
});

test("Registration failed: Validation error from backend", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Attempting to create an account will fail due to validation
    await page.goto("/register");

    await page.fill('input[name="username"]', "X"); // <- too short
    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Check whether the message is displayed correctly
    const errorMessage = page.getByTestId("Register-Username-Error");
    await expect(errorMessage).toBeVisible({timeout: 5000});
});