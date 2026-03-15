// Copyright (c) 2026 cvemula1 — MIT License
// https://github.com/cvemula1/ChangeTrail

import { Search } from 'lucide-react'
import type { TimeRange } from '../types'

const TIME_RANGES: { value: TimeRange; label: string }[] = [
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1h' },
  { value: '6h', label: '6h' },
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
]

const SOURCES = [
  { value: '', label: 'All Sources' },
  { value: 'kubernetes', label: 'Kubernetes' },
  { value: 'github', label: 'GitHub' },
  { value: 'aws', label: 'AWS' },
]

interface FiltersProps {
  timeRange: TimeRange
  onTimeRangeChange: (v: TimeRange) => void
  sourceFilter: string
  onSourceFilterChange: (v: string) => void
  searchQuery: string
  onSearchChange: (v: string) => void
}

export function Filters({
  timeRange,
  onTimeRangeChange,
  sourceFilter,
  onSourceFilterChange,
  searchQuery,
  onSearchChange,
}: FiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-6">
      {/* Time range pills */}
      <div className="flex items-center bg-gray-900 rounded-lg p-0.5 border border-gray-800">
        {TIME_RANGES.map((tr) => (
          <button
            key={tr.value}
            onClick={() => onTimeRangeChange(tr.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              timeRange === tr.value
                ? 'bg-green-600 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {tr.label}
          </button>
        ))}
      </div>

      {/* Source filter */}
      <select
        value={sourceFilter}
        onChange={(e) => onSourceFilterChange(e.target.value)}
        className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-1.5 text-sm 
                   text-gray-300 focus:outline-none focus:ring-1 focus:ring-green-600"
      >
        {SOURCES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      {/* Search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search service or resource..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 
                     text-sm text-gray-300 placeholder-gray-600 focus:outline-none 
                     focus:ring-1 focus:ring-green-600"
        />
      </div>
    </div>
  )
}
