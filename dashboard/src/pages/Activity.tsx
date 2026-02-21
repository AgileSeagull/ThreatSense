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
      setError(e instanceof Error ? e.message : 'Failed to load activity');
    } finally {
      setLoading(false);
    }
  }, [filters.machine_id, filters.user, filters.risk_min, filters.limit]);

  useEffect(() => {
    fetchActivity();
    const t = setInterval(fetchActivity, POLL_MS);
    return () => clearInterval(t);
  }, [fetchActivity]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Activity timeline</h1>
      <FiltersBar
        filters={filters}
        onFiltersChange={setFilters}
        onApply={fetchActivity}
      />
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">
          {error}
        </div>
      )}
      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : events.length === 0 ? (
        <p className="text-gray-500">No activity matches the filters.</p>
      ) : (
        <TimelineStrip events={events} />
      )}
    </div>
  );
}
