
interface ExplanationBlockProps {
  explanation: string | null;
  contributing_factors?: string[] | null;
}

export function ExplanationBlock({ explanation, contributing_factors }: ExplanationBlockProps) {
  if (!explanation && (!contributing_factors || contributing_factors.length === 0))
    return null;
  return (
    <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm">
      {explanation && <p className="text-gray-800 mb-2">{explanation}</p>}
      {contributing_factors && contributing_factors.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {contributing_factors.map((f, i) => (
            <span
              key={i}
              className="inline-block bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-xs"
            >
              {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
