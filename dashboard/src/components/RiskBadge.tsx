interface RiskBadgeProps {
  score: number;
  size?: 'sm' | 'md';
}

export function RiskBadge({ score, size = 'md' }: RiskBadgeProps) {
  const tier =
    score >= 80 ? 'critical' : score >= 50 ? 'high' : score >= 20 ? 'moderate' : 'low';
  const colors = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    moderate: 'bg-amber-400 text-amber-900',
    low: 'bg-teal-100 text-teal-800',
  };
  const labels = {
    critical: 'Critical',
    high: 'High',
    moderate: 'Moderate',
    low: 'Low',
  };
  if (size === 'sm') {
    return (
      <span
        className={`inline-flex items-center gap-1 font-semibold rounded px-1.5 py-0.5 text-xs ${colors[tier]}`}
        title={`Threat Index: ${score}`}
      >
        <span className="font-mono">{Math.round(score)}</span>
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold rounded px-2.5 py-1 text-sm ${colors[tier]}`}
      title={`Threat Index: ${score}`}
    >
      <span className="font-mono">{Math.round(score)}</span>
      <span className="text-xs opacity-80">{labels[tier]}</span>
    </span>
  );
}
