import { act, render, screen, fireEvent, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { DestinationMap, hasCoordinates } from './DestinationMap'
import type { Destination } from '../catalog/types'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { App } from '../App'
import userEvent from '@testing-library/user-event'

const fake = vi.hoisted(() => ({ handlers: {} as Record<string, () => void>, easeTo: vi.fn(), remove: vi.fn(), markerRemove: vi.fn() }))
vi.mock('mapbox-gl', () => ({ default: {
  Map: class {
    addControl() {}
    on(name: string, callback: () => void) { fake.handlers[name] = callback }
    easeTo = fake.easeTo
    resize() {}
    remove = fake.remove
  },
  NavigationControl: class {},
  Marker: class {
    element: HTMLElement
    constructor({ element }: { element: HTMLElement }) { this.element = element; element.setAttribute('role', 'img') }
    setLngLat() { return this }
    addTo() { this.element.setAttribute('role', 'img'); document.body.append(this.element); return this }
    remove() { this.element.remove(); fake.markerRemove() }
  },
} }))
const point: Destination = { slug: 'synthetic', name: 'Synthetic Test Point', category: 'river', region: 'Test', city: null, state: 'GA', description: null, official_website: null, access_notes: null, latitude: 34, longitude: -84 }
const missing = { ...point, slug: 'missing', name: 'No Coordinates', latitude: null }
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.clearAllMocks(); fake.handlers = {}; window.history.replaceState({}, '', '/') })
function prepare() {
  vi.stubEnv('VITE_MAPBOX_ACCESS_TOKEN', 'pk.synthetic-test-only')
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} })
  vi.stubGlobal('matchMedia', () => ({ matches: true }))
}
it('requires both finite coordinates in WGS84 ranges', () => {
  expect(hasCoordinates(point)).toBe(true)
  for (const row of [missing, { ...point, longitude: 181 }, { ...point, latitude: NaN }, { ...point, longitude: Infinity }]) expect(hasCoordinates(row)).toBe(false)
})
it('renders a missing-token state without initializing the map', () => {
  vi.stubEnv('VITE_MAPBOX_ACCESS_TOKEN', '')
  render(<DestinationMap destinations={[point]} onSelect={vi.fn()} fixtures={false} loading={false}/>)
  expect(screen.getByText('Map setup needed')).toBeVisible()
})
it('filters markers, synchronizes selection, replaces result markers and cleans up', async () => {
  prepare()
  const select = vi.fn()
  const view = render(<DestinationMap destinations={[point, missing]} onSelect={select} fixtures={false} loading={false}/>)
  expect(screen.getByText('Loading Georgia’s map…')).toBeVisible()
  await waitFor(() => expect(fake.handlers.load).toBeTypeOf('function'))
  act(() => fake.handlers.load())
  expect(screen.queryByRole('button', { name: 'Select No Coordinates on map' })).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'Select Synthetic Test Point on map' }))
  expect(select).toHaveBeenCalledWith('synthetic')
  view.rerender(<DestinationMap destinations={[point, missing]} selected={point} onSelect={select} fixtures={false} loading={false}/>)
  expect(screen.getByRole('button', { name: 'Select Synthetic Test Point on map' })).toHaveAttribute('aria-pressed', 'true')
  expect(fake.easeTo).toHaveBeenCalledWith(expect.objectContaining({ center: [-84, 34] }))
  fake.easeTo.mockClear()
  view.rerender(<DestinationMap destinations={[missing]} selected={missing} onSelect={select} fixtures={true} loading={false}/>)
  expect(screen.queryByRole('button', { name: 'Select Synthetic Test Point on map' })).toBeNull()
  expect(fake.easeTo).not.toHaveBeenCalled()
  expect(screen.getByText(/No display coordinates/)).toBeVisible()
  view.unmount()
  expect(fake.remove).toHaveBeenCalled()
})
it('shows sanitized map errors and supports retry', async () => {
  prepare()
  render(<DestinationMap destinations={[]} onSelect={vi.fn()} fixtures={false} loading={false}/>)
  await waitFor(() => expect(fake.handlers.error).toBeTypeOf('function'))
  act(() => fake.handlers.error())
  expect(screen.getByRole('alert')).toHaveTextContent('The map could not load.')
  fireEvent.click(screen.getByRole('button', { name: 'Retry map' }))
  expect(screen.getByText('Loading Georgia’s map…')).toBeVisible()
})

