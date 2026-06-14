export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LinkCreate {
  destination_url: string;
  workspace_id?: string | null;
  title?: string | null;
  custom_alias?: string | null;
  password?: string | null;
  expires_at?: string | null;
  strip_tracking_params: boolean;
}

export interface LinkUpdate {
  destination_url?: string | null;
  title?: string | null;
  custom_alias?: string | null;
  password?: string | null;
  clear_password?: boolean;
  is_active?: boolean;
  expires_at?: string | null;
  strip_tracking_params?: boolean;
}

export interface LinkResponse {
  id: number;
  workspace_id: string | null;
  owner_id: string | null;
  short_code: string;
  destination_url: string;
  title: string | null;
  is_password_protected: boolean;
  is_active: boolean;
  flagged_reason: string | null;
  checked_at: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BulkLinkCreateRequest {
  urls: string[];
  workspace_id?: string | null;
  strip_tracking_params: boolean;
}

export interface BulkLinkResult {
  index: number;
  status: "created" | "deduped" | "error" | string;
  url: string;
  link: LinkResponse | null;
  error: string | null;
}

export interface BulkLinkCreateResponse {
  results: BulkLinkResult[];
}

export interface AnalyticsSummaryResponse {
  link_id: number;
  total_clicks: number;
  unique_clicks: number | null;
  unique_clicks_note: string;
}

export interface TimeseriesPoint {
  date: string;
  clicks: number;
}

export interface TimeseriesResponse {
  link_id: number;
  granularity: "day";
  points: TimeseriesPoint[];
}

export interface BreakdownItem {
  dimension: string;
  clicks: number;
}

export interface BreakdownResponse {
  link_id: number;
  items: BreakdownItem[];
}

export interface DeviceBreakdownItem {
  device_type: string;
  browser: string;
  os: string;
  clicks: number;
}

export interface DeviceBreakdownResponse {
  link_id: number;
  items: DeviceBreakdownItem[];
}

export interface ApiErrorBody {
  detail?: string | { requires_password?: boolean };
}
