import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ToastContainer } from "react-toastify";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePage from "../../../pages/home/homepage";
import HomePageNavigation from "../../../pages/home/H_Navigation";

describe(HomePageNavigation, async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    it("[HomePage - HomePageNavigation] displays navigation content correctly", async () => {
        // Mock API response for useEffect in HomePage
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({})
        });

        // Mock useAuth for HomePage and render HomePage
        setMockUseAuth({accessToken: "fake-token", loading: false});
        render(<HomePage/>);

        // Check that the navigation content is displayed correctly
        const navigation = await screen.findByTestId("HomePageNavigation");
        expect(navigation).toBeInTheDocument();
    });


    it.each([
        ["Desktop", "HomePageNavigation-Desktop-Submit-Button"],
        ["Mobile", "HomePageNavigation-Mobile-Submit-Button"]
    ])("HomePageNavigation '%s' signout button works", async (device, testID) => {
        render(<HomePageNavigation />);

        // Mock API response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({})
        });
        
        // Spy on window location
        delete window.location;
        window.location = {href: ""}

        // Simulate user clicking the signout button (either desktop or mobile)
        const signoutButton = await screen.findByTestId(testID);
        expect(signoutButton).toBeInTheDocument();
        await userEvent.click(signoutButton);

        // Check whether the redirection was successful
        expect(window.location.href).toBe("/")
    });


    it.each([
        ["Desktop", "HomePageNavigation-Desktop-Submit-Button"],
        ["Mobile", "HomePageNavigation-Mobile-Submit-Button"]
    ])("HomePageNavigation '%s' signout button displays API error message", async (device, testID) => {
        render(
            <>
                <HomePageNavigation />
                <ToastContainer />
            </>
        );

        // Mock API response with an error message
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({message: "An unknown error has occurred."})
        });

        // Simulate user clicking the signout button (either desktop or mobile)
        const signoutButton = await screen.findByTestId(testID);
        expect(signoutButton).toBeInTheDocument();
        await userEvent.click(signoutButton);

        // Check that the correct error message is displayed
        const errorMessage = await screen.findByText("An unknown error has occurred.");
        expect(errorMessage).toBeInTheDocument();
    });


    it.each([
        ["Desktop", "HomePageNavigation-Desktop-Submit-Button"], 
        ["Mobile", "HomePageNavigation-Mobile-Submit-Button"]
    ])("HomePageNavigation '%s' signout button triggers default error because no message is returned", async (device, testID) => {
        render(
            <>
                <HomePageNavigation />
                <ToastContainer />
            </>
        );

        // Mock API response: Fails without providing an error message in the body
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({}) // no 'message' field returned
        })        

        // Simulate user clicking the signout button (either desktop or mobile)
        const signoutButton = await screen.findByTestId(testID);
        expect(signoutButton).toBeInTheDocument();
        await userEvent.click(signoutButton);

        // Since no message is returned, the default error message should be shown
        const errorMessage = await screen.findByText("Signout failed: An unexpected error occurred.");
        expect(errorMessage).toBeInTheDocument();
    });
})