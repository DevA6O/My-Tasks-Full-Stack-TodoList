import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
import { expect } from "vitest";

export default async function checkFormValidation(
    inputElement, inputValue, submitButton, errorMsg
) {
    if (inputValue !== "") {
        await userEvent.type(inputElement, inputValue);
    };
    await userEvent.click(submitButton);

    // Fetch displayed error message and check whether it displayed correctly
    const displayedErrorMsg = await screen.findByText(errorMsg);
    expect(displayedErrorMsg).toBeInTheDocument();
};