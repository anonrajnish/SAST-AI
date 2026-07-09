import { useQuery } from '@tanstack/react-query'

import { getJson } from '../services/api'

interface LiveResponse {
  status: string
}

/** Foundation app shell. Feature pages are added in later phases (TASK-180a+). */
export function StatusPage() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ['health', 'live'],
    queryFn: () => getJson<LiveResponse>('/health/live'),
    retry: false,
  })

  const backendStatus = isLoading
    ? 'checking…'
    : isError
      ? 'unreachable'
      : (data?.status ?? 'unknown')

  return (
    <section className="max-w-xl">
      <h2 className="text-base font-medium">Engineering foundation</h2>
      <p className="mt-2 text-sm text-slate-600">
        This is the application shell. Feature pages are introduced in later phases.
      </p>
      <dl className="mt-4 rounded-md border border-slate-200 bg-white p-4 text-sm">
        <div className="flex justify-between">
          <dt className="text-slate-500">Backend liveness</dt>
          <dd className="font-mono">{backendStatus}</dd>
        </div>
      </dl>
    </section>
  )
}
