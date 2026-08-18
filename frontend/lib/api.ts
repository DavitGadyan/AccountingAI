/** Typed API client.
 *
 *  One place that knows about auth headers and error shape. Every call goes through
 *  `request`, so a 401 handled once is handled everywhere.
 */

import type {
  CurrentUser,
  Determination,
  EngagementDashboard,
  Engagement,
  ExtractedField,
  Filing,
  GateCheck,
  OpenItem,
  PipelineReport,
  StructureGraph,
  TaxDocument,
  Variance,
  Workpaper,
} from "./types";

const TOKEN_KEY = "accountingai.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail: Record<string, unknown> = {},
  ) {
    super(message);
  }

  /** Blocking reasons from the filing gate, when the server refused a transmission. */
  get blockers(): string[] {
    const value = this.detail.blockers;
    return Array.isArray(value) ? (value as string[]) : [];
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });

  if (!response.ok) {
    let payload: Record<string, unknown> = {};
    try {
      payload = await response.json();
    } catch {
      /* the server returned no body — the status alone is the message */
    }
    const detail = (payload.detail ?? payload) as Record<string, unknown>;
    const message =
      (detail.message as string) ?? (payload.message as string) ?? response.statusText;
    throw new ApiError(response.status, message, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; expires_in: number }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<CurrentUser>("/auth/me"),

  engagements: (taxYear?: number) =>
    request<Engagement[]>(`/engagements${taxYear ? `?tax_year=${taxYear}` : ""}`),

  dashboard: (id: string) => request<EngagementDashboard>(`/engagements/${id}`),

  determine: (id: string) =>
    request<PipelineReport>(`/engagements/${id}/determine`, { method: "POST" }),

  memo: (id: string) => request<{ markdown: string }>(`/engagements/${id}/memo`),

  rollforward: (id: string) =>
    request<Engagement>(`/engagements/${id}/rollforward`, { method: "POST" }),

  determinations: (id: string, requirement?: string) =>
    request<Determination[]>(
      `/engagements/${id}/determinations${requirement ? `?requirement=${requirement}` : ""}`,
    ),

  overrideDetermination: (engagementId: string, determinationId: string, body: { requirement: string; reason: string }) =>
    request<Determination>(
      `/engagements/${engagementId}/determinations/${determinationId}/override`,
      { method: "POST", body: JSON.stringify(body) },
    ),

  filings: (id: string) => request<Filing[]>(`/engagements/${id}/filings`),

  gate: (engagementId: string, filingId: string) =>
    request<GateCheck>(`/engagements/${engagementId}/filings/${filingId}/gate`),

  approveFiling: (engagementId: string, filingId: string, note?: string) =>
    request<Filing>(`/engagements/${engagementId}/filings/${filingId}/approve`, {
      method: "POST",
      body: JSON.stringify({ attestation: true, note }),
    }),

  transmitFiling: (engagementId: string, filingId: string) =>
    request<{ submission_id: string; accepted: boolean; reference: string }>(
      `/engagements/${engagementId}/filings/${filingId}/transmit`,
      { method: "POST" },
    ),

  workpapers: (id: string) => request<Workpaper[]>(`/engagements/${id}/workpapers`),

  openItems: (id: string) => request<OpenItem[]>(`/engagements/${id}/open-items`),

  updateOpenItem: (engagementId: string, itemId: string, body: { status: string; resolution_note?: string }) =>
    request<OpenItem>(`/engagements/${engagementId}/open-items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  variances: (id: string) => request<Variance[]>(`/engagements/${id}/variances`),

  documents: (id: string) => request<TaxDocument[]>(`/engagements/${id}/documents`),

  uploadDocument: (id: string, file: File, sourceEntityId?: string, recipientEntityId?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (sourceEntityId) form.append("source_entity_id", sourceEntityId);
    if (recipientEntityId) form.append("recipient_entity_id", recipientEntityId);
    return request<TaxDocument>(`/engagements/${id}/documents`, { method: "POST", body: form });
  },

  fields: (engagementId: string, documentId: string, needsReviewOnly = false) =>
    request<ExtractedField[]>(
      `/engagements/${engagementId}/documents/${documentId}/fields${needsReviewOnly ? "?needs_review_only=true" : ""}`,
    ),

  reviewField: (engagementId: string, fieldId: string, body: { confirmed: boolean; corrected_value?: number; note?: string }) =>
    request<ExtractedField>(`/engagements/${engagementId}/documents/fields/${fieldId}/review`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  structure: (clientId: string) => request<StructureGraph>(`/clients/${clientId}/structure`),
};
