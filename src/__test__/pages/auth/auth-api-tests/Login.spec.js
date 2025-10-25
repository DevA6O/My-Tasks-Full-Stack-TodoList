import { expect } from "@playwright/test";
import { fixtures as test } from "../../../apiFixtures.js";

test("Login was successful", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Login with the login data from global setup
    await page.goto("/login");

    const emailInput = page.getByTestId("Login-Email-Input");
    const passwordInput = page.getByTestId("Login-Password-Input");
    const submitButton = page.getByTestId("Login-Submit");

    await emailInput.fill("test.frontend@email.com");
    await passwordInput.fill("password1234!");
    await submitButton.click();

    // Check whether the success message is displayed
    const successMessage = page.getByText("Login successful! Redirecting to the homepage...")
    await expect(successMessage).toBeVisible({ timeout: 5000 });

    // Wait for the redirection
    await expect(page).toHaveURL("/", { timeout: 5000 });
}, { timeout: 10000 });


test("Login failed: Invalid login credentials", async ({ page, context }) => {
    // Clear the cookies
    await context.clearCookies();

    // Login attempt fails due to invalid login details
    await page.goto("/login");

    const emailInput = page.getByTestId("Login-Email-Input");
    const passwordInput = page.getByTestId("Login-Password-Input");
    const submitButton = page.getByTestId("Login-Submit");

    await emailInput.fill("test.frontend@email.com");
    await passwordInput.fill("password1234");
    await submitButton.click();

    // Check whether the message is displayed correctly
    const errorMessage = page.getByText("Invalid login credentials.");
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
}, { timeout: 10000 });


test("Login failed: An unexpected error has occurred", async (
    { page, context, simulateAndMockPostRequestWithRealData }
) => {
    // Clear the cookies
    await context.clearCookies();

    // Define test data
    const email = "test.frontend@email.com";
    const password = "password1234!";

    // Mock api response
    const targetURL = `${process.env.VITE_API_URL}/login`;

    await simulateAndMockPostRequestWithRealData({
        url: targetURL,
        headers: {
            "Content-Type": "application/json"
        },
        data: {
            email: email,
            password: password
        },
        accessToken: true,
        status: 400
    });

    // Login attempt fails
    await page.goto("/login");

    const emailInput = page.getByTestId("Login-Email-Input");
    const passwordInput = page.getByTestId("Login-Password-Input");
    const submitButton = page.getByTestId("Login-Submit");

    await emailInput.fill(email);
    await passwordInput.fill(password);
    await submitButton.click();

    // Check whether the message is displayed correctly
    const errorMessage = page.getByText(
        "Login failed: An unexpected error has occurred. Please try again later."
    );
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
}, { timeout: 10000 });