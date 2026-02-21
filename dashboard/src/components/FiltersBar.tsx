
export interface FilterState {
  machine_id: string;
  user: string;
  risk_min: string;
  limit: string;
}

interface FiltersBarProps {
  filters: FilterState;
  onFiltersChange: (f: FilterState) => void;
  onApply: () => void;
}

export function FiltersBar({ filters, onFiltersChange, onApply }: FiltersBarProps) {
  return (
    <div className="flex flex-wrap items-end gap-3 p-3 rounded-lg bg-white border border-gray-200 shadow-sm">
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-gray-500">Machine ID</span>
        <input
          type="text"
          value={filters.machine_id}
          onChange={(e) => onFiltersChange({ ...filters, machine_id: e.target.value })}
          placeholder="e.g. abc123"
          className="bg-white border border-gray-300 rounded px-2 py-1.5 text-gray-800 min-w-[120px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-gray-500">User</span>
        <input
          type="text"
          value={filters.user}
          onChange={(e) => onFiltersChange({ ...filters, user: e.target.value })}
          placeholder="username"
          className="bg-white border border-gray-300 rounded px-2 py-1.5 text-gray-800 min-w-[120px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-gray-500">Min risk</span>
        <input
          type="number"
          min={0}
          max={100}
          value={filters.risk_min}
          onChange={(e) => onFiltersChange({ ...filters, risk_min: e.target.value })}
          placeholder="0"
          className="bg-white border border-gray-300 rounded px-2 py-1.5 text-gray-800 w-20 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-gray-500">Limit</span>
        <input
          type="number"
          min={1}
          max={500}
          value={filters.limit}
          onChange={(e) => onFiltersChange({ ...filters, limit: e.target.value })}
          className="bg-white border border-gray-300 rounded px-2 py-1.5 text-gray-800 w-20 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </label>
      <button
        type="button"
        onClick={onApply}
        className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium"
      >
        Apply
      </button>
    </div>
  );
}
