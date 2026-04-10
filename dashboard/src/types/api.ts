export interface Alert {
  id: number;
  processed_event_id: number;
  event_type: string;
  machine_id: string;
  user: string;
  timestamp: string;
  risk_score: number;
  explanation: string | null;
  contributing_factors: string[] | null;
  created_at: string;
}

export interface ProcessedEvent {
  id: number;
  raw_event_id: number;
  event_type: string;
  machine_id: string;
  user: string;
  timestamp: string;
  source: string;
  payload: Record<string, unknown> | null;
  risk_score: number;
  in_threat_set: boolean;
  explanation: string | null;
  contributing_factors: string[] | null;
  processed_at: string;
}

export interface AlertsQuery {
  machine_id?: string;
  user?: string;
  since?: string;
  until?: string;
  risk_min?: number;
  limit?: number;
}

export interface ActivityQuery {
  machine_id?: string;
  user?: string;
  since?: string;
  until?: string;
  risk_min?: number;
  event_type?: string;
  limit?: number;
}
