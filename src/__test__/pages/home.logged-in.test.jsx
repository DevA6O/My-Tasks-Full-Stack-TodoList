import React from "react";
import { render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { expect, describe, it, beforeEach } from "vitest";
import { setMockUseAuth } from "../helper/mockUseAuth";
import Home from "../../pages/home";

describe("Home - logged in", () => {
    beforeEach(async () => {
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<Home />);
        
        // Wait until the loading screen is removed
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));
    });

    it("Home displays elements correctly", async () => {
        // Check whether loading screen is not in the document
        expect(screen.queryByTestId("loading-text")).not.toBeInTheDocument();
        
        // Check whether some elements are loaded correctly
        const myTasksTitle = await screen.findAllByText(/mytasks/i);
        const welcomeBackMessage = await screen.findByText(/welcome back, user!/i);

        expect(myTasksTitle.length).toBeGreaterThan(0);
        expect(welcomeBackMessage).toBeInTheDocument();
    });
});