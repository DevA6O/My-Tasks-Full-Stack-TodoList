import test, { expect } from "@playwright/test";

test("Signout was successful", async ({ page, context }) => {
    // Clear the cookeis (so that they are not invalid after logging out)
    await context.clearCookies();

    // Log in again
    await page.goto("/login");

    const emailInput = page.getByTestId("Login-Email-Input");
    const passwordInput = page.getByTestId("Login-Password-Input");
    const submitButton = page.getByTestId("Login-Submit");

    await emailInput.fill("test.frontend@email.com");
    await passwordInput.fill("password1234!");
    await submitButton.click();

    // Wait for redirection
    await expect(page).toHaveURL("/");

    // Click on the signout button
    const signoutButton = page.getByTestId("HomePageNavigation-Desktop-Submit-Button");
    await expect(signoutButton).toBeVisible();

    await signoutButton.click();

    // Check whether the signout was successful
    await expect(page).toHaveURL("/login");
}, { timeout: 10000 });


test("Signout failed: No authentication token was found", async ({ page, context }) => {
    // Go to homepage
    await page.goto("/");

    // Get signout button
    const signoutButton = page.getByTestId("HomePageNavigation-Desktop-Submit-Button");
    await expect(signoutButton).toBeVisible();

    // Delete cookie to cause it to fail
    await context.clearCookies();

    // Click on the signout button
    await signoutButton.click();

    // Check whether the error message is displayed
    const errorMessage = page.getByText("Authentication failed");
    await expect(errorMessage).toBeVisible();
}, { timeout: 10000 });