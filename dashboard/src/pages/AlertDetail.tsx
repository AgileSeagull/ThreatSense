import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { RiskBadge } from '../components/RiskBadge';
import { ExplanationBlock } from '../components/ExplanationBlock';
import type { Alert } from '../types/api';

const EVENT_TYPE_LABELS: Record<string, string> = {
  auth: 'Access Control',
  command: 'System Command',
  process: 'System Process',
  sensor: 'Sensor Reading',
};

export function AlertDetail() {
  const { id } = useParams<{ id: string }>();
  const [alert, setAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        setError(null);
        const list = await fetch(`/api/v1/alerts?limit=500`).then((r) => r.json());
        const found = list.find((a: Alert) => a.id === parseInt(id, 10));
        setAlert(found ?? null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load incident report');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );
  if (error) return <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">{error}</div>;
  if (!alert) return (
    <div className="text-center py-20 text-gray-500">
      <p className="text-lg font-medium">Incident report not found</p>
      <Link to="/alerts" className="text-teal-600 hover:underline text-sm mt-2 block">← Back to Clinical Alerts</Link>
    </div>
  );

  const incidentTime = new Date(alert.timestamp).toLocaleString();
  const reportGenerated = new Date(alert.created_at).toLocaleString();
  const categoryLabel = EVENT_TYPE_LABELS[alert.event_type] ?? alert.event_type;

  const severity =
    alert.risk_score >= 80 ? { label: 'Critical', cls: 'bg-red-100 text-red-800 border-red-300' }
    : alert.risk_score >= 50 ? { label: 'High', cls: 'bg-orange-100 text-orange-800 border-orange-300' }
    : alert.risk_score >= 20 ? { label: 'Moderate', cls: 'bg-amber-100 text-amber-800 border-amber-300' }
    : { label: 'Low', cls: 'bg-teal-50 text-teal-800 border-teal-300' };

  return (
    <div className="max-w-2xl space-y-5">
      {/* Breadcrumb */}
      <div className="text-sm text-gray-400">
        <Link to="/alerts" className="hover:text-teal-600">Clinical Alerts</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-600">Incident Report #{alert.id}</span>
      </div>

      <h1 className="text-2xl font-bold text-gray-900">Incident Report #{alert.id}</h1>

      {/* Status banner for critical */}
      {alert.risk_score >= 80 && (
        <div className="rounded-lg bg-red-50 border border-red-300 px-4 py-3 flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-pulse shrink-0" />
          <p className="text-red-800 text-sm font-medium">
            Critical Threat — Immediate clinical review required
          </p>
        </div>
      )}

      {/* Main card */}
      <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-4 shadow-sm">
        {/* Header row */}
        <div className="flex flex-wrap items-center gap-3">
          <RiskBadge score={alert.risk_score} />
          <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${severity.cls}`}>
            {severity.label} Severity
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
            {categoryLabel}
          </span>
        </div>

        {/* Metadata */}
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-gray-400 font-medium">Operator</dt>
          <dd className="text-gray-800 font-semibold">{alert.user}</dd>

          <dt className="text-gray-400 font-medium">Device ID</dt>
          <dd className="text-gray-700 font-mono text-xs">{alert.machine_id}</dd>

          <dt className="text-gray-400 font-medium">Incident Time</dt>
          <dd className="text-gray-700">{incidentTime}</dd>

          <dt className="text-gray-400 font-medium">Report Generated</dt>
          <dd className="text-gray-700">{reportGenerated}</dd>

          <dt className="text-gray-400 font-medium">Reference ID</dt>
          <dd className="text-gray-500 font-mono text-xs">PE-{alert.processed_event_id}</dd>

          <dt className="text-gray-400 font-medium">Threat Index</dt>
          <dd>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${alert.risk_score >= 80 ? 'bg-red-500' : alert.risk_score >= 50 ? 'bg-orange-500' : alert.risk_score >= 20 ? 'bg-amber-400' : 'bg-teal-400'}`}
                  style={{ width: `${Math.min(100, alert.risk_score)}%` }}
                />
              </div>
              <span className="text-sm font-mono font-semibold text-gray-700">{Math.round(alert.risk_score)} / 100</span>
            </div>
          </dd>
        </dl>

        <ExplanationBlock
          explanation={alert.explanation}
          contributing_factors={alert.contributing_factors}
        />
      </div>

      <div className="flex gap-3">
        <Link
          to="/alerts"
          className="text-sm text-teal-600 hover:underline"
        >
          ← Back to Clinical Alerts
        </Link>
      </div>
    </div>
  );
}
