// Registers @testing-library/jest-dom matchers (e.g. `toBeInTheDocument`, `toBeDisabled`) with
// Vitest's `expect`, and provides their TypeScript types. Loaded via `test.setupFiles`.
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Unmount React trees between tests so the jsdom DOM does not leak across cases.
afterEach(() => {
  cleanup()
})
