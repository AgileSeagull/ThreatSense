import type { Alert, ProcessedEvent, AlertsQuery, ActivityQuery } from '../types/api';

const BASE = '/api/v1';

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') url.searchParams.set(k, String(v));
    });
  }
  const r = await fetch(url.toString());
  if (!r.ok) {
    const text = await r.text();
    const isHtml = text.trimStart().startsWith('<');
    throw new Error(`API ${r.status}: ${isHtml ? r.statusText || 'Backend unavailable' : text}`);
  }
  return r.json();
}

export interface DashboardStats {
  total: number;
  total_alerts: number;
  level_12_plus_alerts: number;
  authentication_failure: number;
  authentication_success: number;
}

export interface AlertsOverTimeSeries {
  period: string;
  [key: string]: string | number;
}

export interface TechniqueSeries { name: string; value: number; machine_id?: string }
export interface TopAgentsResponse { series: TechniqueSeries[]; machine_ids: string[] }
export interface EvolutionSeries { period: string; [key: string]: string | number }

export const api = {
  alerts: {
    list: (q?: AlertsQuery) =>
      get<Alert[]>(`${BASE}/alerts`, q as Record<string, string | number | undefined>),
  },
  activity: {
    list: (q?: ActivityQuery) =>
      get<ProcessedEvent[]>(`${BASE}/activity`, q as Record<string, string | number | undefined>),
  },
  dashboard: {
    stats: (params?: { since?: string; until?: string }) =>
      get<DashboardStats>(`${BASE}/dashboard/stats`, params),
    alertsOverTime: (params?: { since?: string; until?: string; interval_minutes?: number }) =>
      get<{ interval_minutes: number; series: AlertsOverTimeSeries[] }>(`${BASE}/dashboard/alerts-over-time`, params),
    alertsByTechnique: (params?: { since?: string; until?: string }) =>
      get<{ series: TechniqueSeries[] }>(`${BASE}/dashboard/alerts-by-technique`, params),
    topAgents: (params?: { since?: string; until?: string; top_n?: number }) =>
      get<TopAgentsResponse>(`${BASE}/dashboard/top-agents`, params),
    alertsEvolutionByAgent: (params?: { since?: string; until?: string; interval_minutes?: number; top_n?: number }) =>
      get<{ interval_minutes: number; series: EvolutionSeries[] }>(`${BASE}/dashboard/alerts-evolution-by-agent`, params),
  },
};
