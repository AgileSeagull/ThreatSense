import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Alert } from '../types/api';
import { RiskBadge } from '../components/RiskBadge';

const POLL_MS = 5000;

const EVENT_TYPE_LABELS: Record<string, string> = {
  auth: 'Access Control',
  command: 'System Command',
  process: 'System Process',
  sensor: 'Sensor Reading',
};

function SeverityPill({ score }: { score: number }) {
  if (score >= 80) return <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200 font-semibold">Critical</span>;
  if (score >= 50) return <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 border border-orange-200 font-semibold">High</span>;
  if (score >= 20) return <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200 font-semibold">Moderate</span>;
  return <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 font-semibold">Low</span>;
}

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
      setError(e instanceof Error ? e.message : 'Failed to load incidents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const t = setInterval(fetchAlerts, POLL_MS);
    return () => clearInterval(t);
  }, [fetchAlerts]);

  const critical = alerts.filter((a) => a.risk_score >= 80).length;
  const high = alerts.filter((a) => a.risk_score >= 50 && a.risk_score < 80).length;

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );
  if (error) return <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">{error}</div>;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Clinical Alerts</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          All security incidents flagged for clinical review — hardware and software sources
        </p>
      </div>

      {/* Summary strip */}
      {alerts.length > 0 && (
        <div className="flex flex-wrap gap-4 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-600" />
            <span className="text-sm font-semibold text-red-700">{critical}</span>
            <span className="text-xs text-gray-500">Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            <span className="text-sm font-semibold text-orange-600">{high}</span>
            <span className="text-xs text-gray-500">High</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-gray-300" />
            <span className="text-sm font-semibold text-gray-600">{alerts.length - critical - high}</span>
            <span className="text-xs text-gray-500">Moderate / Low</span>
          </div>
          <div className="ml-auto text-xs text-gray-400">{alerts.length} total incidents</div>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Timestamp</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Device</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Operator</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Category</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Severity</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Threat Index</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Clinical Finding</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500 text-xs uppercase tracking-wide">Report</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-400">No incidents on record.</td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className={`border-b border-gray-100 hover:bg-slate-50 ${
                      alert.risk_score >= 80 ? 'bg-red-50 hover:bg-red-100' : ''
                    }`}
                  >
                    <td className="py-2 px-4 text-gray-500 text-xs whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleDateString()}{' '}
                      {new Date(alert.timestamp).toLocaleTimeString(undefined, { hour12: false, hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-2 px-4 text-gray-600 font-mono text-xs">{alert.machine_id}</td>
                    <td className="py-2 px-4 text-gray-700">{alert.user}</td>
                    <td className="py-2 px-4">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                        {EVENT_TYPE_LABELS[alert.event_type] ?? alert.event_type}
                      </span>
                    </td>
                    <td className="py-2 px-4"><SeverityPill score={alert.risk_score} /></td>
                    <td className="py-2 px-4">
                      <RiskBadge score={alert.risk_score} size="sm" />
                    </td>
                    <td className="py-2 px-4 text-gray-600 max-w-md truncate text-xs" title={alert.explanation ?? undefined}>
                      {alert.explanation ?? '—'}
                    </td>
                    <td className="py-2 px-4">
                      <Link to={`/alerts/${alert.id}`} className="text-teal-600 hover:underline text-xs font-medium">
                        View →
                      </Link>
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
