import { Link } from 'react-router-dom';
import type { Alert } from '../types/api';
import { RiskBadge } from './RiskBadge';
import { ExplanationBlock } from './ExplanationBlock';

const EVENT_TYPE_LABELS: Record<string, string> = {
  auth: 'Access Control',
  command: 'System Command',
  process: 'System Process',
  sensor: 'Sensor Reading',
};

interface AlertCardProps {
  alert: Alert;
  expanded?: boolean;
  onToggle?: () => void;
}

export function AlertCard({ alert, expanded, onToggle }: AlertCardProps) {
  const time = new Date(alert.timestamp).toLocaleString();
  const categoryLabel = EVENT_TYPE_LABELS[alert.event_type] ?? alert.event_type;
  return (
    <article
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      data-alert-id={alert.id}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <RiskBadge score={alert.risk_score} />
          <span className="font-medium text-gray-800">{alert.user}</span>
          <span className="text-gray-400 text-sm font-mono text-xs">@{alert.machine_id}</span>
          <span className="text-gray-400 text-xs">{time}</span>
        </div>
        <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
          {categoryLabel}
        </span>
        <Link to={`/alerts/${alert.id}`} className="text-teal-600 hover:underline text-sm ml-auto">
          View Report
        </Link>
      </div>
      {onToggle && (
        <button
          type="button"
          onClick={onToggle}
          className="mt-2 text-sm text-teal-600 hover:underline"
        >
          {expanded ? 'Hide findings' : 'Show findings'}
        </button>
      )}
      {(expanded ?? true) && (
        <div className="mt-3">
          <ExplanationBlock
            explanation={alert.explanation}
            contributing_factors={alert.contributing_factors}
          />
        </div>
      )}
    </article>
  );
}
