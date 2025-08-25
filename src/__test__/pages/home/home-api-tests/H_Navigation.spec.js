import test, { expect } from "@playwright/test";

test("Signout was successful", async ({ page, context }) => {
    // Clear the cookeis (so that they are not invalid after logging out)
    await context.clearCookies();

    // Log in again
    await page.goto("/login");

    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Wait for redirection
    await expect(page).toHaveURL("/", {timeout: 5000});

    // Click on the signout button
    const signoutButton = page.getByTestId("HomePageNavigation-Desktop-Submit-Button");
    await expect(signoutButton).toBeVisible();

    await signoutButton.click();

    // Check whether the action was successful
    await expect(page).toHaveURL("/login", {timeout: 5000});
});

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
    const errorMessage = page.getByText("Authorization failed: Authentication token could not be found.", {timeout: 5000})
    await expect(errorMessage).toBeVisible();
});