it('numbers mapped stops by full itinerary order, including gaps for unmapped stops', async () => {
  prepare()
  const view = render(<DestinationMap destinations={[missing, point]} onSelect={vi.fn()} fixtures={false} loading={false} numbered/>)
  await waitFor(() => expect(fake.handlers.load).toBeTypeOf('function'))
  act(() => fake.handlers.load())
  expect(screen.getByRole('button', { name: 'Select Synthetic Test Point on map' })).toHaveTextContent('2')
  view.rerender(<DestinationMap destinations={[point, missing]} onSelect={vi.fn()} fixtures={false} loading={false} numbered/>)
  expect(screen.getByRole('button', { name: 'Select Synthetic Test Point on map' })).toHaveTextContent('1')
  expect(screen.queryByRole('button', { name: 'Select No Coordinates on map' })).toBeNull()
})

it('synchronizes Island Ford cards, markers, previews and Explore filters end to end', async () => {
  prepare()
  HTMLElement.prototype.scrollIntoView = vi.fn()
  window.history.replaceState({}, '', '/explore?preview=1')
  const user = userEvent.setup()
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <MemoryRouter initialEntries={['/explore']}><App /></MemoryRouter>
  </QueryClientProvider>)
  await waitFor(() => expect(fake.handlers.load).toBeTypeOf('function'))
  act(() => fake.handlers.load())
  const marker = () => screen.getByRole('button', { name: 'Select Island Ford on map' })
  await screen.findByRole('button', { name: 'Select Island Ford on map' })
  expect(screen.getByRole('button', { name: 'Explore Amicalola Falls' })).toBeVisible()
  expect(screen.queryByRole('button', { name: 'Select Amicalola Falls on map' })).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Explore Island Ford' }))
  expect(marker()).toHaveAttribute('aria-pressed', 'true')
  expect(fake.easeTo).toHaveBeenCalledWith(expect.objectContaining({ center: [-84.333933, 33.994622] }))
  await user.click(screen.getByRole('button', { name: 'Clear selected destination' }))
  await user.click(marker())
  expect(screen.getByRole('button', { name: 'Explore Island Ford' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByText('Official published entrance reference · routing untested')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Gorge' }))
  await waitFor(() => expect(screen.queryByRole('button', { name: 'Select Island Ford on map' })).toBeNull())
  await user.click(screen.getByRole('button', { name: 'All places' }))
  await screen.findByRole('button', { name: 'Select Island Ford on map' })
  await user.click(screen.getByRole('button', { name: 'Next →' }))
  await waitFor(() => expect(screen.queryByRole('button', { name: 'Select Island Ford on map' })).toBeNull())
  await user.click(screen.getByRole('button', { name: '← Previous' }))
  await screen.findByRole('button', { name: 'Select Island Ford on map' })
  await user.type(screen.getByRole('searchbox'), 'Island Ford')
  await user.click(screen.getByRole('button', { name: 'Search' }))
  expect(await screen.findByText('1 preview place')).toBeVisible()
  expect(marker()).toBeVisible()
  await user.clear(screen.getByRole('searchbox'))
  await user.type(screen.getByRole('searchbox'), 'Falls')
  await user.click(screen.getByRole('button', { name: 'Search' }))
  await waitFor(() => expect(screen.queryByRole('button', { name: 'Select Island Ford on map' })).toBeNull())
})


