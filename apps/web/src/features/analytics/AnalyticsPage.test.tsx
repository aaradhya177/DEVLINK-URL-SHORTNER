import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  getAnalyticsSummary,
  getDeviceBreakdown,
  getGeoBreakdown,
  getTimeseries,
} from "../../api/analytics";
import { AnalyticsPage } from "./AnalyticsPage";


vi.mock("recharts", () => {
  function Shell({
    children,
    label,
  }: {
    children?: ReactNode;
    label: string;
  }) {
    return <div aria-label={label}>{children}</div>;
  }

  return {
    ResponsiveContainer: ({ children }: { children?: ReactNode }) => (
      <Shell label="responsive-chart">{children}</Shell>
    ),
    LineChart: ({ children }: { children?: ReactNode }) => (
      <Shell label="line-chart">{children}</Shell>
    ),
    BarChart: ({ children }: { children?: ReactNode }) => (
      <Shell label="bar-chart">{children}</Shell>
    ),
    Line: () => <span>line-series</span>,
    Bar: () => <span>bar-series</span>,
    CartesianGrid: () => null,
    Tooltip: () => null,
    XAxis: () => null,
    YAxis: () => null,
  };
});

vi.mock("../../api/analytics", () => ({
  getAnalyticsSummary: vi.fn(),
  getTimeseries: vi.fn(),
  getGeoBreakdown: vi.fn(),
  getDeviceBreakdown: vi.fn(),
}));


const getAnalyticsSummaryMock = vi.mocked(getAnalyticsSummary);
const getTimeseriesMock = vi.mocked(getTimeseries);
const getGeoBreakdownMock = vi.mocked(getGeoBreakdown);
const getDeviceBreakdownMock = vi.mocked(getDeviceBreakdown);


describe("AnalyticsPage", () => {
  beforeEach(() => {
    getAnalyticsSummaryMock.mockResolvedValue({
      link_id: 123,
      total_clicks: 42,
      unique_clicks: null,
      unique_clicks_note: "Unique clicks are not tracked yet.",
    });
    getTimeseriesMock.mockResolvedValue({
      link_id: 123,
      granularity: "day",
      points: [{ date: "2026-06-14", clicks: 42 }],
    });
    getGeoBreakdownMock.mockResolvedValue({
      link_id: 123,
      items: [{ dimension: "US", clicks: 30 }],
    });
    getDeviceBreakdownMock.mockResolvedValue({
      link_id: 123,
      items: [
        {
          device_type: "desktop",
          browser: "Chrome",
          os: "Windows",
          clicks: 42,
        },
      ],
    });
  });

  it("renders summary, charts, and device breakdown from API data", async () => {
    renderWithProviders(<AnalyticsPage />);

    expect(await screen.findAllByText("42")).toHaveLength(2);
    expect(screen.getAllByLabelText("line-chart")).toHaveLength(1);
    expect(screen.getAllByLabelText("bar-chart")).toHaveLength(1);
    expect(screen.getByText("desktop")).toBeInTheDocument();
    expect(screen.getByText("Chrome")).toBeInTheDocument();
    expect(screen.getByText("Windows")).toBeInTheDocument();
  });
});


function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/analytics/123"]}>
        <Routes>
          <Route path="/analytics/:linkId" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
