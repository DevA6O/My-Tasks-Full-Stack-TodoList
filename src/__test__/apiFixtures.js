import { test as base, expect } from "@playwright/test";

export const fixtures = base.extend({
    createTodo: async ({ page }, use) => {
        const createTodo = async ({ title, description }) => {
            // Go to homepage
            await page.goto("/");

            // Fill the input fields
            await page.fill('input[name="title"]', title);
            await page.fill('input[name="description"]', description);
            
            // Submit the informations
            const submitButton = page.getByTestId("HomePageAddTodo-Submit-Button", {timeout: 5000});
            await expect(submitButton).toBeVisible();
            
            await submitButton.click();

            // Check whether the success message is displayed 
            const successMessage = page.getByText("Creation successful: Todo was created successfully.", {timeout: 5000});
            await expect(successMessage).toBeVisible();

            // Check whether the todo is displayed correctly
            const todoTitle = page.getByText(title, {timeout: 5000});
            await expect(todoTitle).toBeVisible();

            if (description !== "") {
                const todoDescription = page.getByText(description, {timeout: 5000});
                await expect(todoDescription).toBeVisible();
            };
        };

        await use(createTodo);
    },

    simulateAndMockPostRequestWithRealData: async ({ page, request }, use) => {
        /**
            * This fixture performs a real POST request to the backend API to retrieve a real response,
            * and then simulates the same endpoint for future requests during the test.
            *
            * It is used to:
            * - Simulate a server response (e.g., an error),
            * - but still want to use the real response structure from the backend.
        */
        const simulateAndMockPostRequestWithRealData = async ({ url, headers, data, status = 400 }) => {
            // Do a real api request
            const realResponse = await request.post(url, {
                headers: headers,
                data: data
            });
            const realData = await realResponse.json();
            
            // Mock API response
            await page.route(url, async route => {
                await route.fulfill({
                    status: status,
                    contentType: "application/json",
                    body: JSON.stringify(realData)
                });
            });
        };

        await use(simulateAndMockPostRequestWithRealData);
    }
});