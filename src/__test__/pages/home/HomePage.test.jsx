import React from "react";
import { render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/homepage";


describe(HomePage, async () => {
    beforeEach(async () => {
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<HomePage />);
        
        await waitForElementToBeRemoved(() => screen.queryByTestId("loading-text"));
    });

    it("HomePage shows elements correctly", async () => {
        // Check that the loading screen has been removed correctly
        const loadingScreenElement = screen.queryByTestId("loading-text");
        expect(loadingScreenElement).not.toBeInTheDocument();

        // Check that the navigation is displayed correctly
        const homePageNavigation = await screen.findByTestId("HomePageNavigation");
        expect(homePageNavigation).toBeInTheDocument();
        
        // Check that the main content is displayed correctly
        const mainContent = await screen.findByTestId("homepage-main-content");
        expect(mainContent).toBeInTheDocument();

        // Check that the greeting is displayed correctly
        const welcomeMessage = await screen.findByText(/welcome back, user!/i);
        expect(welcomeMessage).toBeInTheDocument();
    });
})