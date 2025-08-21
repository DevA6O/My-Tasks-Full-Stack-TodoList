import React from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, render, screen, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ToastContainer } from "react-toastify";

import Login from "../../../pages/auth/Login";
import checkFormValidation from "../../helper/formValidation";

let emailInput;
let passwordInput;
let submitButton;

const DEFAULT_ERROR_MSG = "Login failed: An unexpected error has occurred. Please try again later.";
const testEmail = "test@email.com";
const testPassword = "very_secret_lol123+";

describe(Login, async () => {
    beforeEach(async () => {
        render(
            <>
                <Login />

                <ToastContainer />
            </>
        );

        // Defines the input elements and submit button
        emailInput = await screen.getByTestId("Login-Email-Input");
        passwordInput = await screen.getByTestId("Login-Password-Input");
        submitButton = await screen.getByTestId("Login-Submit");

        global.fetch = vi.fn();
    });

    afterEach(async () => {
        cleanup();
    });


    it("Login displays the content correctly", async () => {
        const loginComponent = await screen.getByTestId("Login");
        expect(loginComponent).toBeInTheDocument();

        expect(emailInput).toBeInTheDocument();
        expect(passwordInput).toBeInTheDocument();
        expect(submitButton).toBeInTheDocument();
    });


    it.each([
        ["", "Email is required."],
        ["invalidemail", "Email must be a valid email address."]
    ])("Login shows validation error for email field ('%s')", async (emailValue, errorMsg) => {
        await checkFormValidation(emailInput, emailValue, submitButton, "Login-Email-Error", errorMsg);
    });


    it.each([
        ["", "Password is required."],
        ["short", "Password must have at least 8 characters."],
        ["x".repeat(33), "Password cannot have more than 32 characters."],
    ])("Login shows validation error for password field ('%s')", async (passwordValue, errorMsg) => {
        await checkFormValidation(passwordInput, passwordValue, submitButton, "Login-Password-Error", errorMsg);
    });


    it("Login submits the form with valid data", async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({token: "fake-token"})
        });

        // Enter the information and submit it
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Ensure fetch was called with the correct login URL and options
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining("/login"),
            expect.any(Object)
        );

        // Check whether the success message is displayed
        const successMessage = await screen.findByText("Login successful! Redirecting to the homepage...");
        expect(successMessage).toBeInTheDocument();
    });


    it.each([
        ["", DEFAULT_ERROR_MSG],
        ["Invalid login credentials", "Invalid login credentials"]
    ])("Shows error message on failed login ('%s')", async (detailMsg, displayedMessage) => {
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 401,
            json: async () => detailMsg ? {detail: detailMsg} : {}
        });

        // Mock location -> this is needed to prevent the test from failing due to the redirect
        delete window.location;
        window.location = { href: '' };

        // Enter the information and submit it
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Check whether the displayed message is placed correctly
        const errorMsg = await screen.findByText(displayedMessage);
        expect(errorMsg).toBeInTheDocument();
    });



    it.each([
        ["email", "Login-Email-Error"], 
        ["password", "Login-Password-Error"]
    ])("Backend returns a validation error for input field '%s'", async (field, errorField) => {
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 422,
            json: async () => ({
                detail: {
                    message: "String has not been validated correctly.",
                    field: field
                }
            })
        });

        // Enter the information and submit it
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Check whether the displayed message is placed correctly
        const errorElement = await screen.getByTestId(errorField);
        expect(errorElement).toBeInTheDocument();
        expect(errorElement).toHaveTextContent("String has not been validated correctly.")
    })



    it("Display error message caused by fetch / network error", async () => {
        fetch.mockResolvedValueOnce(new Error("Network error"));

        // Enter the information and submit it
        await userEvent.type(emailInput, "test@email.com");
        await userEvent.type(passwordInput, "very_secret_password123");
        await userEvent.click(submitButton);

        // Check whether the message is displayed
        const errorMsg = await screen.findByText(DEFAULT_ERROR_MSG);
        expect(errorMsg).toBeInTheDocument();
    });
});