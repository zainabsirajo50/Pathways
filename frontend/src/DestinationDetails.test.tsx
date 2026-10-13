import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { afterEach, expect, it, vi } from 'vitest'
import { App } from './App'

const row = { slug: 'published', name: 'Published Place', category: 'park', region: 'Georgia', city: null, state: 'GA', description: null, access_notes: null, official_website: null, latitude: null, longitude: null }
function mount(url: string) {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={[url]}><App /></MemoryRouter></QueryClientProvider>)
}
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); window.history.replaceState({}, '', '/') })
it('loads the single public record and handles unavailable visitor information', async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(row)))
  vi.stubGlobal('fetch', fetchMock)
  mount('/destinations/published')
  expect(screen.getByText('Loading destination…')).toBeVisible()
  expect(await screen.findByRole('heading', { name: 'Published Place' })).toBeVisible()
  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/destinations/published')
  expect(screen.getByText('A description is not yet available for this destination.')).toBeVisible()
  expect(screen.getByText(/Location coordinates are not available/)).toBeVisible()
  expect(screen.getByRole('button', { name: 'Add Published Place to trip' })).toBeEnabled()
})
it('treats unknown and unapproved API records as unavailable without fixture fallback', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 404 })))
  mount('/destinations/island-ford-preview')
  expect(await screen.findByText('This place is not available.')).toBeVisible()
  expect(screen.queryByText('Island Ford')).toBeNull()
})
it('ignores preview parameters in production', async () => {
  vi.stubEnv('DEV', false)
  const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 404 }))
  vi.stubGlobal('fetch', fetchMock)
  mount('/destinations/island-ford-preview?preview=1')
  expect(await screen.findByText('This place is not available.')).toBeVisible()
  expect(fetchMock).toHaveBeenCalled()
  expect(screen.queryByText('Development preview · fixture data')).toBeNull()
})
it('shows fixture provenance and returns to Explore with search and category intact', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  mount('/destinations/island-ford-preview?q=Island+Ford&category=river&preview=1')
  expect(await screen.findByRole('heading', { name: 'Island Ford' })).toBeVisible()
  expect(screen.getByText(/NPS-published Island Ford entrance reference/)).toBeVisible()
  expect(screen.getByRole('link', { name: 'Official visitor information ↗' })).toHaveAttribute('href', 'https://www.nps.gov/chat/planyourvisit/unitdirections.htm')
  expect(screen.getByText(/Routing remains untested/)).toBeVisible()
  expect(fetchMock).not.toHaveBeenCalled()
  await userEvent.setup().click(screen.getByRole('link', { name: '← Back to Explore' }))
  expect(await screen.findByText('1 preview place')).toBeVisible()
  expect(screen.getByRole('searchbox')).toHaveValue('Island Ford')
  expect(screen.getByRole('button', { name: 'River' })).toHaveAttribute('aria-pressed', 'true')
})
it('recovers from a transient network error', async () => {
  const fetchMock = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValue(new Response(JSON.stringify(row)))
  vi.stubGlobal('fetch', fetchMock)
  mount('/destinations/published')
  // The details query retries once; a successful retry renders public information.
  await waitFor(() => expect(screen.getByRole('heading', { name: 'Published Place' })).toBeVisible(), { timeout: 3000 })
})

it('does not use the API for an unknown preview slug', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  mount('/destinations/missing-preview?preview=1')
  expect(await screen.findByText('This place is not available.')).toBeVisible()
  expect(fetchMock).not.toHaveBeenCalled()
})

it('navigates from a card and restores the previous Explore page', async () => {
  vi.stubGlobal('fetch', vi.fn())
  mount('/explore?page=2&preview=1')
  const user = userEvent.setup()
  await user.click(await screen.findByRole('link', { name: 'Vogel State Park' }))
  expect(await screen.findByRole('heading', { name: 'Vogel State Park' })).toBeVisible()
  expect(screen.getByRole('link', { name: '← Back to Explore' })).toHaveAttribute('href', '/explore?page=2&preview=1')
  await user.click(screen.getByRole('link', { name: '← Back to Explore' }))
  expect(await screen.findByText('Page 2 of 2')).toBeVisible()
})

it('shows a retryable catalog error without substituting preview content', async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 503 }))
  vi.stubGlobal('fetch', fetchMock)
  mount('/destinations/published')
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('A small detour.'), { timeout: 3000 })
  expect(screen.queryByText('Development preview · fixture data')).toBeNull()
  fetchMock.mockResolvedValue(new Response(JSON.stringify(row)))
  await userEvent.setup().click(screen.getByRole('button', { name: 'Try again' }))
  expect(await screen.findByRole('heading', { name: 'Published Place' })).toBeVisible()
})


