import React from "react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, beforeEach, afterEach, expect } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import Register from "../../../pages/auth/Register";
import checkFormValidation from "../../helper/formValidation";

let usernameInput;
let emailInput;
let passwordInput;
let submitButton;

const testUsername = "TestUser";
const testEmail = "test@email.com";
const testPassword = "very_secret_lol123+"

describe(Register, async () => {
    beforeEach(async () => {
        render(<Register />);

        usernameInput = await screen.getByLabelText(/username/i);
        emailInput = await screen.getByLabelText(/e-mail address/i);
        passwordInput = await screen.getByLabelText(/password/i);
        submitButton = await screen.getByRole("button", {name: /confirm/i});

        global.fetch = vi.fn();
    });

    afterEach(async () => {
        await userEvent.clear(usernameInput);
        await userEvent.clear(emailInput);
        await userEvent.clear(passwordInput);

        cleanup();
    });

    it("Register displays the username, email and password input", async () => {
        expect(usernameInput).toBeInTheDocument();
        expect(emailInput).toBeInTheDocument();
        expect(passwordInput).toBeInTheDocument();
    });

    

    it.each([
        ["", /username is required./i], 
        ["x", /username must have at least 2 characters./i],
        ["x".repeat(17), /username cannot have more than 16 characters./i]
    ])("Username '%s' shows an error message '%s'", async (usernameValue, errorMsg) => {
        await checkFormValidation(
            usernameInput, usernameValue,
            submitButton, errorMsg
        );
    })



    it.each([
        ["", /email is required./i],
        ["invalid-email", /email must be a valid email address./i],
    ])("Email '%s' shows an error message '%s'", async (emailValue, errorMsg) => {
        await checkFormValidation(
            emailInput, emailValue,
            submitButton, errorMsg
        )
    });



    it.each([
        ["", /password is required./i],
        ["short", /password must have at least 8 characters./i],
        ["x".repeat(33), /password cannot have more than 32 characters./i]
    ])("Password '%s' shows an error message '%s'", async (passwordValue, errorMsg) => {
        await checkFormValidation(
            passwordInput, passwordValue,
            submitButton, errorMsg
        )
    });



    it("Redirects on the homepage after successful registration", async () => {
        const mockFetchResponse = {
            ok: true,
            status: 201,
            json: async () => ({})
        };
        
        fetch.mockResolvedValueOnce(mockFetchResponse);

        // Mock window.location
        delete window.location;
        window.location = {href: ""}

        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Ensure fetch was called successful
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining("/register"),
            expect.any(Object)
        );
        // Checks whether the redirection was successful
        expect(window.location.href).toBe("/");
    });



    it("Register shows an error message when email is already registered", async () => {
        const mockErrorResponse = {
            ok: false,
            status: 409,
            json: async () => ({detail: "Email is already registered."})
        };
        fetch.mockResolvedValueOnce(mockErrorResponse);

        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        const errorMsg = await screen.findByText(/email is already registered/i);
        expect(errorMsg).toBeInTheDocument();
    });

    

    it.each([
        ["username"], ["email"], ["password"]
    ])("Backend returns an error message for input element '%s'", async (field) => {
        const mockErrorResponse = {
            ok: false,
            status: 422,
            json: async () => ({
                detail: {
                    message: "String has not been validated correctly.",
                    field: field
                }
            })
        };
        fetch.mockResolvedValueOnce(mockErrorResponse);

        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        // Defines an input mapping to retrieve the current input element
        const inputMapper = {
            username: usernameInput,
            email: emailInput,
            password: passwordInput
        };
        const inputElement = inputMapper[field];

        // Chechs whether the displayed message is placed correctly
        const container = inputElement.closest("div");
        const errorMsg = within(container).getByText(/string has not been validated correctly/i);
        expect(errorMsg).toBeInTheDocument();
    });



    it("Backend returns an unknown error message", async () => {
        const mockErrorResponse = {
            ok: false,
            status: 400,
            json: async () => ({})
        };
        fetch.mockResolvedValueOnce(mockErrorResponse);

        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        const errorMsg = await screen.findByText(/registration failed: an unknown page error occurred. you will be redirected shortly.../i);
        expect(errorMsg).toBeInTheDocument();
    });



    it("An unknown fetch / network error occurred", async () => {
        fetch.mockResolvedValueOnce(new Error("Network error"));

        await userEvent.type(usernameInput, testUsername);
        await userEvent.type(emailInput, testEmail);
        await userEvent.type(passwordInput, testPassword);
        await userEvent.click(submitButton);

        const errorMsg = await screen.findByText(/registration failed: an unexpected error has occurred. please try again later./i);
        expect(errorMsg).toBeInTheDocument();
    });
});