export interface CurlerCheck {
  uuid: string;
  created_at: string;
  alert_receive_channel: number;
  url: string;
  frequency: number;
  last_pings: CurlerCheckPing[];
  paused: boolean;
}

export interface CurlerCheckPing {
  id: number;
  url: string;
  created_at: string;
  http_status: number;
  latency_ms: number;
  successful: boolean;
  exception_reason: string | null;
}

export interface CurlerCheckStats {
  max_latency: number | null;
  min_latency: number | null;
  uptime: number;
  last_downtime: string;
}
