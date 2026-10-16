import {
  THRESHOLD_COMPARISON_GROUPS,
  comparisonLabel,
  needsExtraOption,
} from '../../utils/periodComparisons';

interface ThresholdComparisonSelectProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

/**
 * The comparison a threshold row is judged on, grouped as the reader thinks of them.
 * A value the list does not hold (an old name such as "yoy", or anything unexpected) is
 * shown as itself rather than silently displayed as the first option.
 */
export function ThresholdComparisonSelect({ value, onChange, className }: ThresholdComparisonSelectProps) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className={className}
      aria-label="Comparison"
    >
      {needsExtraOption(value) && <option value={value}>{comparisonLabel(value)}</option>}
      {THRESHOLD_COMPARISON_GROUPS.map(g => (
        <optgroup key={g.group} label={g.group}>
          {g.options.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}
