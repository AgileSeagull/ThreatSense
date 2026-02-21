import { useState } from 'react';
import type { ProcessedEvent } from '../types/api';
import { RiskBadge } from './RiskBadge';
import { ExplanationBlock } from './ExplanationBlock';

interface TimelineStripProps {
  events: ProcessedEvent[];
}

export function TimelineStrip({ events }: TimelineStripProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  return (
    <ul className="space-y-2">
      {events.map((ev) => {
        const open = expandedId === ev.id;
        const time = new Date(ev.timestamp).toLocaleString();
        return (
          <li
            key={ev.id}
            className="rounded-lg border border-gray-200 bg-white overflow-hidden shadow-sm"
          >
            <button
              type="button"
              onClick={() => setExpandedId(open ? null : ev.id)}
              className="w-full flex flex-wrap items-center gap-3 p-3 text-left hover:bg-gray-50"
            >
              <RiskBadge score={ev.risk_score} size="sm" />
              <span className="text-gray-800 font-medium">{ev.user}</span>
              <span className="text-gray-500 text-sm">{ev.machine_id}</span>
              <span className="text-gray-500 text-sm">{time}</span>
              <span className="text-gray-500 text-sm uppercase">{ev.source}</span>
              {ev.in_threat_set && (
                <span className="text-red-600 text-xs font-semibold">THREAT</span>
              )}
            </button>
            {open && (
              <div className="px-3 pb-3 pt-0">
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
