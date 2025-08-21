import { defineConfig } from "vite";

export default defineConfig({
    test: {
        include: ["src/__test__/**/*.test.{js,ts,jsx,tsx}"],
        environment: "jsdom",
        globals: true,
        setupFiles: "./src/__test__/setupTests.js"
    }
})