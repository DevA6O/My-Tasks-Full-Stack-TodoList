import React from "react";
import { render, screen } from "@testing-library/react";
import { expect, describe, it } from "vitest";
import { setMockUseAuth } from "../helper/mockUseAuth";
import Home from "../../pages/home";

describe("Home - not logged in", async () => {

    it("Home is loading", async () => {
        setMockUseAuth({accessToken: null, loading: true});
        render(<Home />);

        const loadingScreen = await screen.getByTestId("loading-text");
        expect(loadingScreen).toBeInTheDocument();
    });

    it("Home is redirecting user to /login", async () => {
        // Reset window location path to ""
        delete window.location;
        window.location = {href: ""};

        setMockUseAuth({accessToken: null, loading: false});
        render(<Home />);

        // Check whether the redirection is successful
        expect(window.location.href).toBe("/login");
    });
});