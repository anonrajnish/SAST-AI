import { afterEach, describe, expect, it, vi } from 'vitest'

import { getJson } from './api'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('getJson', () => {
  it('returns parsed JSON on a 2xx response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 })),
    )

    await expect(getJson<{ ok: boolean }>('/version')).resolves.toEqual({ ok: true })
  })

  it('throws on a non-2xx response', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('nope', { status: 500 })))

    await expect(getJson('/version')).rejects.toThrow(/status 500/)
  })
})
