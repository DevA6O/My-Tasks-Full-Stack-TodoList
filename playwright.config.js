import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: "./src/__test__",
  testMatch: "**/*.spec.js",
  timeout: 30000,
});