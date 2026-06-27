import type {
  PredefinedTopic,
  ResearchRun,
  RunOutput,
  SourceDocument,
  Subscription,
  User,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL?.trim() || "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, String(detail));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  register: (email: string, password: string, display_name: string) =>
    request<{ access_token: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),

  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<User>("/api/auth/me", {}, token),

  listPredefinedTopics: (token: string) =>
    request<PredefinedTopic[]>("/api/topics/predefined", {}, token),

  listSubscriptions: (token: string, activeOnly = false) =>
    request<Subscription[]>(`/api/subscriptions?active_only=${activeOnly}`, {}, token),

  createSubscription: (
    token: string,
    payload: { name: string; description: string; search_queries: string[] },
  ) =>
    request<Subscription>("/api/subscriptions", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token),

  subscribePredefined: (token: string, topicId: string) =>
    request<Subscription>(`/api/subscriptions/predefined/${topicId}`, {
      method: "POST",
    }, token),

  pauseSubscription: (token: string, id: number) =>
    request<Subscription>(`/api/subscriptions/${id}/pause`, { method: "POST" }, token),

  resumeSubscription: (token: string, id: number) =>
    request<Subscription>(`/api/subscriptions/${id}/resume`, { method: "POST" }, token),

  deleteSubscription: (token: string, id: number) =>
    request<void>(`/api/subscriptions/${id}`, { method: "DELETE" }, token),

  listRuns: (token: string, subscriptionId?: number, limit = 20) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (subscriptionId) {
      params.set("subscription_id", String(subscriptionId));
    }
    return request<ResearchRun[]>(`/api/runs?${params}`, {}, token);
  },

  getRun: (token: string, runId: number) =>
    request<ResearchRun>(`/api/runs/${runId}`, {}, token),

  getRunDocuments: (token: string, runId: number) =>
    request<SourceDocument[]>(`/api/runs/${runId}/documents`, {}, token),

  getRunOutput: (token: string, runId: number) =>
    request<RunOutput>(`/api/runs/${runId}/output`, {}, token),

  triggerAllRuns: (token: string) =>
    request<{ started: number }>("/api/runs", { method: "POST" }, token),

  triggerSubscriptionRun: (token: string, subscriptionId: number) =>
    request<ResearchRun>(`/api/runs/subscription/${subscriptionId}`, { method: "POST" }, token),
};
