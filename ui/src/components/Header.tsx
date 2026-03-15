// Copyright (c) 2026 cvemula1 — MIT License
// https://github.com/cvemula1/ChangeTrail

import { RefreshCw, Activity } from 'lucide-react'

interface HeaderProps {
  total: number
  loading: boolean
  onRefresh: () => void
}

export function Header({ total, loading, onRefresh }: HeaderProps) {
  return (
    <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-green-400" />
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">ChangeTrail</h1>
            <p className="text-xs text-gray-500">What changed before this alert?</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">
            {total} event{total !== 1 ? 's' : ''}
          </span>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 
                       rounded-lg text-sm text-gray-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>
    </header>
  )
}
