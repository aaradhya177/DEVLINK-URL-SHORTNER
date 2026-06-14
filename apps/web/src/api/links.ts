import { apiRequest, apiUrl } from "./client";
import type {
  BulkLinkCreateRequest,
  BulkLinkCreateResponse,
  LinkCreate,
  LinkResponse,
  LinkUpdate,
} from "./types";

export interface ListLinksParams {
  limit: number;
  offset: number;
  includeInactive?: boolean;
}

export function listLinks(params: ListLinksParams): Promise<LinkResponse[]> {
  const search = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
    include_inactive: String(params.includeInactive ?? false),
  });
  return apiRequest<LinkResponse[]>(`/api/v1/links?${search.toString()}`);
}

export function createLink(payload: LinkCreate): Promise<LinkResponse> {
  return apiRequest<LinkResponse>("/api/v1/links", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateLink(
  linkId: number,
  payload: LinkUpdate,
): Promise<LinkResponse> {
  return apiRequest<LinkResponse>(`/api/v1/links/${linkId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteLink(linkId: number): Promise<LinkResponse> {
  return apiRequest<LinkResponse>(`/api/v1/links/${linkId}`, {
    method: "DELETE",
  });
}

export function bulkCreateLinks(
  payload: BulkLinkCreateRequest,
): Promise<BulkLinkCreateResponse> {
  return apiRequest<BulkLinkCreateResponse>("/api/v1/links/bulk", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getQrImageUrl(
  shortCode: string,
  imageFormat: "png" | "svg" = "png",
): string {
  const search = new URLSearchParams({ image_format: imageFormat });
  return apiUrl(`/api/v1/links/${shortCode}/qr?${search.toString()}`);
}
