// Copyright (c) 2026 cvemula1 — MIT License
// https://github.com/cvemula1/ChangeTrail

import type { TimelineResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

export async function fetchChanges(params: Record<string, string>): Promise<TimelineResponse> {
  const query = new URLSearchParams(params).toString()
  const res = await fetch(`${API_BASE}/changes?${query}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch('/health')
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`)
  return res.json()
}
