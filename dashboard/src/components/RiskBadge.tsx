
interface RiskBadgeProps {
  score: number;
  size?: 'sm' | 'md';
}

export function RiskBadge({ score, size = 'md' }: RiskBadgeProps) {
  const tier =
    score >= 80 ? 'critical' : score >= 50 ? 'high' : score >= 20 ? 'medium' : 'low';
  const colors = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-600 text-white',
    medium: 'bg-amber-500 text-gray-900',
    low: 'bg-gray-500 text-white',
  };
  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1';
  return (
    <span
      className={`inline-block font-mono font-semibold rounded ${colors[tier]} ${sizeClass}`}
      title={`Risk score: ${score}`}
    >
      {Math.round(score)}
    </span>
  );
}
