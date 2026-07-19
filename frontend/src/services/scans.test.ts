import { describe, expect, it } from 'vitest'

import { techStackToScanConfig } from './scans'

describe('techStackToScanConfig', () => {
  it('maps Auto Detect to AUTO mode with no groups', () => {
    expect(techStackToScanConfig('auto')).toEqual({ mode: 'auto', groups: [] })
  })

  it('maps Python to MANUAL mode scoped to the python group', () => {
    expect(techStackToScanConfig('python')).toEqual({ mode: 'manual', groups: ['python'] })
  })

  it('maps Web to MANUAL mode scoped to the web group', () => {
    expect(techStackToScanConfig('web')).toEqual({ mode: 'manual', groups: ['web'] })
  })
})
