// Copyright (c) 2026 cvemula1 — MIT License
// https://github.com/cvemula1/ChangeTrail

import { useState, useEffect, useCallback } from 'react'
import { fetchChanges } from './api'
import type { ChangeEvent, TimeRange, TimelineResponse } from './types'
import { Timeline } from './components/Timeline'
import { Filters } from './components/Filters'
import { Header } from './components/Header'

export default function App() {
  const [events, setEvents] = useState<ChangeEvent[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<TimeRange>('1h')
  const [sourceFilter, setSourceFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const loadEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = { last: timeRange, limit: '200' }
      if (sourceFilter) params.source = sourceFilter
      if (searchQuery) params.resource_name = searchQuery
      const data: TimelineResponse = await fetchChanges(params)
      setEvents(data.events)
      setTotal(data.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load events')
      // Load demo data if API unavailable
      setEvents(DEMO_EVENTS)
      setTotal(DEMO_EVENTS.length)
    } finally {
      setLoading(false)
    }
  }, [timeRange, sourceFilter, searchQuery])

  useEffect(() => {
    loadEvents()
    const interval = setInterval(loadEvents, 15000)
    return () => clearInterval(interval)
  }, [loadEvents])

  return (
    <div className="min-h-screen bg-gray-950">
      <Header total={total} loading={loading} onRefresh={loadEvents} />
      <main className="max-w-5xl mx-auto px-4 py-6">
        <Filters
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
          sourceFilter={sourceFilter}
          onSourceFilterChange={setSourceFilter}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />
        {error && (
          <div className="mb-4 px-4 py-2 bg-yellow-900/40 border border-yellow-700 rounded-lg text-yellow-300 text-sm">
            API unavailable — showing demo data. {error}
          </div>
        )}
        <Timeline events={events} loading={loading} />
      </main>
    </div>
  )
}

const DEMO_EVENTS: ChangeEvent[] = [
  {
    id: '1',
    timestamp: new Date(Date.now() - 4 * 60000).toISOString(),
    source: 'kubernetes',
    resource_type: 'deployment',
    resource_name: 'checkout-service',
    namespace: 'production',
    action: 'deployed',
    severity: 'info',
    summary: 'deployed checkout-service → v1.23',
    metadata: { new_version: 'v1.23', old_version: 'v1.22' },
    labels: {},
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 3 * 60000).toISOString(),
    source: 'kubernetes',
    resource_type: 'configmap',
    resource_name: 'checkout-config',
    namespace: 'production',
    action: 'updated',
    severity: 'info',
    summary: 'updated configmap checkout-config',
    metadata: { keys: ['DB_HOST', 'CACHE_TTL'] },
    labels: {},
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
    source: 'kubernetes',
    resource_type: 'pod',
    resource_name: 'checkout-service-7f8b9c6d4-x2k9p',
    namespace: 'production',
    action: 'restarted',
    severity: 'warning',
    summary: 'restarted pod checkout-service-7f8b9c6d4-x2k9p (×3)',
    metadata: { restart_count: 3, reason: 'OOMKilled', exit_code: 137 },
    labels: {},
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 1 * 60000).toISOString(),
    source: 'aws',
    resource_type: 'iam-role',
    resource_name: 'checkout-svc-role',
    namespace: 'aws-account-123',
    action: 'modified',
    severity: 'warning',
    summary: 'modified iam-role checkout-svc-role',
    metadata: { change: 'policy attachment added' },
    labels: {},
  },
  {
    id: '5',
    timestamp: new Date(Date.now() - 8 * 60000).toISOString(),
    source: 'github',
    resource_type: 'repository',
    resource_name: 'checkout-service',
    namespace: 'cvemula1',
    action: 'updated',
    severity: 'info',
    summary: 'push to main: 3 commit(s) by alice',
    metadata: { branch: 'main', commit_count: 3, pusher: 'alice' },
    labels: {},
  },
  {
    id: '6',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    source: 'github',
    resource_type: 'pull_request',
    resource_name: 'checkout-service',
    namespace: 'cvemula1',
    action: 'updated',
    severity: 'info',
    summary: 'PR #142 merged: Add Redis caching layer',
    metadata: { pr_number: 142, title: 'Add Redis caching layer', author: 'bob' },
    labels: {},
  },
]
