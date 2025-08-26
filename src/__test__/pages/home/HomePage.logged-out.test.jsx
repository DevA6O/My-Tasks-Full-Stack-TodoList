import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/HomePage";


describe("HomePage - not logged in", async () => {
    it("HomePage shows a loading screen", async () => {
        setMockUseAuth({accessToken: null, loading: true});
        render(<HomePage />);
        
        // Check that the loading screen is displayed correctly
        const loadingScreenElement = await screen.getByTestId("loading-text");
        expect(loadingScreenElement).toBeInTheDocument();
    });

    it("HomePage redirect user to /login", async () => {
        // Spy on location
        delete window.location;
        window.location = {href: ""};

        // Render homepage and mock useAuth
        setMockUseAuth({accessToken: null, loading: false});
        render(<HomePage />);

        // Check whether the redirection is successful
        expect(window.location.href).toBe("/login");
    })
})