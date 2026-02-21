import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Alert } from '../types/api';

const POLL_MS = 5000;

export function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setError(null);
      const list = await api.alerts.list({ limit: 500 });
      setAlerts(Array.isArray(list) ? list : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const t = setInterval(fetchAlerts, POLL_MS);
    return () => clearInterval(t);
  }, [fetchAlerts]);

  if (loading) return <p className="text-gray-500">Loading alerts…</p>;
  if (error) return <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">{error}</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-900">Alerts</h1>
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-3 px-4 font-medium text-gray-700">Time</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Machine</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">User</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Type</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Risk</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Description</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Detail</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">No alerts.</td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 px-4 text-gray-600">
                      {new Date(alert.timestamp).toLocaleDateString()} {new Date(alert.timestamp).toLocaleTimeString(undefined, { hour12: false, hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-2 px-4 text-gray-700">{alert.machine_id}</td>
                    <td className="py-2 px-4 text-gray-700">{alert.user}</td>
                    <td className="py-2 px-4 text-gray-700">{alert.event_type}</td>
                    <td className="py-2 px-4 font-mono font-medium">{Math.round(alert.risk_score)}</td>
                    <td className="py-2 px-4 text-gray-600 max-w-md truncate" title={alert.explanation ?? undefined}>
                      {alert.explanation ?? '—'}
                    </td>
                    <td className="py-2 px-4">
                      <Link to={`/alerts/${alert.id}`} className="text-blue-600 hover:underline">#{alert.id}</Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
