import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { expect } from "vitest";

export default async function checkFormValidation(
    inputElement, inputValue, submitButton, errorField, errorMsg
) {
    if (inputValue !== "") {
        await userEvent.type(inputElement, inputValue);
    };
    await userEvent.click(submitButton);

    // Fetch displayed error message and check whether it displayed correctly
    await waitFor(async () => {
        const errorElement = await screen.findByTestId(errorField);
        expect(errorElement).toBeInTheDocument();
        expect(errorElement).toHaveTextContent(errorMsg);
    })
};