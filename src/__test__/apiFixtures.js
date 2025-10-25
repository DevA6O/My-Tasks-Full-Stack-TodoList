import { test as base, expect } from "@playwright/test";

export const fixtures = base.extend({
    createTodo: async ({ page }, use) => {
        const createTodo = async ({ title, description }) => {
            // Go to homepage
            await page.goto("/");

            // Create the todo
            const titleInput = page.getByTestId("HomePageAddTodo-Title-Input");
            const descriptionInput = page.getByTestId("HomePageAddTodo-Description-Input");
            const submitButton = page.getByTestId("HomePageAddTodo-Submit-Button");
            
            await titleInput.fill(title);
            await descriptionInput.fill(description);
            await submitButton.click();

            // Check whether the success message is displayed 
            const successMessage = page.getByText("Creation successful: Todo was created successfully.");
            await expect(successMessage).toBeVisible();

            // Check whether the todo is displayed correctly
            const todoTitle = page.getByText(title);
            await expect(todoTitle).toBeVisible();

            if (description !== "") {
                const todoDescription = page.getByText(description);
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
        const simulateAndMockPostRequestWithRealData = async (
            { url, headers, data, accessToken = false, status = 400 }
        ) => {
            // Add authorization header if needed
            if (accessToken) {
                // Get the access token
                const response = await request.post(`${process.env.VITE_API_URL}/token/refresh/valid`, {
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "include"
                });

                const data = await response.json();
                const accessToken = data.access_token;

                // Add authorization header
                headers["Authorization"] = `Bearer ${accessToken}`;
            }

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