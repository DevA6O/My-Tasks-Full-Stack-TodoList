import { expect } from "@playwright/test";
import { fixtures as test } from "../../../apiFixtures.js";

test("Registration was successful", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Register a new test user
    await page.goto("/register");

    const usernameInput = page.getByTestId("Register-Username-Input");
    const emailInput = page.getByTestId("Register-Email-Input");
    const passwordInput = page.getByTestId("Register-Password-Input");
    const submitButton = page.getByTestId("Register-Submit-Button");

    await usernameInput.fill("TestUser");
    await emailInput.fill("test.frontend2@email.com");
    await passwordInput.fill("password1234!");
    await submitButton.click();

    // Wait for the redirection
    await expect(page).toHaveURL("/", { timeout: 5000 });
}, { timeout: 10000 });


test("Registration failed: Email already exists", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Trying to create an account, but the email address is already registered
    await page.goto("/register");

    const usernameInput = page.getByTestId("Register-Username-Input");
    const emailInput = page.getByTestId("Register-Email-Input");
    const passwordInput = page.getByTestId("Register-Password-Input");
    const submitButton = page.getByTestId("Register-Submit-Button");

    await usernameInput.fill("TestUser");
    await emailInput.fill("test.frontend@email.com");
    await passwordInput.fill("password1234!");
    await submitButton.click();

    // Check whether the message is displayed correctly
    const errorMessage = page.getByTestId("Register-Email-Error");
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
}, { timeout: 10000 });


test("Registration failed: An unexpected error has occurred", async (
    { page, context, simulateAndMockPostRequestWithRealData }
) => {
    // Define test data
    const username = "TestUser";
    const email = "test.frontend5@email.com";
    const password = "password1234!";
    
    // Mock api response
    const targetURL = `${process.env.VITE_API_URL}/register`;

    await simulateAndMockPostRequestWithRealData({
        url: targetURL,
        headers: {
            "Content-Type": "application/json"
        },
        data: {
            username: username,
            email: email,
            password: password
        },
        accessToken: true,
        status: 400
    });

    // Clear the cookies
    await context.clearCookies();

    // Attempting to create an account will fail
    await page.goto("/register");

    const usernameInput = page.getByTestId("Register-Username-Input");
    const emailInput = page.getByTestId("Register-Email-Input");
    const passwordInput = page.getByTestId("Register-Password-Input");
    const submitButton = page.getByTestId("Register-Submit-Button");

    await usernameInput.fill(username);
    await emailInput.fill(email);
    await passwordInput.fill(password);
    await submitButton.click();

    // Check whether the message is displayed correctly
    const errorMessage = page.getByText(
        "Registration failed: An unexpected error has occurred. Please try again later."
    );
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
}, { timeout: 10000 });