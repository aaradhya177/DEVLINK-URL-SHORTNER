import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CreateLinkForm } from "./CreateLinkForm";
import { createLink } from "../../api/links";


vi.mock("qrcode.react", () => ({
  QRCodeCanvas: ({ value }: { value: string }) => (
    <div aria-label="qr-preview">{value}</div>
  ),
}));

vi.mock("../../api/links", async () => {
  const actual = await vi.importActual<typeof import("../../api/links")>(
    "../../api/links",
  );
  return {
    ...actual,
    createLink: vi.fn(),
  };
});


const createLinkMock = vi.mocked(createLink);


describe("CreateLinkForm", () => {
  beforeEach(() => {
    createLinkMock.mockReset();
  });

  it("submits normalized form values to the link API", async () => {
    createLinkMock.mockResolvedValue({
      id: 1,
      workspace_id: null,
      owner_id: "user-1",
      short_code: "launch",
      destination_url: "https://example.com",
      title: "Launch",
      is_password_protected: true,
      is_active: true,
      flagged_reason: null,
      checked_at: null,
      expires_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    renderWithQueryClient(<CreateLinkForm />);

    await userEvent.type(screen.getByLabelText(/long url/i), "https://example.com");
    await userEvent.type(screen.getByLabelText(/title/i), "Launch");
    await userEvent.type(screen.getByLabelText(/custom alias/i), "launch");
    await userEvent.click(screen.getByLabelText(/password protect/i));
    await userEvent.type(screen.getByLabelText(/link password/i), "secret-pass");
    expect(screen.getByLabelText("qr-preview")).toHaveTextContent("/r/launch");
    await userEvent.click(screen.getByRole("button", { name: /create link/i }));

    await waitFor(() => expect(createLinkMock).toHaveBeenCalledTimes(1));
    expect(createLinkMock.mock.calls[0][0]).toEqual({
      destination_url: "https://example.com",
      title: "Launch",
      custom_alias: "launch",
      password: "secret-pass",
      expires_at: null,
      strip_tracking_params: true,
    });
  });

  it("shows a friendly creation error", async () => {
    createLinkMock.mockRejectedValue(new Error("alias conflict"));
    renderWithQueryClient(<CreateLinkForm />);

    await userEvent.type(screen.getByLabelText(/long url/i), "https://example.com");
    await userEvent.click(screen.getByRole("button", { name: /create link/i }));

    expect(
      await screen.findByText(/unable to create link/i),
    ).toBeInTheDocument();
  });
});


function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}
