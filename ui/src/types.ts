// Copyright (c) 2026 cvemula1 — MIT License
// https://github.com/cvemula1/ChangeTrail

export interface ChangeEvent {
  id: string
  timestamp: string
  source: string
  resource_type: string
  resource_name: string
  namespace: string | null
  action: string
  severity: string
  summary: string
  metadata: Record<string, unknown>
  labels: Record<string, string>
}

export interface TimelineResponse {
  events: ChangeEvent[]
  total: number
  query: Record<string, unknown>
}

export type TimeRange = '15m' | '30m' | '1h' | '6h' | '24h' | '7d'
