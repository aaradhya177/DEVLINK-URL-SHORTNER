import { apiRequest } from "./client";
import type {
  AnalyticsSummaryResponse,
  BreakdownResponse,
  DeviceBreakdownResponse,
  TimeseriesResponse,
} from "./types";

export function getAnalyticsSummary(
  linkId: number,
): Promise<AnalyticsSummaryResponse> {
  return apiRequest<AnalyticsSummaryResponse>(
    `/api/v1/analytics/${linkId}/summary`,
  );
}

export function getTimeseries(
  linkId: number,
  from: string,
  to: string,
): Promise<TimeseriesResponse> {
  const search = new URLSearchParams({ from, to, granularity: "day" });
  return apiRequest<TimeseriesResponse>(
    `/api/v1/analytics/${linkId}/timeseries?${search.toString()}`,
  );
}

export function getGeoBreakdown(linkId: number): Promise<BreakdownResponse> {
  return apiRequest<BreakdownResponse>(`/api/v1/analytics/${linkId}/geo`);
}

export function getDeviceBreakdown(
  linkId: number,
): Promise<DeviceBreakdownResponse> {
  return apiRequest<DeviceBreakdownResponse>(
    `/api/v1/analytics/${linkId}/devices`,
  );
}
