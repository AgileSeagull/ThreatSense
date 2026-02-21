import { Link } from 'react-router-dom';
import type { Alert } from '../types/api';
import { RiskBadge } from './RiskBadge';
import { ExplanationBlock } from './ExplanationBlock';

interface AlertCardProps {
  alert: Alert;
  expanded?: boolean;
  onToggle?: () => void;
}

export function AlertCard({ alert, expanded, onToggle }: AlertCardProps) {
  const time = new Date(alert.timestamp).toLocaleString();
  return (
    <article
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      data-alert-id={alert.id}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <RiskBadge score={alert.risk_score} />
          <span className="font-medium text-gray-800">{alert.user}</span>
          <span className="text-gray-500 text-sm">@{alert.machine_id}</span>
          <span className="text-gray-500 text-sm">{time}</span>
        </div>
        <span className="text-gray-500 text-sm uppercase">{alert.event_type}</span>
        <Link to={`/alerts/${alert.id}`} className="text-blue-600 hover:underline text-sm ml-auto">
          Details
        </Link>
      </div>
      {onToggle && (
        <button
          type="button"
          onClick={onToggle}
          className="mt-2 text-sm text-blue-600 hover:underline"
        >
          {expanded ? 'Hide details' : 'Show details'}
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
