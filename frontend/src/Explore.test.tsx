import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { categories, type Destination } from './catalog/types'

const rows: Destination[] = Array.from({ length: 8 }, (_, i) => ({
  slug: `public-${i}`, name: i === 0 ? 'Public Falls' : `Public River ${i}`,
  category: i === 0 ? 'waterfall' : 'river', region: 'Georgia', city: null, state: 'GA',
  description: 'Public destination description', official_website: null, access_notes: null,
  latitude: i === 0 ? 34 : null, longitude: i === 0 ? -84 : null,
}))
function mockAPI() {
  const mock = vi.fn(async (path: string) => {
    const url = new URL(path, 'http://localhost')
    if (url.pathname.endsWith('/categories')) return new Response(JSON.stringify({ categories }))
    const q = url.searchParams.get('q') || ''
    const category = url.searchParams.get('category')
    const page = Number(url.searchParams.get('page'))
    const matches = rows.filter(row => row.name.toLowerCase().includes(q.toLowerCase()) && (!category || row.category === category))
    return new Response(JSON.stringify({ items: matches.slice((page - 1) * 6, page * 6), total: matches.length, page, page_size: 6 }))
  })
  vi.stubGlobal('fetch', mock)
  return mock
}
function mount(path = '/explore') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>)
}
afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState({}, '', '/'); vi.unstubAllEnvs() })

describe('Explore', () => {
  it('loads public cards, filters by name/category and resets page', async () => {
    mockAPI(); mount(); const user = userEvent.setup()
    expect(await screen.findByRole('heading', { name: 'Public Falls' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Next →' }))
    expect(await screen.findByRole('heading', { name: 'Public River 7' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Waterfall' }))
    expect(await screen.findByRole('heading', { name: 'Public Falls' })).toBeVisible()
    expect(screen.getByText('1 place')).toBeVisible()
    await user.type(screen.getByRole('searchbox'), 'missing')
    await user.click(screen.getByRole('button', { name: 'Search' }))
    expect(await screen.findByText('No places on this path.')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(await screen.findByText('8 places')).toBeVisible()
  })
  it('selects and clears details, identifying coordinates as display points', async () => {
    mockAPI(); mount(); const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Explore Public Falls' }))
    expect(screen.getByRole('button', { name: 'Explore Public Falls' })).toHaveAttribute('aria-pressed', 'true')
    const details = screen.getByRole('region', { name: 'Destination details' })
    expect(within(details).getByRole('link', { name: 'View Details' })).toHaveAttribute('href', '/destinations/public-0')
    await user.click(screen.getByRole('button', { name: 'Clear selected destination' }))
    expect(within(details).getByText('Start with a place.')).toBeVisible()
  })
  it('keeps an empty public catalog empty instead of substituting fixtures', async () => {
    vi.stubGlobal('fetch', vi.fn(async (path: string) => new Response(JSON.stringify(path.endsWith('/categories') ? { categories } : { items: [], total: 0, page: 1, page_size: 6 }))))
    mount()
    expect(await screen.findByText('Good places take a little care.')).toBeVisible()
    expect(screen.queryByText('Amicalola Falls')).not.toBeInTheDocument()
    expect(screen.queryByText('Development preview · fixture data')).not.toBeInTheDocument()
  })
  it('shows loading and error states, then retries successfully', async () => {
    let finish: (value: Response) => void = () => {}
    vi.stubGlobal('fetch', vi.fn((path: string) => path.endsWith('/categories') ? Promise.resolve(new Response(JSON.stringify({ categories }))) : new Promise<Response>(resolve => { finish = resolve })))
    mount()
    expect(screen.getByRole('status', { name: 'Loading destinations' })).toBeVisible()
    finish(new Response('', { status: 503 }))
    expect(await screen.findByText('A small detour.')).toBeVisible()
    mockAPI()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: 'Public Falls' })).toBeVisible()
  })
  it('opts into labeled fixtures without API calls, then switches to the public cache', async () => {
    window.history.replaceState({}, '', '/explore?preview=1')
    const fetchMock = mockAPI(); mount(); const user = userEvent.setup()
    expect(await screen.findByRole('heading', { name: 'Amicalola Falls' })).toBeVisible()
    expect(screen.getByText('Development preview · fixture data')).toBeVisible()
    expect(fetchMock).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Explore Amicalola Falls' }))
    expect(screen.getByRole('link', { name: 'View Details' })).toHaveAttribute('href', '/destinations/amicalola-preview?preview=1')
    await user.click(screen.getByRole('button', { name: /Use public API/ }))
    expect(await screen.findByRole('heading', { name: 'Public Falls' })).toBeVisible()
    expect(screen.queryByRole('heading', { name: 'Amicalola Falls' })).not.toBeInTheDocument()
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
  })
  it('ignores fixture query parameters and hides preview controls in production', async () => {
    vi.stubEnv('DEV', false)
    window.history.replaceState({}, '', '/explore?preview=1')
    mockAPI(); mount()
    expect(await screen.findByRole('heading', { name: 'Public Falls' })).toBeVisible()
    expect(screen.queryByRole('button', { name: /Preview fixtures/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Amicalola Falls')).not.toBeInTheDocument()
  })
  it('provides a useful not-found route', () => {
    mount('/unknown')
    expect(screen.getByText('A path less traveled.')).toBeVisible()
    expect(screen.getByRole('link', { name: 'Back to Explore' })).toHaveAttribute('href', '/explore')
  })
})


