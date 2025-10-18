import React from "react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, afterEach, expect } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { ToastContainer } from "react-toastify";

import Register from "../../../pages/auth/Register";
import checkFormValidation from "../../helper/formValidation";


// Define global variables
let usernameInput;
let emailInput;
let passwordInput;
let submitButton;

const testUsername = "TestUser";
const testEmail = "test@email.com";
const testPassword = "very_secret_lol123+"

describe(Register, async () => {
    beforeEach(async () => {
        render(
            <>
                <Register />

                <ToastContainer />
            </>
        );

        // Defines the input elements and submit button
        usernameInput = await screen.getByTestId("Register-Username-Input");
        emailInput = await screen.getByTestId("Register-Email-Input");
        passwordInput = await screen.getByTestId("Register-Password-Input");
        submitButton = await screen.getByTestId("Register-Submit-Button");

        global.fetch = vi.fn();
    });

    afterEach(async () => {
        cleanup();
    });

    it("Register displays the content correctly", async () => {
        const registerComponent = await screen.getByTestId("Register");
        expect(registerComponent).toBeInTheDocument();

        // Checks whether the input fields and submit button are displayed
        expect(usernameInput).toBeInTheDocument();
        expect(emailInput).toBeInTheDocument();
        expect(passwordInput).toBeInTheDocument();
        expect(submitButton).toBeInTheDocument();
    });


    it.each([
        ["", "Username is required."], 
        ["x", "Username must have at least 2 characters."],
        ["x".repeat(17), "Username cannot have more than 16 characters."]
    ])("Username '%s' shows an error message '%s'", async (usernameValue, errorMsg) => {
        await checkFormValidation(
            usernameInput, usernameValue, submitButton, "Register-Username-Error", errorMsg
        );
    });

    it.each([
        ["", "Email is required."],
        ["invalid-email", "Email must be a valid email address."],
    ])("Email '%s' shows an error message '%s'", async (emailValue, errorMsg) => {
        await checkFormValidation(
            emailInput, emailValue, submitButton, "Register-Email-Error", errorMsg
        );
    });

    it.each([
        ["", "Password is required."],
        ["short", "Password must have at least 8 characters."],
        ["x".repeat(33), "Password cannot have more than 32 characters."]
    ])("Password '%s' shows an error message '%s'", async (passwordValue, errorMsg) => {
        await checkFormValidation(
            passwordInput, passwordValue, submitButton, "Register-Password-Error", errorMsg
        );
    });


    it.each([
        ["Message is displayed correclty", true],
        ["Redirection is working", false]
    ])("Registration was successful: %s", async (_, action) => {
        // Save the current setTimeout
        const realSetTimeout = global.setTimeout;

        // Check whether the redirection should be checked
        if (!action) {
            // Prevents waiting for setTimeout
            global.setTimeout = (cb, _ms, ...args) => {
                try { 
                    cb(...args); 
                } catch (e) {
                    // let test fail normally 
                }
                return 0; // fake id
            };

            // Spy on location to check the redirection later
            delete window.location;
            window.location = { href: "" };
        };

        // Mock API response
        fetch.mockResolvedValueOnce({
            ok: true,
            status: 201,
            json: async () => ({})
        });

        // Simulate user input and submit the form
        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Ensure fetch was called successful
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining("/register"),
            expect.any(Object)
        );

        // Checks whether the success message is displayed
        if (action) {
            const successMessage = await screen.findByText(
                "Registration successful! You will be redirected to the homepage shortly."
            );
            expect(successMessage).toBeInTheDocument();
        } else {
            expect(window.location.href).toBe("/");

            // Restore normal state from setTimeout
            global.setTimeout = realSetTimeout;   
        };
    });


    it("Register shows an error message when the email is already registered", async () => {
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 409,
            json: async () => ({detail: "Email is already registered."})
        });

        // Simulate user input and submit the form
        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Check whether the error message is displayed
        const errorMsg = await screen.findByText("Email is already registered.");
        expect(errorMsg).toBeInTheDocument();
    });

    

    it.each([
        ["username", "Register-Username-Error"], 
        ["email", "Register-Email-Error"], 
        ["password", "Register-Password-Error"]
    ])("Backend returns a validation error for %s input field", async (field, errorField) => {
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 422,
            json: async () => ({
                detail: {
                    message: `${field} has not been validated correctly.`,
                    field: field
                }
            })
        });

        // Simulate user input and submit the form
        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Checks whether the displayed message is placed correctly
        const errorElement = await screen.getByTestId(errorField);
        expect(errorElement).toBeInTheDocument();
        expect(errorElement).toHaveTextContent(`${field} has not been validated correctly.`);
    });



    it.each([
        ["Error message is displayed correctly", true],
        ["Page reload is working correclty", false]
    ])("Backend returns an unknown error: %s", async (_, action) => {
        // Save the current setTimeout
        const realSetTimeout = global.setTimeout;

        // Check whether the page reload should be checked
        if (!action) {
            // Prevents waiting for setTimeout
            global.setTimeout = (cb, _ms, ...args) => {
                try { 
                    cb(...args); 
                } catch (e) {
                    // let test fail normally 
                }
                return 0; // fake id
            };

            // Spy on location to check the reload later
            delete window.location;
            window.location = { reload: vi.fn() };
        };

        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({})
        });

        // Simulate user input and submit the form
        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Check whether the error message is displayed
        if (action) {
            const errorMsg = await screen.findByText(
                "Registration failed: An unknown page error occurred. You will be redirected shortly..."
            );
            expect(errorMsg).toBeInTheDocument();
        } else {
            expect(window.location.reload).toHaveBeenCalled();

            // Restore normal state from setTimeout
            global.setTimeout = realSetTimeout;   
        };
    });



    it("An unknown error has occurred", async () => {
        fetch.mockResolvedValueOnce(new Error("Network error"));

        // Simulate user input and submit the form
        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Check whether the error message is displayed
        const errorMsg = await screen.findByText(
            "Registration failed: An unexpected error has occurred. Please try again later."
        );
        expect(errorMsg).toBeInTheDocument();
    });
});