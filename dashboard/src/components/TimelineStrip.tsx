import { useState } from 'react';
import type { ProcessedEvent } from '../types/api';
import { RiskBadge } from './RiskBadge';
import { ExplanationBlock } from './ExplanationBlock';

interface TimelineStripProps {
  events: ProcessedEvent[];
}

const SOURCE_LABELS: Record<string, string> = {
  auth: 'Access Control',
  command: 'System Command',
  process: 'System Process',
  sensor: 'Sensor Reading',
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  auth: 'Access Control',
  command: 'System Command',
  process: 'System Process',
  sensor: 'Sensor Reading',
};

export function TimelineStrip({ events }: TimelineStripProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  return (
    <ul className="space-y-2">
      {events.map((ev) => {
        const open = expandedId === ev.id;
        const time = new Date(ev.timestamp).toLocaleString();
        const sourceLabel = SOURCE_LABELS[ev.source] ?? ev.source;
        const isHighRisk = ev.risk_score >= 50;
        return (
          <li
            key={ev.id}
            className={`rounded-lg border bg-white overflow-hidden shadow-sm ${
              isHighRisk ? 'border-orange-300' : 'border-gray-200'
            }`}
          >
            <button
              type="button"
              onClick={() => setExpandedId(open ? null : ev.id)}
              className="w-full flex flex-wrap items-center gap-3 p-3 text-left hover:bg-slate-50"
            >
              <RiskBadge score={ev.risk_score} size="sm" />
              <span className="text-gray-800 font-medium">{ev.user}</span>
              <span className="text-gray-500 text-sm font-mono text-xs">{ev.machine_id}</span>
              <span className="text-gray-400 text-xs">{time}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                {sourceLabel}
              </span>
              {ev.in_threat_set && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-red-100 text-red-700 border border-red-300">
                  KNOWN THREAT
                </span>
              )}
            </button>
            {open && (
              <div className="px-3 pb-3 pt-0">
                <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs text-gray-600 mb-2">
                  <dt className="text-gray-400">Category</dt>
                  <dd>{EVENT_TYPE_LABELS[ev.event_type] ?? ev.event_type}</dd>
                  <dt className="text-gray-400">Device</dt>
                  <dd className="font-mono">{ev.machine_id}</dd>
                  <dt className="text-gray-400">Operator</dt>
                  <dd>{ev.user}</dd>
                </dl>
                <ExplanationBlock
                  explanation={ev.explanation}
                  contributing_factors={ev.contributing_factors}
                />
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
