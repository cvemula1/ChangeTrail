// Copyright (c) 2026 cvemula1 — MIT License
// https://github.com/cvemula1/ChangeTrail

import { useState } from 'react'
import {
  Rocket,
  RefreshCw,
  Settings,
  Trash2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  GitBranch,
  Cloud,
  Box,
  Shield,
} from 'lucide-react'
import type { ChangeEvent } from '../types'

interface TimelineProps {
  events: ChangeEvent[]
  loading: boolean
}

export function Timeline({ events, loading }: TimelineProps) {
  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" />
        Loading changes...
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-20 text-gray-500">
        <Box className="w-10 h-10 mx-auto mb-3 opacity-50" />
        <p>No changes found for this time range.</p>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Vertical timeline line */}
      <div className="absolute left-[23px] top-0 bottom-0 w-px bg-gray-800" />

      <div className="space-y-1">
        {events.map((event) => (
          <TimelineItem key={event.id} event={event} />
        ))}
      </div>
    </div>
  )
}

function TimelineItem({ event }: { event: ChangeEvent }) {
  const [expanded, setExpanded] = useState(false)
  const time = new Date(event.timestamp)
  const timeStr = time.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

  const severityColor = {
    info: 'bg-blue-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
  }[event.severity] || 'bg-gray-500'

  const Icon = getActionIcon(event.action)
  const sourceIcon = getSourceIcon(event.source)

  return (
    <div
      className={`relative pl-12 pr-4 py-3 rounded-lg cursor-pointer transition-colors
                   hover:bg-gray-900/60 ${expanded ? 'bg-gray-900/40' : ''}`}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Timeline dot */}
      <div
        className={`absolute left-[18px] top-[18px] w-[11px] h-[11px] rounded-full 
                     border-2 border-gray-950 ${severityColor}`}
      />

      {/* Main row */}
      <div className="flex items-start gap-3">
        <span className="text-xs text-gray-500 font-mono w-12 shrink-0 pt-0.5">
          {timeStr}
        </span>

        <div className="flex items-center gap-1.5 shrink-0">
          <Icon className="w-4 h-4 text-gray-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${actionBadgeColor(event.action)}`}>
              {event.action}
            </span>
            <span className="text-sm text-gray-200 font-medium truncate">
              {event.resource_type}/{event.resource_name}
            </span>
          </div>
          {event.summary && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{event.summary}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="flex items-center gap-1 text-xs text-gray-600">
            {sourceIcon}
            {event.source}
          </span>
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
          )}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 ml-[60px] p-3 bg-gray-800/50 rounded-lg text-xs">
          <div className="grid grid-cols-2 gap-2 text-gray-400">
            <div>
              <span className="text-gray-600">Source:</span> {event.source}
            </div>
            <div>
              <span className="text-gray-600">Severity:</span>{' '}
              <span className={severityTextColor(event.severity)}>{event.severity}</span>
            </div>
            {event.namespace && (
              <div>
                <span className="text-gray-600">Namespace:</span> {event.namespace}
              </div>
            )}
            <div>
              <span className="text-gray-600">Time:</span>{' '}
              {new Date(event.timestamp).toISOString()}
            </div>
          </div>
          {Object.keys(event.metadata).length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-700">
              <span className="text-gray-600">Metadata:</span>
              <pre className="mt-1 text-gray-400 overflow-x-auto">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function getActionIcon(action: string) {
  switch (action) {
    case 'deployed':
      return Rocket
    case 'restarted':
      return RefreshCw
    case 'updated':
    case 'modified':
      return Settings
    case 'deleted':
      return Trash2
    case 'failed':
      return AlertTriangle
    default:
      return Box
  }
}

function getSourceIcon(source: string) {
  switch (source) {
    case 'kubernetes':
      return <Box className="w-3 h-3" />
    case 'github':
      return <GitBranch className="w-3 h-3" />
    case 'aws':
    case 'azure':
      return <Cloud className="w-3 h-3" />
    default:
      return <Shield className="w-3 h-3" />
  }
}

function actionBadgeColor(action: string): string {
  switch (action) {
    case 'deployed':
      return 'bg-green-900/60 text-green-400'
    case 'created':
      return 'bg-blue-900/60 text-blue-400'
    case 'updated':
    case 'modified':
      return 'bg-yellow-900/60 text-yellow-400'
    case 'deleted':
      return 'bg-red-900/60 text-red-400'
    case 'restarted':
      return 'bg-orange-900/60 text-orange-400'
    case 'failed':
      return 'bg-red-900/80 text-red-300'
    case 'scaled':
      return 'bg-purple-900/60 text-purple-400'
    default:
      return 'bg-gray-800 text-gray-400'
  }
}

function severityTextColor(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'text-red-400'
    case 'warning':
      return 'text-yellow-400'
    default:
      return 'text-blue-400'
  }
}
