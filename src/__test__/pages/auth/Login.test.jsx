import React from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import Login from "../../../pages/auth/Login";
import checkFormValidation from "../../helper/formValidation";

let emailInput;
let passwordInput;
let submitButton;

const DEFAULT_ERROR_MSG = /an unexpected error has occurred. please try again later./i

describe(Login, () => {
    beforeEach(async () => {
        render(<Login/>);

        emailInput = await screen.getByLabelText(/e-mail address/i);
        passwordInput = await screen.getByLabelText(/password/i);
        submitButton = await screen.getByRole("button", {name: /login/i});

        globalThis.fetch = vi.fn();
    })

    afterEach(async () => {
        await userEvent.clear(emailInput);
        await userEvent.clear(passwordInput);
        cleanup();
    })



    it("Login displays the input fields and confirm button", () => {
        expect(emailInput).not.toBeNull();
        expect(passwordInput).not.toBeNull();
        expect(submitButton).not.toBeNull();
    });



    it.each([
        ["", /email is required./i],
        ["invalidemail", /email must be a valid email address/i]
    ])("Login shows validation error for email field ('%s')", async (emailValue, errorMsg) => {
        await checkFormValidation(
            emailInput, emailValue,
            submitButton, errorMsg
        )
    });



    it.each([
        ["", /password is required/i],
        ["short", /password must have at least 8 characters./i],
        ["x".repeat(33), /password cannot have more than 32 characters./i],
    ])("Login shows validation error for password field ('%s')", async (passwordValue, errorMsg) => {
        await checkFormValidation(
            passwordInput, passwordValue,
            submitButton, errorMsg
        )
    });



    it("Redirects on a new page after the login was successful", async () => {
        const mockFetchResponse = {
            ok: true,
            status: 200,
            json: async () => ({token: "fake-token"})
        };
        
        fetch.mockResolvedValueOnce(mockFetchResponse);

        // Reset the window.location.href to test if it gets changed after login
        delete window.location;
        window.location = {href: ""};

        await userEvent.type(emailInput, "test@mail.com");
        await userEvent.type(passwordInput, "very_secret_password123");
        await userEvent.click(submitButton);
        
        // Ensure fetch was called with the correct login URL and options
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining("/login"),
            expect.any(Object)
        );
        // Check that the page was redirected after login
        expect(window.location.href).toBe("/");
    });



    it.each([
        ["", DEFAULT_ERROR_MSG],
        ["Invalid login credentials", /invalid login credentials/i]
    ])("Shows error message on failed login", async (detailMsg, findMsg) => {
        const mockErrorResponse = {
            ok: false,
            status: 401,
            json: async () => detailMsg ? {detail: detailMsg} : {}
        };

        fetch.mockResolvedValueOnce(mockErrorResponse);

        await userEvent.type(emailInput, "not.registered@email.com");
        await userEvent.type(passwordInput, "invalid_password123456");
        await userEvent.click(submitButton);

        const errorMsg = await screen.findByText(findMsg);
        expect(errorMsg).not.toBeNull();
    });



    it("Sets general error message caused by fetch / network error", async () => {
        fetch.mockResolvedValueOnce(new Error("Network error"));

        await userEvent.type(emailInput, "test@email.com");
        await userEvent.type(passwordInput, "very_secret_password123");
        await userEvent.click(submitButton);

        const errorMsg = await screen.findByText(DEFAULT_ERROR_MSG);
        expect(errorMsg).not.toBeNull();
    });
});