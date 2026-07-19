import type { TechStack } from '../../services/scans'

interface TechStackOption {
  value: TechStack
  label: string
  hint: string
}

const OPTIONS: readonly TechStackOption[] = [
  { value: 'auto', label: 'Auto Detect', hint: 'Detect supported languages in the repository' },
  { value: 'python', label: 'Python', hint: 'Scan Python sources only' },
  { value: 'web', label: 'Web', hint: 'Scan JavaScript, TypeScript, and HTML' },
]

interface TechStackSelectorProps {
  value: TechStack
  onChange: (value: TechStack) => void
  disabled?: boolean
}

/** A single-choice Tech Stack selector (Auto Detect / Python / Web), rendered as a radio group. */
export function TechStackSelector({ value, onChange, disabled = false }: TechStackSelectorProps) {
  return (
    <fieldset className="space-y-2" disabled={disabled}>
      <legend className="text-sm font-medium text-slate-700">Tech stack</legend>
      <div className="flex flex-col gap-2 sm:flex-row">
        {OPTIONS.map((option) => (
          <label
            key={option.value}
            className="flex flex-1 cursor-pointer items-start gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 has-[:checked]:border-slate-900 has-[:checked]:ring-1 has-[:checked]:ring-slate-900"
          >
            <input
              type="radio"
              name="tech-stack"
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="mt-1"
            />
            <span>
              <span className="block text-sm font-medium text-slate-900">{option.label}</span>
              <span className="block text-xs text-slate-500">{option.hint}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
