import React from "react";
import userEvent from "@testing-library/user-event";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import Login from "../../../pages/auth/Login";

let emailInput;
let passwordInput;
let confirmBtn;

describe(Login, () => {
    beforeEach(() => {
        render(<Login/>);

        emailInput = screen.getByLabelText(/e-mail address/i);
        passwordInput = screen.getByLabelText(/password/i);
        confirmBtn = screen.getByRole("button", {name: /login/i})

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
        expect(confirmBtn).not.toBeNull();
    });



    it.each([
        ["", /email is required./i],
        ["invalidemail", /email must be a valid email address/i]
    ])("Login shows validation error for email field ('%s')", async (emailValue, errorMsg) => {
        if (emailValue !== "") {
            await userEvent.type(emailInput, emailValue);
        }
        await userEvent.click(confirmBtn);

        const emailError = await screen.findByText(errorMsg);
        expect(emailError).not.toBeNull();
    });



    it.each([
        ["", /password is required/i],
        ["short", /password must have at least 8 characters./i],
        ["x".repeat(33), /password cannot have more than 32 characters./i],
    ])("Login shows validation error for password field ('%s')", async (passwordValue, errorMsg) => {
        await userEvent.type(emailInput, "test@email.com");

        if (passwordValue !== "") {
            await userEvent.type(passwordInput, passwordValue);
        } 
        await userEvent.click(confirmBtn); 

        const passwordError = await screen.findByText(errorMsg);
        expect(passwordError).not.toBeNull();
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
        await userEvent.click(confirmBtn);
        
        // Ensure fetch was called with the correct login URL and options
        expect(fetch).toHaveBeenCalledWith(
            expect.stringContaining("/login"),
            expect.any(Object)
        );
        // Check that the page was redirected after login
        expect(window.location.href).toBe("/");
    });



    it.each([
        ["", /an unexpected error occurred. please try again./i],
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
        await userEvent.click(confirmBtn);

        const errorMsg = await screen.findByText(findMsg);
        expect(errorMsg).not.toBeNull();
    });
});