import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { RiskBadge } from '../components/RiskBadge';
import { ExplanationBlock } from '../components/ExplanationBlock';
import type { Alert } from '../types/api';

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
        setError(e instanceof Error ? e.message : 'Failed to load alert');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <p className="text-gray-500">Loading…</p>;
  if (error) return <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4">{error}</div>;
  if (!alert) return <p className="text-gray-500">Alert not found.</p>;

  const time = new Date(alert.timestamp).toLocaleString();
  const created = new Date(alert.created_at).toLocaleString();

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Alert #{alert.id}</h1>
      <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <RiskBadge score={alert.risk_score} />
          <span className="text-gray-800 font-medium">{alert.user}</span>
          <span className="text-gray-500 text-sm">{alert.machine_id}</span>
          <span className="text-gray-500 text-sm uppercase">{alert.event_type}</span>
        </div>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-gray-500">Event time</dt>
          <dd className="text-gray-800">{time}</dd>
          <dt className="text-gray-500">Alert created</dt>
          <dd className="text-gray-800">{created}</dd>
          <dt className="text-gray-500">Processed event ID</dt>
          <dd className="text-gray-800">{alert.processed_event_id}</dd>
        </dl>
        <ExplanationBlock
          explanation={alert.explanation}
          contributing_factors={alert.contributing_factors}
        />
      </div>
    </div>
  );
}
