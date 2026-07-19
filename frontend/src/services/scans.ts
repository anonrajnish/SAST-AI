// Typed contract for the scan API. These mirror the backend Pydantic models
// (`app.services.scan.ScanConfig`, `app.services.jobs.ScanJob`) so the UI speaks the same
// vocabulary. Slice 1 uses only the *request-side* config types (the Tech Stack selector); the
// network calls that submit an upload and read jobs are wired in later slices.

/** Analysis capability groups the backend supports (Web bundles JS/TS/HTML). */
export type LanguageGroup = 'python' | 'web'

/** How target languages are chosen for a scan. */
export type TargetMode = 'auto' | 'manual'

/** Lifecycle states of a scan job (mirrors `ScanJobStatus`). */
export type ScanJobStatus = 'pending' | 'running' | 'completed' | 'failed'

/**
 * The scan configuration sent with an upload. Mirrors the backend form contract:
 * AUTO carries no groups; MANUAL requires at least one.
 */
export interface ScanConfigRequest {
  mode: TargetMode
  groups: LanguageGroup[]
}

/**
 * A scan job as returned by the API. `result` is intentionally left opaque here — the results
 * view (which types the nested `ScanResult`) arrives in a later slice.
 */
export interface ScanJob {
  job_id: string
  status: ScanJobStatus
  created_at: string
  completed_at: string | null
  result: unknown | null
  error: string | null
}

/** The user-facing Tech Stack choice on the upload page: one of three mutually-exclusive options. */
export type TechStack = 'auto' | 'python' | 'web'

/** Translate a Tech Stack choice into the backend scan-config request. Pure and reusable. */
export function techStackToScanConfig(stack: TechStack): ScanConfigRequest {
  switch (stack) {
    case 'auto':
      return { mode: 'auto', groups: [] }
    case 'python':
      return { mode: 'manual', groups: ['python'] }
    case 'web':
      return { mode: 'manual', groups: ['web'] }
  }
}
