import { vi } from "vitest";

export const mockUseAuth = vi.fn();

vi.mock("../../context/AuthContext", () => ({
    useAuth: mockUseAuth
}));

export function setMockUseAuth({accessToken = null, loading = false} = {}) {
    mockUseAuth.mockReturnValue({accessToken, loading})
}