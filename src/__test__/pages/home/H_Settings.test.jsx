import React from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { ToastContainer } from "react-toastify";

import { setMockUseAuth } from "../../helper/mockUseAuth";
import HomePageSettingsModal from "../../../pages/home/H_Settings";
import userEvent from "@testing-library/user-event";

let defaultInformationMock = {
    informations: {
        username: "TestUser",
        email: "test@email.com",
        sessions: [
            {
                jti_id: "00000000-0000-0000-0000-000000000000",
                ip_address: "127.0.0.1",
                browser: "Firefox",
                os: "Windows",
                current: true
            },

            {
                jti_id: "00000000-0000-0000-0000-000000000001",
                ip_address: "127.0.0.1",
                browser: "Firefox",
                os: "Windows",
                current: false
            }
        ],
    }
};


describe(HomePageSettingsModal, async () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        cleanup();
    })


    it("Settings page loads...: Loading screen is displaying correctly", async () => {
        // Mock useAuth to start the test
        setMockUseAuth({ accessToken: "fake-token", loading: true });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );

        // Check whether the loading screen is displayed correctly
        const loadingScreen = await screen.findByTestId("loading-text");
        expect(loadingScreen).toBeInTheDocument();
    });


    it("Settings page could not be loaded: Authentication is failed", async () => {
        // Spy on href to check the redirection later
        delete window.location;
        window.location = { href: "" };

        // Mock useAuth to check the redirection
        setMockUseAuth({ accessToken: false, loading: false });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );

        // Check whether the redirection works correctly
        await waitFor(() => {
            expect(window.location.href).toBe("/login");
        }, 2000);
    });


    it("Settings page loads correctly without displaying any information", async () => {
        // Mock the api response
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({})
        });

        // Mock useAuth to start the test
        setMockUseAuth({ accessToken: "fake-token", loading: false });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );

        
        // Check whether the settings page is displayed correctly
        const mainElement = await screen.findByTestId("settings-modal");
        expect(mainElement).toBeInTheDocument();

        // Check whether the informations are not displayed correctly
        const currentUsername = await screen.findByTestId("currentUsername");
        const currentEmail = await screen.findByTestId("currentEmail");
        const activeSessions = await screen.findByText("No active sessions found.");

        expect(currentUsername.value).toBe("");
        expect(currentEmail.value).toBe("");
        expect(activeSessions).toBeInTheDocument();

        // Check whether the error message is displayed correctly
        const errorMessage = await screen.findByText(
            "Settings is not accessible. Please try again later."
        );
        expect(errorMessage).toBeInTheDocument();
    });


    it("Settings page loads correctly and displays the information", async () => {
        // Mock useAuth to start the test
        setMockUseAuth({ accessToken: "fake-token", loading: false });

        // Mock the api response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => (
                defaultInformationMock
            )
        });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );
        
        // Check whether the settings page is displayed correctly
        const mainElement = await screen.findByTestId("settings-modal");
        expect(mainElement).toBeInTheDocument();

        // Check whether the informations are displayed correctly
        const currentUsername = await screen.findByTestId("currentUsername");
        const currentEmail = await screen.findByTestId("currentEmail");
        const activeSessions = await screen.findByText("This session");

        expect(currentUsername.value).toBe("TestUser");
        expect(currentEmail.value).toBe("test@email.com");
        expect(activeSessions).toBeInTheDocument();
    });


    it("Session could be revoked successful", async () => {
        // Mock useAuth to start the test
        setMockUseAuth({ accessToken: "fake-token", loading: false });

        // Mock the api response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => (
                defaultInformationMock
            )
        });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );

        // Mock all api responses first
        fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({
                informations: {
                    username: "TestUser",
                    email: "test@email.com",
                    sessions: [
                        {
                            jti_id: "00000000-0000-0000-0000-000000000000",
                            ip_address: "127.0.0.1",
                            browser: "Firefox",
                            os: "Windows",
                            current: true
                        }
                    ],
                }
            })
        });

        // Revoke the session
        const revokeButton = await screen.findByTestId(
            "revoke-btn-00000000-0000-0000-0000-000000000001"
        );
        await userEvent.click(revokeButton);

        // Check whether the session could be revoked successfully
        await waitFor(() => {
            const revokedSession = screen.queryByTestId(
            "revoke-btn-00000000-0000-0000-0000-000000000001"
            );
            expect(revokedSession).not.toBeInTheDocument();
        }, 3000)

        // Check whether the current session is still active
        const currentSession = await screen.findByText("This session");
        expect(currentSession).toBeInTheDocument();
    });


    it("Session could be successfully revoked", async () => {
        // Mock useAuth to start the test
        setMockUseAuth({ accessToken: "fake-token", loading: false });

        // Mock the api response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => (
                defaultInformationMock
            )
        });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );

        // Mock all api responses first
        fetch.mockResolvedValue({
            ok: false,
            status: 400,
            json: async () => ({})
        });

        // Revoke the session
        const revokeButton = await screen.findByTestId(
            "revoke-btn-00000000-0000-0000-0000-000000000001"
        );
        await userEvent.click(revokeButton);

        // Check whether the session could not be revoked successfully
        const errorMessage = await screen.findByText(
            "An unexpected error is occurred. Please try again later."
        );
        expect(errorMessage).toBeInTheDocument();
    });


    it("Session could not be successfully revoked: Authentication failed", async () => {
        // Spy on window.location to check the redirection later
        delete window.location;
        window.location = { href: "" };

        // Mock useAuth to start the test
        setMockUseAuth({ accessToken: "fake-token", loading: false });

        // Mock the api response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => (
                defaultInformationMock
            )
        });

        // Render the page
        render(
            <>
                <HomePageSettingsModal 
                    isOpen={true} 
                    onClose={vi.fn()} 
                />

                <ToastContainer />
            </>
        );

        // Mock all api responses first
        fetch.mockResolvedValue({
            ok: false,
            status: 401,
            json: async () => ({})
        });

        // Revoke the session
        const revokeButton = await screen.findByTestId(
            "revoke-btn-00000000-0000-0000-0000-000000000001"
        );
        await userEvent.click(revokeButton);

        // Check whether the authentication is actually failed
        expect(window.location.href).toBe("/login");
    });
});