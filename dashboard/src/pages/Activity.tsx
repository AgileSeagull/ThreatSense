import { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';
import type { ProcessedEvent } from '../types/api';
import { TimelineStrip } from '../components/TimelineStrip';
import type { FilterState } from '../components/FiltersBar';
import { FiltersBar } from '../components/FiltersBar';

const POLL_MS = 5000;

export function Activity() {
  const [events, setEvents] = useState<ProcessedEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    machine_id: '',
    user: '',
    risk_min: '',
    limit: '100',
  });

  const fetchActivity = useCallback(async () => {
    try {
      setError(null);
      const q: Record<string, string | number> = { limit: parseInt(filters.limit) || 100 };
      if (filters.machine_id) q.machine_id = filters.machine_id;
      if (filters.user) q.user = filters.user;
      if (filters.risk_min) q.risk_min = parseInt(filters.risk_min);
      const data = await api.activity.list(q);
      setEvents(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load incident log');
    } finally {
      setLoading(false);
    }
  }, [filters.machine_id, filters.user, filters.risk_min, filters.limit]);

  useEffect(() => {
    fetchActivity();
    const t = setInterval(fetchActivity, POLL_MS);
    return () => clearInterval(t);
  }, [fetchActivity]);

  const flaggedCount = events.filter((e) => e.risk_score >= 50).length;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Incident Log</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Chronological record of all monitored events — click any row to view clinical findings
        </p>
      </div>

      <FiltersBar
        filters={filters}
        onFiltersChange={setFilters}
        onApply={fetchActivity}
      />

      {!loading && events.length > 0 && (
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{events.length} events</span>
          {flaggedCount > 0 && (
            <span className="text-orange-600 font-medium">{flaggedCount} high-risk</span>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p>No events match the current filters.</p>
        </div>
      ) : (
        <TimelineStrip events={events} />
      )}
    </div>
  );
}
