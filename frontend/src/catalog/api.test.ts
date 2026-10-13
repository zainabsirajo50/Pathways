import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchCategories, fetchDestinations } from './api'

afterEach(() => vi.unstubAllGlobals())
describe('public API client', () => {
  it('encodes name filters and pagination and omits credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 0, page: 2, page_size: 6 })))
    vi.stubGlobal('fetch', fetchMock)
    const controller = new AbortController()
    await fetchDestinations({ q: '  Falls & woods  ', category: 'waterfall', page: 2 }, controller.signal)
    const url = new URL(fetchMock.mock.calls[0][0], 'http://localhost')
    expect(url.pathname).toBe('/api/v1/destinations')
    expect(Object.fromEntries(url.searchParams)).toEqual({ page: '2', page_size: '6', q: 'Falls & woods', category: 'waterfall' })
    expect(fetchMock.mock.calls[0][1]).toEqual({ signal: controller.signal, credentials: 'omit' })
  })
  it('reports invalid filters without exposing server details', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('sensitive internals', { status: 422 })))
    await expect(fetchDestinations({ q: '', category: '', page: 1 })).rejects.toThrow('These filters could not be accepted')
  })
  it('rejects malformed coordinates and taxonomy', async () => {
    const row = { slug: 'test', name: 'Test', region: 'Georgia', city: null, state: 'GA', category: 'river', description: null, official_website: null, access_notes: null, latitude: 999, longitude: null }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [row], total: 1, page: 1, page_size: 6 }))))
    await expect(fetchDestinations({ q: '', category: '', page: 1 })).rejects.toThrow('unexpected response')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ categories: ['invented'] }))))
    await expect(fetchCategories()).rejects.toThrow('category list')
  })
})
