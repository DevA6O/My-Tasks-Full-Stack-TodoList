import { defineConfig } from '@playwright/test';
import dotenv from "dotenv";

dotenv.config();

export default defineConfig({
  testDir: "./src/__test__",
  testMatch: "**/*.spec.js",
  timeout: 30000,
  globalSetup: "./global-setup.js",

  use: {
    baseURL: process.env.VITE_BASE_URL,
    storageState: "./authLogin.json"
  }
});