import { useState } from 'react'
import type { ChangeEvent } from 'react'

import { TechStackSelector } from '../components/upload/TechStackSelector'
import type { TechStack } from '../services/scans'

/** Format a byte count for display (e.g. `1.2 MB`). */
function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  return `${value.toFixed(1)} ${units[unit]}`
}

/**
 * Landing page for the primary workflow: choose a repository ZIP and a tech stack, then scan.
 *
 * Slice 1 (foundation) wires up file selection and configuration only. Submitting the upload and
 * running a scan are deferred to the next slice, so the Scan button is intentionally a stub that
 * performs no network request.
 */
export function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [techStack, setTechStack] = useState<TechStack>('auto')
  const [showStubNotice, setShowStubNotice] = useState(false)

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setShowStubNotice(false)
    const selected = event.target.files?.[0] ?? null
    if (selected && !selected.name.toLowerCase().endsWith('.zip')) {
      setFile(null)
      setFileError('Please choose a .zip archive of the repository.')
      return
    }
    setFile(selected)
    setFileError(null)
  }

  function handleScan() {
    // Foundation slice: scan submission is not wired to the backend yet.
    setShowStubNotice(true)
  }

  return (
    <section className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Scan a repository</h2>
        <p className="mt-1 text-sm text-slate-600">
          Upload a repository as a <code>.zip</code> archive and choose which languages to analyze.
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="repo-archive" className="block text-sm font-medium text-slate-700">
          Repository archive
        </label>
        <input
          id="repo-archive"
          type="file"
          accept=".zip,application/zip"
          onChange={handleFileChange}
          className="block w-full text-sm text-slate-700 file:mr-4 file:rounded-md file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-700"
        />
        {file && (
          <p className="text-xs text-slate-500">
            Selected: <span className="font-medium text-slate-700">{file.name}</span> (
            {formatBytes(file.size)})
          </p>
        )}
        {fileError && (
          <p role="alert" className="text-xs text-red-600">
            {fileError}
          </p>
        )}
      </div>

      <TechStackSelector value={techStack} onChange={setTechStack} />

      <div className="space-y-2">
        <button
          type="button"
          onClick={handleScan}
          disabled={!file}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Scan
        </button>
        {showStubNotice && (
          <p role="status" className="text-xs text-slate-500">
            Scan submission is wired up in the next slice.
          </p>
        )}
      </div>
    </section>
  )
}
