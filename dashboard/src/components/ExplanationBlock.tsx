interface ExplanationBlockProps {
  explanation: string | null;
  contributing_factors?: string[] | null;
}

export function ExplanationBlock({ explanation, contributing_factors }: ExplanationBlockProps) {
  if (!explanation && (!contributing_factors || contributing_factors.length === 0))
    return null;
  return (
    <div className="rounded-lg border border-teal-100 bg-teal-50 p-3 text-sm space-y-2">
      {explanation && (
        <div>
          <p className="text-xs font-semibold text-teal-700 uppercase tracking-wide mb-1">Clinical Finding</p>
          <p className="text-gray-800">{explanation}</p>
        </div>
      )}
      {contributing_factors && contributing_factors.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-teal-700 uppercase tracking-wide mb-1">Clinical Indicators</p>
          <div className="flex flex-wrap gap-1">
            {contributing_factors.map((f, i) => (
              <span
                key={i}
                className="inline-block bg-white border border-teal-200 text-teal-800 px-2 py-0.5 rounded text-xs"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
