import { chromium, expect } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config();
const baseURL = process.env.VITE_BASE_URL;

async function globalSetup() {
    // Set up browser
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Start registration
    await page.goto(`${baseURL}/register`);
    await page.fill('input[name="username"]', "TestFrontendUser");
    await page.fill('input[name="email"]', "test.frontend@email.com");
    await page.fill('input[name="password"]', "password1234!");
    await page.click('button[type="submit"]');

    // Wait for the redirection
    await expect(page).toHaveURL("http://localhost:5173/", {timeout: 5000});

    // Save the status in which you are logged in for each test
    await page.context().storageState({path: "./authLogin.json"});

    // Close the browser after the registration
    await browser.close();
};

export default globalSetup;