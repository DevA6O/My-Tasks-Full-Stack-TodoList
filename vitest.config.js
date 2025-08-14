import { defineConfig } from "vite";

export default defineConfig({
    test: {
        environment: "jsdom",
        globals: true,
        setupFiles: "./src/__test__/setupTests.js"
    }
})